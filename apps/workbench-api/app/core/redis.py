"""
Redis Configuration
===================
Redis client for caching and job queues.
"""

from typing import Optional

import redis.asyncio as redis
import structlog

from app.core.config import settings

logger = structlog.get_logger()

# Global Redis client
redis_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    """Initialize Redis connection."""
    global redis_client

    logger.info("Initializing Redis connection")

    try:
        redis_client = redis.from_url(
            str(settings.REDIS_URL),
            encoding="utf-8",
            decode_responses=True,
        )

        # Test connection
        await redis_client.ping()

        logger.info("Redis connection established")
    except Exception as e:
        logger.error("Failed to connect to Redis", error=str(e))
        raise


async def close_redis() -> None:
    """Close Redis connection."""
    global redis_client

    if redis_client:
        logger.info("Closing Redis connection")
        await redis_client.close()
        redis_client = None


async def get_redis() -> redis.Redis:
    """Get Redis client."""
    if not redis_client:
        raise RuntimeError("Redis not initialized")
    return redis_client


async def check_redis_connection() -> bool:
    """Check if Redis is accessible."""
    try:
        if redis_client:
            await redis_client.ping()
            return True
        return False
    except Exception:
        return False
