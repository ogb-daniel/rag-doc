import logging

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])


class ServiceHealth(BaseModel):
    status: str  # "healthy" or "unhealthy"
    message: str = ""


class HealthResponse(BaseModel):
    status: str  # "healthy" or "degraded" or "unhealthy"
    postgres: ServiceHealth
    redis: ServiceHealth
    qdrant: ServiceHealth


@router.get("/health", response_model=HealthResponse)
async def deep_health_check() -> HealthResponse:
    results: dict[str, ServiceHealth] = {}
    try:
        from sqlalchemy import text

        from src.core.database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        results["postgres"] = ServiceHealth(status="healthy")
    except Exception as e:
        logger.error(f"Postgres health check failed: {e}")
        results["postgres"] = ServiceHealth(status="unhealthy", message=str(e))

    try:
        import redis.asyncio as aioredis

        from src.core.config import settings

        r = aioredis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0")
        await r.ping()
        await r.close()
        results["redis"] = ServiceHealth(status="healthy")
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        results["redis"] = ServiceHealth(status="unhealthy", message=str(e))

    try:
        from src.services.qdrant_service import qdrant_service

        qdrant_service.client.get_collections()
        results["qdrant"] = ServiceHealth(status="healthy")
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        results["qdrant"] = ServiceHealth(status="unhealthy", message=str(e))

    all_healthy = all(s.status == "healthy" for s in results.values())
    any_unhealthy = any(s.status == "unhealthy" for s in results.values())

    if all_healthy:
        overall = "healthy"
    elif any_unhealthy:
        overall = "degraded"  # Some services down but app is partially functional
    else:
        overall = "unhealthy"

    return HealthResponse(status=overall, **results)
