import redis.asyncio as aioredis
from app.core.config import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def blacklist_token(jti: str, ttl_seconds: int = 3600):
    r = await get_redis()
    await r.setex(f"blacklist:{jti}", ttl_seconds, "1")


async def is_token_blacklisted(jti: str) -> bool:
    r = await get_redis()
    return await r.exists(f"blacklist:{jti}") == 1


async def cache_set(key: str, value: str, ttl: int = 300):
    r = await get_redis()
    await r.setex(key, ttl, value)


async def cache_get(key: str) -> str | None:
    r = await get_redis()
    return await r.get(key)


async def cache_delete(key: str):
    r = await get_redis()
    await r.delete(key)
