"""
Simple caching system for API responses.

Provides thread-safe caching with TTL (Time To Live) support.
"""

import time
import threading


class SimpleCache:
    """
    Thread-safe cache with TTL support.

    Usage:
        cache = SimpleCache(default_ttl=300)  # 5 minutes
        cache.set('key', 'value')
        value = cache.get('key')
        cache.clear()
    """

    def __init__(self, default_ttl=300):
        """
        Initialize cache.

        Args:
            default_ttl (int): Default time-to-live in seconds (default: 300)
        """
        self.cache = {}
        self.default_ttl = default_ttl
        self.lock = threading.Lock()

    def get(self, key):
        """
        Get value from cache.

        Args:
            key (str): Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self.lock:
            if key in self.cache:
                data, timestamp = self.cache[key]
                if time.time() - timestamp < self.default_ttl:
                    return data
                else:
                    # Remove expired entry
                    del self.cache[key]
            return None

    def set(self, key, value, ttl=None):
        """
        Set value in cache.

        Args:
            key (str): Cache key
            value: Value to cache
            ttl (int, optional): Time-to-live in seconds (uses default if None)
        """
        with self.lock:
            self.cache[key] = (value, time.time())

    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()

    def size(self):
        """
        Get number of cached items.

        Returns:
            int: Number of items in cache
        """
        with self.lock:
            return len(self.cache)

    def keys(self):
        """
        Get all cache keys.

        Returns:
            list: List of cache keys
        """
        with self.lock:
            return list(self.cache.keys())
