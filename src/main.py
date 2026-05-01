from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI

from src.api.v1.api import api_router
from src.core.config import settings
from src.core.limiter import init_limiter
from src.core.logging import setup_logging
from src.services.qdrant_service import qdrant_service

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    qdrant_service.ensure_collection()
    print("Startup: Qdrant collection ready")
    await init_limiter()
    yield
    print("Shutdown: Closing connections...")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")

app.include_router(api_router)


@app.get("/health")
async def health_check() -> dict[str, Any]:
    return {"status": "healthy", "app": settings.PROJECT_NAME, "database": "checked_in_lifespan"}
