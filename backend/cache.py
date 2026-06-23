import time

class SimpleCache:
    def __init__(self, ttl: int = 300):
        self._store = {}
        self._ttl = ttl

    def get(self, key: str):
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expiry = entry
        if time.time() > expiry:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value):
        self._store[key] = (value, time.time() + self._ttl)

    def clear(self, key: str = None):
        if key:
            self._store.pop(key, None)
        else:
            self._store.clear()

    def invalidate_by_species(self, species_ids: list):
        ids_set = set(str(sid) for sid in species_ids)
        keys_to_remove = [k for k in self._store if any(f"_{sid}_" in f"_{k}_" or k.endswith(f"_{sid}") for sid in ids_set)]
        for k in keys_to_remove:
            self._store.pop(k, None)

trends_cache = SimpleCache(ttl=300)
species_cache = SimpleCache(ttl=300)
