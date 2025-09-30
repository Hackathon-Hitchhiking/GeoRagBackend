from functools import lru_cache

import anyio
import boto3
from botocore.exceptions import ClientError
from loguru import logger

from configs.Environment import get_environment_variables
from errors.errors import ErrBadRequest, ErrEntityNotFound


class S3StorageService:
    def __init__(self) -> None:
        self._env = get_environment_variables()
        self._client = boto3.client(
            "s3",
            region_name=self._env.AWS_REGION,
            aws_access_key_id=self._env.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self._env.AWS_SECRET_ACCESS_KEY,
            endpoint_url=self._env.AWS_S3_ENDPOINT_URL,
        )

    async def upload_text(
        self, key: str, content: str, *, content_type: str = "text/plain"
    ) -> None:
        logger.debug("Uploading object to S3: {}", key)
        await anyio.to_thread.run_sync(
            self._client.put_object,
            Bucket=self._env.AWS_S3_BUCKET,
            Key=key,
            Body=content.encode("utf-8"),
            ContentType=content_type,
        )

    async def ensure_object_exists(self, key: str) -> None:
        try:
            await anyio.to_thread.run_sync(
                self._client.head_object,
                Bucket=self._env.AWS_S3_BUCKET,
                Key=key,
            )
        except ClientError as exc:  # pragma: no cover - network interaction
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in {"404", "NotFound"}:
                raise ErrEntityNotFound("Object does not exist in storage") from exc
            raise ErrBadRequest("Unable to verify object in storage") from exc

    def generate_presigned_url(self, key: str, expires_in: int = 900) -> str:
        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._env.AWS_S3_BUCKET, "Key": key},
                ExpiresIn=expires_in,
            )
        except ClientError as exc:  # pragma: no cover - network interaction
            raise ErrBadRequest("Unable to generate presigned URL") from exc


@lru_cache
def get_storage_service() -> S3StorageService:
    return S3StorageService()
