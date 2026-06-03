import time
from typing import Any, Dict, Tuple

class SimpleCache:
    def __init__(self, ttl_seconds: int = 60):
        self.ttl = ttl_seconds
        self._cache: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Any:
        if key in self._cache:
            timestamp, value = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any):
        self._cache[key] = (time.time(), value)

    def invalidate(self, key: str):
        if key in self._cache:
            del self._cache[key]
            
    def clear(self):
        self._cache.clear()

# 全局单例缓存，默认 TTL 5 分钟
species_cache = SimpleCache(ttl_seconds=300)
trends_cache = SimpleCache(ttl_seconds=300)