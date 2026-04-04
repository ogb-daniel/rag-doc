from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str
    use_rag: bool = True


class ChatEndpointResponse(BaseModel):
    answer: str
    model_used: str
    context_injected: bool
