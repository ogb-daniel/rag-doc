import abc

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatResponse(BaseModel):
    content: str
    model_used: str
    input_tokens: int = 0
    output_tokens: int = 0


class BaseLLMProvider(abc.ABC):
    @abc.abstractmethod
    async def generate_response(
        self, messages: list[ChatMessage], model: str | None = None, temperature: float = 0.7
    ) -> ChatResponse:
        pass

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        pass
