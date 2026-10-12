from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_auth_user
from src.core.database import get_db
from src.models.api_key import APIKey
from src.models.chat import Conversation
from src.models.document import Document
from src.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_auth_user)
) -> dict[str, Any]:
    doc_count_result = await db.execute(
        select(func.count()).select_from(Document).where(Document.user_id == current_user.id)
    )
    total_documents = doc_count_result.scalar() or 0

    conv_count_result = await db.execute(
        select(func.count()).select_from(Conversation).where(Conversation.user_id == current_user.id)
    )
    total_conversations = conv_count_result.scalar() or 0

    key_count_result = await db.execute(
        select(func.count()).select_from(APIKey).where(APIKey.user_id == current_user.id)
    )
    active_api_keys = key_count_result.scalar() or 0

    tokens_used_month = 0

    return {
        "total_documents": total_documents,
        "total_conversations": total_conversations,
        "active_api_keys": active_api_keys,
        "tokens_used_month": tokens_used_month,
    }
