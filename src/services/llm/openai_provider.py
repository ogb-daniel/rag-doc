import logging
import time

from openai import AsyncOpenAI
from opentelemetry import trace

from src.core.config import settings
from src.core.metrics import (
    llm_failures_total,
    llm_request_duration,
    llm_requests_total,
    llm_tokens_used,
)
from src.services.llm.base import BaseLLMProvider, ChatMessage, ChatResponse

logger = logging.getLogger(__name__)

tracer = trace.get_tracer(__name__)


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

        with tracer.start_as_current_span("openai.chat.completion") as span:
            span.set_attribute("llm.provider", "openai")
            span.set_attribute("llm.model", target_model)
            span.set_attribute("llm.temperature", temperature)

            start_time = time.perf_counter()

            try:
                response = await self.client.chat.completions.create(
                    model=target_model, messages=messages, temperature=temperature
                )
                duration = time.perf_counter() - start_time
                llm_requests_total.add(1, {"provider": "openai", "model": target_model})
                llm_request_duration.record(duration, {"provider": "openai"})
                if response.usage:
                    llm_tokens_used.add(response.usage.prompt_tokens, {"provider": "openai", "type": "input"})
                    llm_tokens_used.add(response.usage.completion_tokens, {"provider": "openai", "type": "output"})

                    span.set_attribute("llm.tokens.input", response.usage.prompt_tokens)
                    span.set_attribute("llm.tokens.output", response.usage.completion_tokens)

                return ChatResponse(
                    content=response.choices[0].message.content or "",
                    model_used=target_model,
                    input_tokens=response.usage.prompt_tokens if response.usage else 0,
                    output_tokens=response.usage.completion_tokens if response.usage else 0,
                )
            except Exception as e:
                llm_failures_total.add(1, {"provider": "openai"})
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                raise
