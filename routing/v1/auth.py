from fastapi import APIRouter, Depends, HTTPException, Request, status

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
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    content_type = request.headers.get("content-type", "")

    if content_type.startswith("application/x-www-form-urlencoded") or content_type.startswith("multipart/form-data"):
        form_data = await request.form()
        email = form_data.get("email") or form_data.get("username")
        password = form_data.get("password")
        if not email or not password:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Missing credentials")
        payload = LoginRequest(email=email, password=password)
    else:
        try:
            body = await request.json()
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request body") from exc
        payload = LoginRequest.model_validate(body)

    return await auth_service.login(payload)


@router.get("/me", response_model=UserRead)
async def get_current_profile(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
