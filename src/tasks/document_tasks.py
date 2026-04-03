import asyncio
import logging
import uuid
from typing import Any

from src.core.celery_app import celery_app
from src.core.database import AsyncSessionLocal
from src.services.ingestion_service import process_document

logger = logging.getLogger(__name__)


async def _run_async_ingestion(document_id: str) -> None:
    doc_uuid = uuid.UUID(document_id)
    async with AsyncSessionLocal() as db:
        await process_document(doc_uuid, db)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_document_task(self: Any, document_id: str) -> Any:
    try:
        asyncio.run(_run_async_ingestion(document_id))
        logger.info(f"Task payload completed for document {document_id}")
        return {"status": "processed", "document_id": document_id}
    except Exception as exc:
        logger.exception(f"Background verification failed for document {document_id}")
        raise self.retry(exc=exc) from exc
