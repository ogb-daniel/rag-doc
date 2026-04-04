import logging
import os

from anthropic import AsyncAnthropic

from src.services.llm.base import BaseLLMProvider, ChatMessage, ChatResponse

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    def __init__(self) -> None:
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        self.default_model = "claude-3-haiku-20240307"

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def generate_response(
        self, messages: list[ChatMessage], model: str | None = None, temperature: float = 0.7
    ) -> ChatResponse:
        target_model = model or self.default_model

        system_prompt = ""
        anthropic_msgs = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                anthropic_msgs.append(msg)
        logger.info(f"Sending request to Anthropic ({target_model})")
        response = await self.client.messages.create(
            model=target_model, system=system_prompt, messages=anthropic_msgs, max_tokens=1024, temperature=temperature
        )
        content = response.content[0].text if response.content else ""

        return ChatResponse(
            content=content,
            model_used=target_model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
