import logging
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.core.database import Memory, EventStore
from backend.app.services.memory.service import MemoryService
from backend.app.services.identity.pipeline import IdentityExtractor

logger = logging.getLogger(__name__)

class IdentityService:
    """
    Identity Evolution Engine and profile compiler. Bridges the extraction pipeline, 
    relational database persistence, reinforcement scoring, and vector synchronization.
    """
    
    @staticmethod
    def reinforce_or_store_identity_item(
        db: Session,
        key: str,
        value: str,
        category: str,
        score_increment: float = 0.5
    ) -> Memory:
        """
        Stores an identity item or increments its salience score if it already exists (reinforcement scoring).
        """
        logger.info(f"Integrating identity item. Key: {key}, Category: {category}")
        
        existing = db.query(Memory).filter(Memory.entity_key == key).first()
        if existing:
            # Identity Evolution: Increment the salience/confidence score
            old_score = existing.salience_score or 1.0
            new_score = min(float(old_score) + score_increment, 5.0)  # Caps at 5.0 salience
            existing.entity_value = value  # Update value to reflect recent phrasing
            existing.salience_score = new_score
            existing.updated_at = datetime.utcnow()
            db_memory = existing
            logger.info(f"Reinforced existing identity element: {key}. Score: {old_score} -> {new_score}")
        else:
            # Create new identity elements starting at 1.0 score
            db_memory = Memory(
                entity_key=key,
                entity_value=value,
                category=category,
                salience_score=1.0
            )
            db.add(db_memory)
            logger.info(f"Created new identity element: {key}")
            
        db.commit()
        db.refresh(db_memory)
        
        # Synchronize with vector memory fabric
        from backend.app.services.memory.memory import get_text_embedding, memory_store
        vector = get_text_embedding(f"{key}: {value}")
        memory_store.add_semantic_memory(
            text=f"{key}: {value}",
            category=category,
            vector=vector,
            metadata={
                "memory_id": str(db_memory.id),
                "entity_key": key,
                "salience_score": float(db_memory.salience_score)
            }
        )
        
        # Log system event in Event Store for traceability
        event = EventStore(
            event_type="identity_updated" if existing else "identity_created",
            payload={
                "memory_id": str(db_memory.id),
                "key": key,
                "category": category,
                "salience_score": float(db_memory.salience_score)
            }
        )
        db.add(event)
        db.commit()
        
        return db_memory

    @staticmethod
    def extract_and_integrate_from_text(db: Session, text: str) -> list[dict]:
        """
        Run the extraction pipeline over the text and reinforce/save results in database and vector store.
        """
        extracted_elements = IdentityExtractor.extract_from_text(text)
        results = []
        for element in extracted_elements:
            db_item = IdentityService.reinforce_or_store_identity_item(
                db=db,
                key=element["key"],
                value=element["value"],
                category=element["category"],
                score_increment=0.5
            )
            results.append({
                "id": str(db_item.id),
                "key": db_item.entity_key,
                "value": db_item.entity_value,
                "category": db_item.category,
                "salience_score": float(db_item.salience_score)
            })
        return results

    @staticmethod
    def get_identity_profile(db: Session) -> dict:
        """
        Compile the full, structured user identity profile categorized by models.
        """
        categories = ["value", "preference", "motivation", "learning_style", "future_self"]
        profile = {cat: {} for cat in categories}
        
        # Query all identity-related records
        memories = db.query(Memory).filter(Memory.category.in_(categories)).all()
        for mem in memories:
            profile[mem.category][mem.entity_key] = {
                "id": str(mem.id),
                "value": mem.entity_value,
                "salience_score": float(mem.salience_score),
                "updated_at": mem.updated_at.isoformat()
            }
            
        return profile

    @staticmethod
    def search_identity_memories(db: Session, query: str, limit: int = 5) -> list[dict]:
        """
        Retrieve identity memories semantically.
        """
        # Simply proxy to MemoryService, but filter by category at the application layer if needed.
        raw_results = MemoryService.search_memories(db=db, query=query, limit=limit)
        # Filter raw results to only include identity categories
        identity_categories = {"value", "preference", "motivation", "learning_style", "future_self"}
        filtered = []
        for r in raw_results:
            meta = r.get("metadata", {})
            if meta.get("category") in identity_categories:
                filtered.append(r)
        return filtered
