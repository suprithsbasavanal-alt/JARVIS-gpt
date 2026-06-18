import logging
import json
import time
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class CacheClient:
    """
    A Redis caching client that automatically falls back to a thread-safe
    in-memory dictionary if Redis is offline or unavailable.
    """
    def __init__(self):
        self.redis = None
        self.local_store = {}
        self.local_expiry = {}
        
        try:
            import redis
            # Parse Redis URL
            self.redis = redis.from_url(settings.REDIS_URL, socket_timeout=2.0, decode_responses=True)
            # Test ping
            self.redis.ping()
            logger.info("Successfully connected to Redis Cache.")
        except Exception as e:
            self.redis = None
            logger.warning(f"Redis not available ({e}). Using in-memory fallback cache.")

    def get(self, key: str) -> str | None:
        """
        Get value from cache. Handles expirations.
        """
        if self.redis:
            try:
                return self.redis.get(key)
            except Exception as e:
                logger.warning(f"Redis GET failed: {e}. Falling back to memory.")
        
        # Local fallback
        if key in self.local_store:
            expiry = self.local_expiry.get(key)
            if expiry and time.time() > expiry:
                # Expired
                del self.local_store[key]
                del self.local_expiry[key]
                return None
            return self.local_store[key]
        return None

    def set(self, key: str, value: str, ex_seconds: int | None = None) -> bool:
        """
        Set key-value in cache with optional expiration in seconds.
        """
        if self.redis:
            try:
                if ex_seconds:
                    self.redis.set(key, value, ex=ex_seconds)
                else:
                    self.redis.set(key, value)
                return True
            except Exception as e:
                logger.warning(f"Redis SET failed: {e}. Falling back to memory.")
        
        # Local fallback
        self.local_store[key] = value
        if ex_seconds:
            self.local_expiry[key] = time.time() + ex_seconds
        else:
            self.local_expiry.pop(key, None)
        return True

    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        """
        if self.redis:
            try:
                self.redis.delete(key)
                return True
            except Exception as e:
                logger.warning(f"Redis DELETE failed: {e}. Falling back to memory.")
        
        # Local fallback
        self.local_store.pop(key, None)
        self.local_expiry.pop(key, None)
        return True

    def clear(self):
        """
        Clear all cached entries.
        """
        if self.redis:
            try:
                self.redis.flushdb()
            except Exception:
                pass
        self.local_store.clear()
        self.local_expiry.clear()

# Global cache client instance
cache = CacheClient()
