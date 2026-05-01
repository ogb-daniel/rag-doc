import logging
import uuid

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.document import Document, DocumentStatus
from src.services.embedding_service import embedding_service
from src.services.qdrant_service import qdrant_service

logger = logging.getLogger(__name__)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""],
)


async def process_document(document_id: uuid.UUID, db: AsyncSession) -> None:
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if not document:
        logger.error(f"Document {document_id} not found")
        return
    try:
        document.status = DocumentStatus.PROCESSING
        await db.commit()
        file_path = str(document.file_path)
        if document.content_type == "application/pdf" or file_path.lower().endswith(".pdf"):
            loader = PyPDFLoader(document.file_path)
        else:
            loader = TextLoader(document.file_path)

        raw_docs = loader.load()
        full_text = "\n".join([doc.page_content for doc in raw_docs])

        chunks = text_splitter.split_text(full_text)
        logger.info(f"Document {document_id}: {len(chunks)} chunks created")

        if not chunks:
            document.status = DocumentStatus.FAILED
            document.error_message = "No text content extracted"
            await db.commit()
            return

        vectors = await embedding_service.embed_texts(chunks)
        qdrant_service.upsert_vectors(
            vectors=vectors,
            texts=chunks,
            document_id=document.id,
            metadatas=[{"chunk_index": i, "filename": document.filename} for i in range(len(chunks))],
            user_id=document.user_id,
        )

        document.status = DocumentStatus.INDEXED
        document.chunk_count = len(chunks)
        await db.commit()
        logger.info(f"Document {document_id} indexed successfully")

    except Exception as e:
        logger.exception(f"Failed to process document {document_id}")
        document.status = DocumentStatus.FAILED
        document.error_message = str(e)
        await db.commit()
        raise
