from functools import lru_cache

from typing import Optional

from pydantic_settings import BaseSettings


class EnvironmentSettings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    DEBUG: bool
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_S3_BUCKET: str
    AWS_S3_ENDPOINT_URL: Optional[str] = None
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = "configs/.env"
        env_file_encoding = "utf-8"


@lru_cache
def get_environment_variables() -> EnvironmentSettings:
    return EnvironmentSettings()
