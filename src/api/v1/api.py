from fastapi import APIRouter

from src.api.v1.api_keys import router as api_keys_router
from src.api.v1.auth import router as auth_router
from src.api.v1.chat import router as chat_router
from src.api.v1.conversations import router as conversations_router
from src.api.v1.dashboard import router as dashboard_router
from src.api.v1.documents import router as documents_router
from src.api.v1.health import router as health_router
from src.api.v1.metrics_api import router as metrics_router
from src.api.v1.users import router as users_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(documents_router)
api_router.include_router(chat_router)
api_router.include_router(api_keys_router)
api_router.include_router(health_router)

api_router.include_router(dashboard_router)
api_router.include_router(conversations_router)
api_router.include_router(metrics_router)
