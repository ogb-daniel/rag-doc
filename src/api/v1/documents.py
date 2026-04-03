import os
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.core.config import settings
from src.core.database import get_db
from src.models.document import Document
from src.models.user import User
from src.schemas.document import DocumentListResponse, DocumentResponse
from src.tasks.document_tasks import process_document_task

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_TYPES = {"text/plain", "text/markdown", "application/pdf"}


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Document:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_id = uuid.uuid4()
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}_{file.filename}")
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    document = Document(
        filename=file.filename or "unknown",
        content_type=file.content_type or "text/plain",
        file_path=file_path,
        user_id=current_user.id,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    process_document_task.delay(str(document.id))
    await db.refresh(document)
    return document


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    result = await db.execute(select(Document).where(Document.user_id == current_user.id))
    documents = result.scalars().all()

    count_result = await db.execute(
        select(func.count()).select_from(Document).where(Document.user_id == current_user.id)
    )
    total = count_result.scalar() or 0
    return {"documents": list(documents), "total": total}


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Document:
    result = await db.execute(select(Document).where(Document.id == document_id, Document.user_id == current_user.id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
