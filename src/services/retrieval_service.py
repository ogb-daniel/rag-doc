import logging
import time
import uuid

from opentelemetry import trace

from src.core.metrics import retrieval_duration
from src.services.embedding_service import embedding_service
from src.services.qdrant_service import qdrant_service

tracer = trace.get_tracer(__name__)

logger = logging.getLogger(__name__)


class RetrievalService:
    async def retrieve_context(self, query: str, user_id: uuid.UUID, top_k: int = 5) -> str:
        logger.info(f"Retrieving context for query: '{query}'")
        with tracer.start_as_current_span("rag.retrieve_context") as span:
            span.set_attribute("rag.query", query[:100])
            span.set_attribute("rag.top_k", top_k)

        try:
            with tracer.start_as_current_span("embedding.embed_query"):
                query_vector = await embedding_service.embed_query(query)
            start = time.perf_counter()
            with tracer.start_as_current_span("qdrant.vector_search") as qdrant_span:
                results = qdrant_service.search(query_vector=query_vector, top_k=top_k, user_id=user_id)
                qdrant_span.set_attribute("qdrant.results_count", len(results))

            retrieval_duration.record(time.perf_counter() - start, {})

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
