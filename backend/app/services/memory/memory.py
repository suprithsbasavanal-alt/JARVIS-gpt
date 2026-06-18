import logging
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class MemoryStore:
    def __init__(self):
        self.client = None
        self.collection_name = "jarvis_semantic_memory"
        try:
            self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
            # Try to check connection or list collections
            self.client.get_collections()
            logger.info("Connected to Qdrant successfully.")
            self._init_collection()
        except Exception as e:
            logger.warning(f"Qdrant not available: {e}. Falling back to mock in-memory store.")
            self.client = None
            self._local_vectors = []

    def _init_collection(self):
        if self.client:
            try:
                collections = [c.name for c in self.client.get_collections().collections]
                if self.collection_name not in collections:
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                    )
                    logger.info(f"Created collection: {self.collection_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Qdrant collection: {e}")

    def add_memory(self, text: str, vector: list[float], metadata: dict):
        if self.client:
            try:
                import uuid
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[
                        {
                            "id": str(uuid.uuid4()),
                            "vector": vector,
                            "payload": {"text": text, **metadata}
                        }
                    ]
                )
                return True
            except Exception as e:
                logger.error(f"Error writing to Qdrant: {e}")
        
        # Fallback
        self._local_vectors.append({
            "text": text,
            "vector": vector,
            "payload": metadata
        })
        return True

    def search_memories(self, query_vector: list[float], limit: int = 5) -> list[dict]:
        if self.client:
            try:
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=limit
                )
                return [{"text": r.payload.get("text"), "metadata": r.payload} for r in results]
            except Exception as e:
                logger.error(f"Error searching Qdrant: {e}")
        
        # Simple fallback mock calculation (using cosine similarity approximation or random search)
        import math
        def dot_product(v1, v2):
            return sum(x*y for x, y in zip(v1, v2))
        def norm(v):
            return math.sqrt(sum(x*x for x in v))
        
        scored_memories = []
        for memory in self._local_vectors:
            try:
                dp = dot_product(query_vector, memory["vector"])
                n1 = norm(query_vector)
                n2 = norm(memory["vector"])
                similarity = dp / (n1 * n2) if n1 > 0 and n2 > 0 else 0
                scored_memories.append((similarity, memory))
            except Exception:
                scored_memories.append((0, memory))
                
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [{"text": item["text"], "metadata": item["payload"]} for score, item in scored_memories[:limit]]

memory_store = MemoryStore()
