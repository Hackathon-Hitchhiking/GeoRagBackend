from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from configs.Database import get_db_connection
from configs.Environment import get_environment_variables
from errors.errors import ErrNotAuthorized
from models.user import User
from services.auth import AuthService
from services.image_record import ImageRecordService
from services.ml_client import MLServiceClient


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in get_db_connection():
        yield session


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


async def get_image_record_service(
    db: AsyncSession = Depends(get_db),
) -> ImageRecordService:
    return ImageRecordService(db)


def get_ml_service_client() -> MLServiceClient:
    env = get_environment_variables()
    return MLServiceClient(env.ML_SERVICE_BASE_URL)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    if not token:
        raise ErrNotAuthorized("Not authenticated")
    return await auth_service.validate_token(token)
