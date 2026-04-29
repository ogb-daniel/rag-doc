import secrets
import string

from fastapi import APIRouter, Depends
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.core.database import get_db
from src.models.api_key import APIKey
from src.models.user import User

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class APIKeyCreateRequest(BaseModel):
    name: str


class APIKeyResponse(BaseModel):
    id: str
    name: str
    raw_key: str | None = None


def generate_secure_api_key() -> str:
    alphabet = string.ascii_letters + string.digits
    key = "".join(secrets.choice(alphabet) for _ in range(32))
    return f"sk_{key}"


@router.post("/", response_model=APIKeyResponse)
async def create_api_key(
    request: APIKeyCreateRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> APIKeyResponse:
    raw_key = generate_secure_api_key()

    hashed_key = pwd_context.hash(raw_key[:72])

    new_key = APIKey(user_id=current_user.id, name=request.name, key_hash=hashed_key)

    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    return APIKeyResponse(id=str(new_key.id), name=new_key.name, raw_key=raw_key)


@router.get("/", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[APIKeyResponse]:
    result = await db.execute(select(APIKey).where(APIKey.user_id == current_user.id, APIKey.is_active))
    keys = result.scalars().all()
    return [APIKeyResponse(id=str(k.id), name=k.name) for k in keys]
