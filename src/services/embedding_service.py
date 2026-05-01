import hashlib
import json
import logging
from typing import Any

import redis.asyncio as redis
from langchain_openai import OpenAIEmbeddings
from opentelemetry import trace

from src.core.config import settings
from src.core.metrics import embedding_cache_total

tracer = trace.get_tracer(__name__)
logger = logging.getLogger(__name__)

cache_redis = redis.from_url(
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/2", encoding="utf-8", decode_responses=True
)


class EmbeddingService:
    def __init__(self) -> None:
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        self.cache_ttl = 60 * 60 * 24 * 7

    async def embed_texts(self, texts: list[str]) -> Any:
        vectors = await self.embeddings.aembed_documents(texts)
        logger.info(f"Embedded {len(texts)} chunks → {len(vectors)} vectors")
        return vectors

    async def embed_query(self, query: str) -> Any:
        with tracer.start_as_current_span("embedding.lookup") as span:
            cache_key = f"embed:{self._hash_text(query)}"

            cached_result = await cache_redis.get(cache_key)
            if cached_result:
                span.set_attribute("cache.hit", True)

                embedding_cache_total.add(1, {"result": "hit"})
                logger.info("Cache HIT for embedding query")
                return json.loads(cached_result)

            span.set_attribute("cache.hit", False)

            embedding_cache_total.add(1, {"result": "miss"})

            logger.info("Cache MISS: Calling OpenAI for embedding query")

            with tracer.start_as_current_span("openai.embedding"):
                vector = await self.embeddings.aembed_query(query)
            await cache_redis.set(cache_key, json.dumps(vector), ex=self.cache_ttl)
            return vector

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


embedding_service = EmbeddingService()
