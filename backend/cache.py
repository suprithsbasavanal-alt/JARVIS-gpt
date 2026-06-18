import redis
import logging
from backend.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.client = None
        try:
            self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.client.ping()
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            logger.warning(f"Redis not available: {e}. Falling back to in-memory cache.")
            self.client = None
            self._local_cache = {}

    def get(self, key: str) -> str | None:
        if self.client:
            try:
                return self.client.get(key)
            except Exception:
                pass
        return self._local_cache.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> bool:
        if self.client:
            try:
                self.client.set(key, value, ex=ex)
                return True
            except Exception:
                pass
        self._local_cache[key] = value
        return True

    def delete(self, key: str) -> bool:
        if self.client:
            try:
                self.client.delete(key)
                return True
            except Exception:
                pass
        if key in self._local_cache:
            del self._local_cache[key]
        return True

cache = RedisClient()
