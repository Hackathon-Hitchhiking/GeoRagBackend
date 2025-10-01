from collections.abc import AsyncIterator

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from configs.Database import get_db_connection
from configs.Environment import get_environment_variables
from errors.errors import ErrNotAuthorized
from models.user import User
from services.auth import AuthService
from services.dataset import DatasetService
from services.document import DocumentService
from services.ml_proxy import MLProxyService


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


def get_ml_proxy_service() -> MLProxyService:
    env = get_environment_variables()
    return MLProxyService(env.ML_SERVICE_BASE_URL)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    if not token:
        raise ErrNotAuthorized("Not authenticated")
    return await auth_service.validate_token(token)
