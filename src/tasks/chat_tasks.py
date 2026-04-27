import asyncio
import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.celery_app import celery_app
from src.core.config import settings
from src.models.chat import Conversation, Message
from src.services.llm.base import ChatMessage
from src.services.llm.router import llm_router

logger = logging.getLogger(__name__)


async def _run_async_summary(conversation_id: str) -> None:
    conv_uuid = uuid.UUID(conversation_id)

    local_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    LocalSession = async_sessionmaker(bind=local_engine, expire_on_commit=False)

    async with LocalSession() as db:
        result = await db.execute(select(Conversation).where(Conversation.id == conv_uuid))
        conversation = result.scalar_one_or_none()

        if not conversation:
            await local_engine.dispose()
            return

        msg_result = await db.execute(
            select(Message).where(Message.conversation_id == conv_uuid).order_by(Message.created_at.desc()).limit(10)
        )
        db_msgs = list(msg_result.scalars())[::-1]

        transcript = ""
        for msg in db_msgs:
            transcript += f"{msg.role.upper()}: {msg.content}\n"

        system_prompt = (
            "You are a summarization assistant. Your job is to update the summary of a conversation. "
            "Keep it concise, focusing strictly on facts, user preferences, and the core topic."
        )

        user_prompt = "Here are the latest messages in the conversation:\n" + transcript

        if conversation.summary:
            user_prompt += f"\n\nHere is the previous summary: {conversation.summary}\n"
            user_prompt += "Please incorporate the new messages into the previous summary."
        else:
            user_prompt += "\nPlease provide a brief summary of this conversation."

        messages_for_llm = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ]

        try:
            logger.info(f"Generating summary for conversation {conversation_id}")
            response = await llm_router.execute_with_fallback(messages_for_llm, temperature=0.3)

            conversation.summary = response.content
            await db.commit()
            logger.info("Summary updated successfully.")

        except Exception as e:
            logger.error(f"Failed to summarize: {e}")
            await db.rollback()

    await local_engine.dispose()


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def summarize_conversation_task(self: Any, conversation_id: str) -> Any:
    try:
        asyncio.run(_run_async_summary(conversation_id))
        logger.info(f"Task completed for conversation {conversation_id}")
        return {"status": "success", "conversation_id": conversation_id}
    except Exception as exc:
        logger.exception(f"Summarization failed for conversation {conversation_id}")
        raise self.retry(exc=exc) from exc
