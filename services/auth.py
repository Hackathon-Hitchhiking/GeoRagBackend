import uuid
from datetime import timedelta

from jose import JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from configs.Environment import get_environment_variables
from errors.errors import ErrEntityConflict, ErrNotAuthorized
from models.user import User
from repositories.user_repository import UserRepository
from schemas.auth import LoginRequest, Token, TokenPayload, UserCreate
from utils.utils import create_access_token, decode_access_token, get_password_hash, verify_password


class AuthService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._repo = UserRepository(db)
        self._env = get_environment_variables()

    async def register_user(self, payload: UserCreate) -> User:
        existing = await self._repo.get_by_email(payload.email)
        if existing is not None:
            raise ErrEntityConflict("User with this email already exists")
        hashed_password = get_password_hash(payload.password)
        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hashed_password,
        )
        return await self._repo.create(user)

    async def authenticate_user(self, email: str, password: str) -> User:
        user = await self._repo.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise ErrNotAuthorized("Incorrect email or password")
        if not user.is_active:
            raise ErrNotAuthorized("User is inactive")
        return user

    async def login(self, payload: LoginRequest) -> Token:
        user = await self.authenticate_user(payload.email, payload.password)
        token = self._create_access_token(user.id)
        return Token(access_token=token)

    def _create_access_token(self, user_id: uuid.UUID) -> str:
        expires_delta = timedelta(minutes=self._env.ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(
            subject=str(user_id),
            expires_delta=expires_delta,
            secret_key=self._env.JWT_SECRET_KEY,
            algorithm=self._env.JWT_ALGORITHM,
        )

    async def validate_token(self, token: str) -> User:
        try:
            payload = decode_access_token(
                token,
                secret_key=self._env.JWT_SECRET_KEY,
                algorithms=[self._env.JWT_ALGORITHM],
            )
            token_data = TokenPayload(**payload)
        except (JWTError, ValidationError, ValueError) as exc:  # pragma: no cover - defensive
            raise ErrNotAuthorized("Could not validate credentials") from exc

        user = await self._repo.get(token_data.sub)
        if user is None or not user.is_active:
            raise ErrNotAuthorized("Could not validate credentials")
        return user
