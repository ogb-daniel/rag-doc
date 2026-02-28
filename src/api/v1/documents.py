import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.core.config import settings
from src.core.database import get_db
from src.models.document import Document
from src.models.user import User
from src.schemas.document import DocumentResponse
from src.services.ingestion_service import process_document

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

    await process_document(document.id, db)
    await db.refresh(document)
    return document
