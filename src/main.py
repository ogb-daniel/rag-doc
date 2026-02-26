from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI

from src.api.v1.api import api_router
from src.core.config import settings
from src.core.logging import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    print("Startup: Checking connections...")
    yield
    print("Shutdown: Closing connections...")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")

app.include_router(api_router)


@app.get("/health")
async def health_check() -> dict[str, Any]:
    return {"status": "healthy", "app": settings.PROJECT_NAME, "database": "checked_in_lifespan"}
