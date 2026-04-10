import uuid
from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str
    use_rag: bool = True
    conversation_id: Optional[uuid.UUID] = None


class ChatEndpointResponse(BaseModel):
    answer: str
    model_used: str
    context_injected: bool
    conversation_id: uuid.UUID
