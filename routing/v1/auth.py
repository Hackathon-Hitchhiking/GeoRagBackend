from fastapi import APIRouter, Depends, status

from dependencies import get_auth_service, get_current_user
from models.user import User
from schemas import LoginRequest, Token, UserCreate, UserRead
from services.auth import AuthService


router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    user = await auth_service.register_user(payload)
    return UserRead.model_validate(user)


@router.post("/login", response_model=Token)
async def login_user(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    return await auth_service.login(payload)


@router.get("/me", response_model=UserRead)
async def get_current_profile(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
