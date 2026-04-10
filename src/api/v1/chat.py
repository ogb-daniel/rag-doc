from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.core.database import get_db
from src.models.chat import Conversation, Message
from src.models.user import User
from src.schemas.chat import ChatEndpointResponse, ChatRequest
from src.services.llm.base import ChatMessage
from src.services.llm.router import llm_router
from src.services.retrieval_service import retrieval_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatEndpointResponse)
async def chat_interaction(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatEndpointResponse:
    if request.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == request.conversation_id, Conversation.user_id == current_user.id
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Conversation not found")

        msg_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc())
            .limit(10)
        )
        db_messages = list(msg_result.scalars())[::-1]
    else:
        conversation = Conversation(
            user_id=current_user.id,
            title=request.query[:50],  # Auto-title based on first query
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        db_messages = []

    system_prompt = "You are a helpful internal knowledge assistant."
    context_injected = False

    if request.use_rag:
        context = await retrieval_service.retrieve_context(query=request.query)
        if context:
            system_prompt += f"\n\nContext:\n<context>\n{context}\n</context>"
            context_injected = True

    messages_for_llm = [ChatMessage(role="system", content=system_prompt)]

    for db_msg in db_messages:
        messages_for_llm.append(ChatMessage(role=db_msg.role, content=db_msg.content))
    messages_for_llm.append(ChatMessage(role="user", content=request.query))

    new_user_msg = Message(conversation_id=conversation.id, role="user", content=request.query)

    db.add(new_user_msg)

    response = await llm_router.execute_with_fallback(messages_for_llm)

    new_assistant_msg = Message(conversation_id=conversation.id, role="assistant", content=response.content)

    db.add(new_assistant_msg)

    await db.commit()
    return ChatEndpointResponse(
        answer=response.content,
        model_used=response.model_used,
        context_injected=context_injected,
        conversation_id=conversation.id,
    )
