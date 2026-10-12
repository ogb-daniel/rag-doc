from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_auth_user
from src.core.database import get_db
from src.models.user import User

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/summary")
async def get_metrics_summary(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_auth_user)
) -> dict[str, Any]:
    return {"llm_requests": [], "token_usage": [], "latency": [], "cache_ratio": {"hits": 0, "misses": 0}}
