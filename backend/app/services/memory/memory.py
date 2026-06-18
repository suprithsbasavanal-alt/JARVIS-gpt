import logging
import uuid
import math
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class MemoryStore:
    def __init__(self):
        self.client = None
        self.semantic_collection = "jarvis_semantic_memory"
        self.code_collection = "jarvis_code_knowledge"
        self.vector_size = 1536  # Default size (Gemini/OpenAI)
        
        try:
            self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
            # Try to check connection or list collections
            self.client.get_collections()
            logger.info("Connected to Qdrant successfully.")
            self._init_collections()
        except Exception as e:
            logger.warning(f"Qdrant not available: {e}. Falling back to mock in-memory store.")
            self.client = None
            self._local_semantic_vectors = []
            self._local_code_vectors = []

    def _init_collections(self):
        if self.client:
            for collection_name in [self.semantic_collection, self.code_collection]:
                try:
                    collections = [c.name for c in self.client.get_collections().collections]
                    if collection_name not in collections:
                        self.client.create_collection(
                            collection_name=collection_name,
                            vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
                        )
                        logger.info(f"Created collection: {collection_name}")
                except Exception as e:
                    logger.error(f"Failed to initialize Qdrant collection {collection_name}: {e}")

    # General backward compatible add_memory mapping to semantic memory
    def add_memory(self, text: str, vector: list[float], metadata: dict):
        return self.add_semantic_memory(text, metadata.get("category", "general"), vector, metadata)

    # General backward compatible search_memories mapping to semantic memory
    def search_memories(self, query_vector: list[float], limit: int = 5) -> list[dict]:
        return self.search_semantic_memory(query_vector, limit=limit)

    def add_semantic_memory(self, text: str, category: str, vector: list[float], metadata: dict | None = None):
        payload = {"text": text, "category": category, "timestamp": int(datetime.utcnow().timestamp())}
        if metadata:
            payload.update(metadata)
            
        if self.client:
            try:
                self.client.upsert(
                    collection_name=self.semantic_collection,
                    points=[
                        {
                            "id": str(uuid.uuid4()),
                            "vector": vector,
                            "payload": payload
                        }
                    ]
                )
                return True
            except Exception as e:
                logger.error(f"Error writing to Qdrant semantic memory: {e}")
        
        # Fallback
        self._local_semantic_vectors.append({
            "text": text,
            "vector": vector,
            "payload": payload
        })
        return True

    def search_semantic_memory(self, query_vector: list[float], category: str | None = None, limit: int = 5) -> list[dict]:
        if self.client:
            try:
                # Optional filtering by category
                filter_query = None
                if category:
                    from qdrant_client.http import models as qd_models
                    filter_query = qd_models.Filter(
                        must=[
                            qd_models.FieldCondition(
                                key="category",
                                match=qd_models.MatchValue(value=category)
                            )
                        ]
                    )
                results = self.client.search(
                    collection_name=self.semantic_collection,
                    query_vector=query_vector,
                    query_filter=filter_query,
                    limit=limit
                )
                return [{"text": r.payload.get("text"), "metadata": r.payload, "score": r.score} for r in results]
            except Exception as e:
                logger.error(f"Error searching Qdrant semantic memory: {e}")
        
        # Fallback search
        scored = []
        for memory in self._local_semantic_vectors:
            if category and memory["payload"].get("category") != category:
                continue
            sim = self._cosine_similarity(query_vector, memory["vector"])
            scored.append((sim, memory))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"text": item["text"], "metadata": item["payload"], "score": score} for score, item in scored[:limit]]

    def add_code_knowledge(self, file_path: str, content_chunk: str, project_id: str, vector: list[float]):
        payload = {
            "file_path": file_path,
            "content_chunk": content_chunk,
            "project_id": project_id,
            "timestamp": int(datetime.utcnow().timestamp())
        }
        if self.client:
            try:
                self.client.upsert(
                    collection_name=self.code_collection,
                    points=[
                        {
                            "id": str(uuid.uuid4()),
                            "vector": vector,
                            "payload": payload
                        }
                    ]
                )
                return True
            except Exception as e:
                logger.error(f"Error writing to Qdrant code knowledge: {e}")
        
        # Fallback
        self._local_code_vectors.append({
            "vector": vector,
            "payload": payload
        })
        return True

    def search_code_knowledge(self, query_vector: list[float], project_id: str | None = None, limit: int = 5) -> list[dict]:
        if self.client:
            try:
                filter_query = None
                if project_id:
                    from qdrant_client.http import models as qd_models
                    filter_query = qd_models.Filter(
                        must=[
                            qd_models.FieldCondition(
                                key="project_id",
                                match=qd_models.MatchValue(value=project_id)
                            )
                        ]
                    )
                results = self.client.search(
                    collection_name=self.code_collection,
                    query_vector=query_vector,
                    query_filter=filter_query,
                    limit=limit
                )
                return [{"file_path": r.payload.get("file_path"), "content_chunk": r.payload.get("content_chunk"), "metadata": r.payload, "score": r.score} for r in results]
            except Exception as e:
                logger.error(f"Error searching Qdrant code knowledge: {e}")
        
        # Fallback search
        scored = []
        for code in self._local_code_vectors:
            if project_id and code["payload"].get("project_id") != project_id:
                continue
            sim = self._cosine_similarity(query_vector, code["vector"])
            scored.append((sim, code))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"file_path": item["payload"]["file_path"], "content_chunk": item["payload"]["content_chunk"], "metadata": item["payload"], "score": score} for score, item in scored[:limit]]

    def _cosine_similarity(self, v1, v2):
        dot_product = sum(x*y for x, y in zip(v1, v2))
        norm1 = math.sqrt(sum(x*x for x in v1))
        norm2 = math.sqrt(sum(x*x for x in v2))
        return dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0

memory_store = MemoryStore()
