from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

from src.api.v1.api import api_router
from src.core.config import settings
from src.core.logging import setup_logging
from src.services.qdrant_service import qdrant_service

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    qdrant_service.ensure_collection()

    print("Startup: Qdrant collection ready")
    redis_conn = redis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0", encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis_conn)
    print("Startup: Redis limiter connection ready")

    yield
    print("Shutdown: Closing connections...")
    await redis_conn.close()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")

app.include_router(api_router)


@app.get("/health")
async def health_check() -> dict[str, Any]:
    return {"status": "healthy", "app": settings.PROJECT_NAME, "database": "checked_in_lifespan"}
