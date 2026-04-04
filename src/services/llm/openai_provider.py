import logging

from openai import AsyncOpenAI

from src.core.config import settings
from src.services.llm.base import BaseLLMProvider, ChatMessage, ChatResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.default_model = "gpt-4o-mini"

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate_response(
        self, messages: list[ChatMessage], model: str | None = None, temperature: float = 0.7
    ) -> ChatResponse:
        target_model = model or self.default_model

        # formatted_msgs = [{"role": msg.role, "content": msg.content} for msg in messages]
        logger.info(f"Sending request to OpenAI ({target_model})")
        response = await self.client.chat.completions.create(
            model=target_model, messages=messages, temperature=temperature
        )

        return ChatResponse(
            content=response.choices[0].message.content or "",
            model_used=target_model,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
        )
