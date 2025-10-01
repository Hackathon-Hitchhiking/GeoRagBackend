from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from models.image_record import ImageRecord
from repositories.image_record_repository import ImageRecordRepository
from schemas.image_record import ImageRecordCreate, ImageRecordRead, ImageRecordUpdate
from services.storage import S3StorageService, get_storage_service


class ImageRecordService:
    def __init__(
        self,
        db: AsyncSession,
        storage_service: Optional[S3StorageService] = None,
    ) -> None:
        self._db = db
        self._repo = ImageRecordRepository(db)
        self._storage = storage_service or get_storage_service()

    async def list_records(
        self,
        limit: int,
        offset: int,
        *,
        image_hash: str | None = None,
        matcher_type: str | None = None,
        local_feature_type: str | None = None,
    ) -> Sequence[ImageRecord]:
        if image_hash:
            return await self._repo.list_by_hash(image_hash, limit, offset)
        return await self._repo.list(
            limit,
            offset,
            matcher_type=matcher_type,
            local_feature_type=local_feature_type,
        )

    async def get_record(self, image_id: int) -> ImageRecord:
        return await self._repo.get(image_id)

    async def create_record(self, payload: ImageRecordCreate) -> ImageRecord:
        data = payload.model_dump(by_alias=False)
        metadata = data.pop("metadata", None)
        record = ImageRecord(**data)
        record.metadata = metadata
        return await self._repo.create(record)

    async def update_record(
        self, image_id: int, payload: ImageRecordUpdate
    ) -> ImageRecord:
        record = await self._repo.get(image_id)
        update_data = payload.model_dump(exclude_unset=True, by_alias=False)
        metadata = update_data.pop("metadata", None)
        for key, value in update_data.items():
            setattr(record, key, value)
        if metadata is not None:
            record.metadata = metadata
        return await self._repo.update(record)

    async def delete_record(self, image_id: int) -> None:
        await self._repo.delete(image_id)

    def to_read_model(
        self,
        record: ImageRecord,
        *,
        include_signed_urls: bool = False,
        expires_in: int = 900,
    ) -> ImageRecordRead:
        extras: dict[str, str | None] = {}
        if include_signed_urls:
            extras["signed_image_url"] = self._storage.generate_presigned_url(
                record.image_key, expires_in
            )
            extras["signed_preview_url"] = (
                self._storage.generate_presigned_url(record.preview_key, expires_in)
                if record.preview_key
                else None
            )
        return ImageRecordRead.model_validate(record, update=extras)
