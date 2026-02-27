import logging
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.core.config import settings

logger = logging.getLogger(__name__)


class QdrantService:
    def __init__(self) -> None:
        self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.collection_name = settings.QDRANT_COLLECTION_NAME

    def ensure_collection(self) -> None:
        collections = self.client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=settings.EMBEDDING_DIMENSION, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {self.collection_name}")

    def upsert_vectors(
        self,
        vectors: list[list[float]],
        texts: list[str],
        document_id: uuid.UUID,
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={"text": text, "document_id": str(document_id), **(metadatas[i] if metadatas else {})},
            )
            for i, (vector, text) in enumerate(zip(vectors, texts, strict=False))
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info(f"Upserted {len(points)} vectors for document {document_id}")

    def search(self, query_vector: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        results = self.client.query_points(collection_name=self.collection_name, query=query_vector, limit=top_k)
        return [
            {
                "text": point.payload.get("text", ""),
                "document_id": point.payload.get("document_id"),
                "score": point.score,
            }
            for point in results.points
        ]

    def delete_by_document_id(self, document_id: uuid.UUID) -> None:
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=str(document_id)))]),
        )


qdrant_service = QdrantService()
