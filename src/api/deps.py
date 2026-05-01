from typing import Any

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.api_key import APIKeyHeader
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.models.api_key import APIKey
from src.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception from e

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


async def get_api_key_user(
    api_key_header_val: str = Security(api_key_header), db: AsyncSession = Depends(get_db)
) -> Any:
    if not api_key_header_val:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    result = await db.execute(select(APIKey).where(APIKey.is_active))
    all_keys = result.scalars().all()
    from src.api.v1.api_keys import pwd_context

    matching_key = None
    for key_record in all_keys:
        if pwd_context.verify(api_key_header_val, key_record.key_hash):
            matching_key = key_record
            break
    if not matching_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    result = await db.execute(select(User).where(User.id == matching_key.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_auth_user(request: Request, db: AsyncSession = Depends(get_db)) -> Any:
    api_key_val = request.headers.get("X-API-Key")
    if api_key_val:
        return await get_api_key_user(api_key_val, db)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    return await get_current_user(token, db)

    raise HTTPException(status_code=401, detail="Not authenticated. Provide a Bearer token or X-API-Key.")
