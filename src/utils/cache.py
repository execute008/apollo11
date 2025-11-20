"""Intelligent caching layer to reduce API calls and save costs."""

import logging
import hashlib
import json
from typing import Optional, Any, Callable
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps
import requests_cache

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for API requests to reduce costs and improve performance."""

    def __init__(
        self,
        cache_dir: str = ".cache",
        default_expire: int = 3600,  # 1 hour default
        backend: str = "sqlite"
    ):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory for cache storage
            default_expire: Default expiration in seconds
            backend: Cache backend ('sqlite' or 'memory')
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_expire = default_expire

        # Initialize requests-cache for HTTP caching
        cache_file = str(self.cache_dir / "http_cache")

        requests_cache.install_cache(
            cache_name=cache_file,
            backend=backend,
            expire_after=default_expire,
            allowable_codes=(200, 201),
            allowable_methods=('GET', 'POST'),
        )

        logger.info(f"Cache initialized: {cache_file} (expire: {default_expire}s)")

    def get_cache_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        key_data = {
            "args": args,
            "kwargs": {k: v for k, v in kwargs.items() if k != 'api_key'}  # Don't cache API keys
        }

        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            # Check expiration
            if 'expires_at' in data:
                expires_at = datetime.fromisoformat(data['expires_at'])
                if datetime.now() > expires_at:
                    cache_file.unlink()  # Delete expired cache
                    return None

            return data.get('value')

        except Exception as e:
            logger.debug(f"Cache read error: {e}")
            return None

    def set(self, key: str, value: Any, expire_after: Optional[int] = None):
        """Set value in cache with optional expiration."""
        expire_after = expire_after or self.default_expire

        cache_file = self.cache_dir / f"{key}.json"

        try:
            data = {
                'value': value,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(seconds=expire_after)).isoformat()
            }

            with open(cache_file, 'w') as f:
                json.dump(data, f)

        except Exception as e:
            logger.debug(f"Cache write error: {e}")

    def clear(self):
        """Clear all cached data."""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()

            requests_cache.clear()
            logger.info("Cache cleared")

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def get_stats(self) -> dict:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.json"))

        stats = {
            "cache_dir": str(self.cache_dir),
            "total_entries": len(cache_files),
            "size_bytes": sum(f.stat().st_size for f in cache_files),
        }

        # Get requests-cache stats
        try:
            session = requests_cache.get_cache()
            if hasattr(session, 'responses'):
                stats["http_cached_responses"] = len(session.responses)
        except:
            pass

        return stats


# Global cache instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get singleton cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached_request(expire_after: Optional[int] = None):
    """
    Decorator to cache function results.

    Usage:
        @cached_request(expire_after=3600)
        def expensive_api_call(param1, param2):
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()

            # Generate cache key
            cache_key = f"{func.__name__}_{cache.get_cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {func.__name__}")
                return cached_value

            # Call function and cache result
            logger.debug(f"Cache miss: {func.__name__}")
            result = func(*args, **kwargs)

            cache.set(cache_key, result, expire_after=expire_after)

            return result

        return wrapper
    return decorator
