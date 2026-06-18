import logging
import re
from sqlalchemy.orm import Session
from backend.app.core.database import Message, EventStore
from backend.app.services.pcc.service import PCCService

logger = logging.getLogger(__name__)

class MemoryConsolidationService:
    """
    Consolidates raw conversational history (episodic messages) into structured, long-term 
    knowledge nodes and edges within the Personal Knowledge Graph (PKG).
    """
    
    @staticmethod
    def consolidate_episodic_logs(db: Session) -> dict:
        """
        Scan unconsolidated chat history, extract skills, projects, and goals, and link them in the PKG.
        """
        logger.info("Running episodic memory consolidation loop...")
        
        # 1. Fetch recent messages
        messages = db.query(Message).filter(Message.sender == "user").all()
        if not messages:
            return {"status": "skipped", "reason": "No episodic logs to consolidate."}
            
        nodes_added = 0
        edges_added = 0
        
        # Establish default User node to anchor everything
        PCCService.upsert_node(db, "user_me", "user", "Owner Profile")
        
        for msg in messages:
            content = msg.content
            
            # Simple heuristic entity extraction
            # Projects extraction (e.g. "working on JARVIS-gpt")
            project_match = re.search(r"working on\s+([a-zA-Z0-9_-]+)", content, re.IGNORECASE)
            if project_match:
                proj_name = project_match.group(1).strip().lower()
                PCCService.upsert_node(
                    db=db,
                    node_id=f"project_{proj_name}",
                    node_type="project",
                    label=f"Project {proj_name.upper()}",
                    properties={"source": "consolidation"}
                )
                PCCService.upsert_edge(
                    db=db,
                    source_node_id="user_me",
                    relationship_type="WORKS_ON",
                    target_node_id=f"project_{proj_name}"
                )
                nodes_added += 1
                edges_added += 1

            # Skills extraction (e.g. "writing python code" or "rust backend")
            skills = ["python", "rust", "typescript", "javascript", "docker", "c++"]
            for skill in skills:
                if re.search(rf"\b{skill}\b", content, re.IGNORECASE):
                    PCCService.upsert_node(
                        db=db,
                        node_id=f"skill_{skill}",
                        node_type="skill",
                        label=f"Skill: {skill.capitalize()}",
                        properties={"level": "learning"}
                    )
                    PCCService.upsert_edge(
                        db=db,
                        source_node_id="user_me",
                        relationship_type="HAS_SKILL",
                        target_node_id=f"skill_{skill}"
                    )
                    nodes_added += 1
                    edges_added += 1
                    
                    # If project was also found, link skill to project
                    if project_match:
                        proj_name = project_match.group(1).strip().lower()
                        PCCService.upsert_edge(
                            db=db,
                            source_node_id=f"project_{proj_name}",
                            relationship_type="REQUIRES",
                            target_node_id=f"skill_{skill}"
                        )
                        edges_added += 1

        # Log event
        if nodes_added > 0 or edges_added > 0:
            event = EventStore(
                event_type="memory_consolidated",
                payload={
                    "messages_processed": len(messages),
                    "nodes_added": nodes_added,
                    "edges_added": edges_added
                }
            )
            db.add(event)
            db.commit()
            
        return {
            "status": "success",
            "messages_processed": len(messages),
            "nodes_added": nodes_added,
            "edges_added": edges_added
        }
