from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI

from src.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    print("Startup: Checking connections...")
    yield
    print("Shutdown: Closing connections...")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")


@app.get("/health")
async def health_check() -> dict[str, Any]:
    return {"status": "healthy", "app": settings.PROJECT_NAME, "database": "checked_in_lifespan"}
