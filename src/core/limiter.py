from typing import Any

import redis.asyncio as redis
from fastapi import Request, Response
from fastapi_limiter.depends import RateLimiter
from pyrate_limiter import Duration, Limiter, Rate, RedisBucket

from src.core.config import settings

limiter: Limiter | None = None


async def init_limiter() -> None:
    global limiter
    redis_conn = redis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0", encoding="utf-8", decode_responses=True
    )
    rates = [Rate(5, Duration.SECOND * 60)]

    redis_bucket = await RedisBucket.init(rates, redis_conn, "api-rate-limit")
    limiter = Limiter(redis_bucket)
    print("Limiter initialized")


async def rate_limit_dependency(request: Request, response: Response) -> Any:
    if limiter is None:
        return
    handler = RateLimiter(limiter=limiter)
    return await handler(request, response)
