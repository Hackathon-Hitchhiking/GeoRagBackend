from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    *,
    expires_delta: timedelta,
    secret_key: str,
    algorithm: str,
) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode: Dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def decode_access_token(
    token: str,
    *,
    secret_key: str,
    algorithms: List[str],
) -> Dict[str, Any]:
    return jwt.decode(token, secret_key, algorithms=algorithms)
