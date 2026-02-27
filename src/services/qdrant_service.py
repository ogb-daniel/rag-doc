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
