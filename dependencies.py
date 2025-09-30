from collections.abc import AsyncIterator

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from configs.Database import get_db_connection
from errors.errors import ErrNotAuthorized
from models.user import User
from services.auth import AuthService
from services.dataset import DatasetService
from services.document import DocumentService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/core/v1/auth/login")


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in get_db_connection():
        yield session


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


async def get_dataset_service(db: AsyncSession = Depends(get_db)) -> DatasetService:
    return DatasetService(db)


async def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    return DocumentService(db)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    if not token:
        raise ErrNotAuthorized("Not authenticated")
    return await auth_service.validate_token(token)
