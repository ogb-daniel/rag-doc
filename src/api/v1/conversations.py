from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_auth_user
from src.core.database import get_db
from src.models.chat import Conversation, Message
from src.models.user import User

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("/")
async def list_conversations(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_auth_user)
) -> list[dict[str, Any]]:
    result = await db.execute(
        select(Conversation).where(Conversation.user_id == current_user.id).order_by(desc(Conversation.created_at))
    )
    conversations = result.scalars().all()

    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at,
            "message_count": 0,  # For simplicity here, or query it if needed
        }
        for c in conversations
    ]


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_auth_user)
) -> dict[str, Any]:
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_result = await db.execute(
        select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()

    return {
        "id": conv.id,
        "title": conv.title,
        "messages": [{"role": m.role, "content": m.content, "created_at": m.created_at} for m in messages],
    }


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_auth_user)
) -> None:
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conv)
    await db.commit()
