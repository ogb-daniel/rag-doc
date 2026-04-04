import logging

from src.services.llm.anthropic_provider import AnthropicProvider
from src.services.llm.base import ChatMessage, ChatResponse
from src.services.llm.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class LLMRouter:
    def __init__(self) -> None:
        self.primary = OpenAIProvider()
        self.fallback = AnthropicProvider()

    async def execute_with_fallback(self, messages: list[ChatMessage], temperature: float = 0.7) -> ChatResponse:
        try:
            return await self.primary.generate_response(messages, temperature=temperature)
        except Exception as e:
            logger.error(f"Primary LLM ({self.primary.provider_name}) failed: {str(e)}")
            logger.info(f"Flipping to fallback LLM ({self.fallback.provider_name})...")

            try:
                return await self.fallback.generate_response(messages, temperature=temperature)
            except Exception as fallback_e:
                logger.critical("ALL LLM PROVIDERS FAILED!")
                raise RuntimeError("Service temporarily unavailable") from fallback_e


llm_router = LLMRouter()
