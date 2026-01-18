"""
Redis caching service for SmartCanopy Agent
Handles caching of API responses, tool results, and session data
"""

import redis.asyncio as redis
import json
import hashlib
from typing import Any, Optional, Dict
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service"""

    def __init__(self, redis_url: str):
        """
        Initialize cache service

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        if self.client is None:
            self.client = await redis.from_url(
                self.redis_url,
                encoding='utf-8',
                decode_responses=True
            )
            logger.info("Connected to Redis")

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.client:
            await self.connect()

        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            await self.connect()

        try:
            serialized = json.dumps(value, default=str)
            if ttl:
                await self.client.setex(key, ttl, serialized)
            else:
                await self.client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        if not self.client:
            await self.connect()

        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        if not self.client:
            await self.connect()

        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern

        Args:
            pattern: Key pattern (e.g., "session:*")

        Returns:
            Number of keys deleted
        """
        if not self.client:
            await self.connect()

        try:
            keys = []
            async for key in self.client.scan_iter(pattern):
                keys.append(key)

            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0

    @staticmethod
    def generate_key(prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from arguments

        Args:
            prefix: Key prefix (e.g., "tool:species_recommender")
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        # Create hash of arguments
        data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        data_str = json.dumps(data, sort_keys=True, default=str)
        hash_value = hashlib.md5(data_str.encode()).hexdigest()[:16]

        return f"{prefix}:{hash_value}"

    async def get_or_set(
        self,
        key: str,
        fetch_func: callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get from cache or fetch and cache if not found

        Args:
            key: Cache key
            fetch_func: Async function to fetch value if not cached
            ttl: Time to live in seconds

        Returns:
            Cached or fetched value
        """
        # Try to get from cache
        cached = await self.get(key)
        if cached is not None:
            logger.debug(f"Cache HIT: {key}")
            return cached

        # Fetch value
        logger.debug(f"Cache MISS: {key}")
        value = await fetch_func()

        # Cache the value
        if value is not None:
            await self.set(key, value, ttl)

        return value

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a counter

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value
        """
        if not self.client:
            await self.connect()

        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return 0

    async def decrement(self, key: str, amount: int = 1) -> int:
        """
        Decrement a counter

        Args:
            key: Cache key
            amount: Amount to decrement by

        Returns:
            New value
        """
        if not self.client:
            await self.connect()

        try:
            return await self.client.decrby(key, amount)
        except Exception as e:
            logger.error(f"Cache decrement error for key {key}: {e}")
            return 0

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration on existing key

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        if not self.client:
            await self.connect()

        try:
            return await self.client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False


# ============================================================================
# Specialized Cache Helpers
# ============================================================================

class SessionCache:
    """Helper for session-specific caching"""

    def __init__(self, cache: CacheService, session_id: str):
        self.cache = cache
        self.session_id = session_id

    def _key(self, suffix: str) -> str:
        """Generate session-specific key"""
        return f"session:{self.session_id}:{suffix}"

    async def get_data(self) -> Optional[Dict]:
        """Get session data"""
        return await self.cache.get(self._key("data"))

    async def set_data(self, data: Dict, ttl: int = 86400) -> bool:
        """Set session data (default 24 hour TTL)"""
        return await self.cache.set(self._key("data"), data, ttl)

    async def get_site_context(self) -> Optional[Dict]:
        """Get current site context"""
        return await self.cache.get(self._key("site_context"))

    async def set_site_context(self, context: Dict, ttl: int = 3600) -> bool:
        """Set site context (default 1 hour TTL)"""
        return await self.cache.set(self._key("site_context"), context, ttl)

    async def clear(self) -> int:
        """Clear all session data"""
        return await self.cache.clear_pattern(f"session:{self.session_id}:*")


class ToolCache:
    """Helper for tool result caching"""

    def __init__(self, cache: CacheService):
        self.cache = cache

    async def get_result(
        self,
        tool_name: str,
        params: Dict
    ) -> Optional[Dict]:
        """
        Get cached tool result

        Args:
            tool_name: Name of the tool
            params: Tool input parameters

        Returns:
            Cached result or None
        """
        key = CacheService.generate_key(f"tool:{tool_name}", **params)
        return await self.cache.get(key)

    async def set_result(
        self,
        tool_name: str,
        params: Dict,
        result: Dict,
        ttl: int
    ) -> bool:
        """
        Cache tool result

        Args:
            tool_name: Name of the tool
            params: Tool input parameters
            result: Tool output
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        key = CacheService.generate_key(f"tool:{tool_name}", **params)
        return await self.cache.set(key, result, ttl)


class APICache:
    """Helper for external API response caching"""

    def __init__(self, cache: CacheService):
        self.cache = cache

    async def get_response(
        self,
        api_name: str,
        endpoint: str,
        params: Dict
    ) -> Optional[Any]:
        """Get cached API response"""
        key = CacheService.generate_key(f"api:{api_name}:{endpoint}", **params)
        return await self.cache.get(key)

    async def set_response(
        self,
        api_name: str,
        endpoint: str,
        params: Dict,
        response: Any,
        ttl: int
    ) -> bool:
        """Cache API response"""
        key = CacheService.generate_key(f"api:{api_name}:{endpoint}", **params)
        return await self.cache.set(key, response, ttl)


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache() -> CacheService:
    """
    Get cache service singleton

    Returns:
        CacheService instance
    """
    global _cache_service
    if _cache_service is None:
        from agent.config import settings
        _cache_service = CacheService(settings.redis_url)
    return _cache_service
