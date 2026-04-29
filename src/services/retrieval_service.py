import logging
import uuid

from src.services.embedding_service import embedding_service
from src.services.qdrant_service import qdrant_service

logger = logging.getLogger(__name__)


class RetrievalService:
    async def retrieve_context(self, query: str, user_id: uuid.UUID, top_k: int = 5) -> str:
        logger.info(f"Retrieving context for query: '{query}'")
        try:
            query_vector = await embedding_service.embed_query(query)
            results = qdrant_service.search(query_vector=query_vector, top_k=top_k, user_id=user_id)
            if not results:
                logger.info("No relevant context found.")
                return ""
            formatted_context = ""
            for i, res in enumerate(results):
                score = res.get("score", 0)
                text = res.get("text", "")
                # print(text, score)
                # if score > 0.70:
                formatted_context += f"--- Excerpt {i+1} (Relevance: {score:.2f}) ---\n{text}\n\n"
            logger.info(f"Retrieved {len(results)} chunks, fused into context.")
            return formatted_context.strip()
        except Exception:
            logger.exception("Failed during retrieval process")
            return ""


retrieval_service = RetrievalService()
