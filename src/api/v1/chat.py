from fastapi import APIRouter, Depends

from src.api.deps import get_current_user
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
) -> ChatEndpointResponse:
    system_prompt = "You are a helpful internal knowledge assistant."
    context_injected = False

    if request.use_rag:
        context = await retrieval_service.retrieve_context(query=request.query)
        if context:
            system_prompt += (
                f"\n\nHere is some context to help answer the user's question. "
                f"Use this context if it is relevant. If the context does not contain "
                f"the answer, rely on your general knowledge gracefully.\n\n"
                f"<context>\n{context}\n</context>"
            )
            context_injected = True

    messages = [ChatMessage(role="system", content=system_prompt), ChatMessage(role="user", content=request.query)]

    response = await llm_router.execute_with_fallback(messages)

    return ChatEndpointResponse(
        answer=response.content,
        model_used=response.model_used,
        context_injected=context_injected,
    )
