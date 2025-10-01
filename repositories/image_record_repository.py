from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.image_record import ImageRecord
from repositories.mixins.crud import CRUDRepositoryMixin


class ImageRecordRepository(CRUDRepositoryMixin):
    def __init__(self, db: AsyncSession):
        super().__init__(ImageRecord, db)

    async def list_by_hash(
        self, image_hash: str, limit: int, offset: int
    ) -> Sequence[ImageRecord]:
        query = (
            select(ImageRecord)
            .where(ImageRecord.image_hash == image_hash)
            .offset(offset)
            .limit(limit)
            .order_by(ImageRecord.id)
        )
        result = await self._db.execute(query)
        return result.scalars().all()
