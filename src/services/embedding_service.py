import logging
from typing import Any

from langchain_openai import OpenAIEmbeddings

from src.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self) -> None:
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
        )

    async def embed_texts(self, texts: list[str]) -> Any:
        vectors = await self.embeddings.aembed_documents(texts)
        logger.info(f"Embedded {len(texts)} chunks → {len(vectors)} vectors")
        return vectors

    async def embed_query(self, query: str) -> Any:
        return await self.embeddings.aembed_query(query)


embedding_service = EmbeddingService()
