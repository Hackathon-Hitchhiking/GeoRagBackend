import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.document import Document
from repositories.mixins.crud import CRUDRepositoryMixin


class DocumentRepository(CRUDRepositoryMixin):
    def __init__(self, db: AsyncSession):
        super().__init__(Document, db)

    async def list_by_dataset(
        self, dataset_id: uuid.UUID, limit: int, offset: int
    ) -> List[Document]:
        query = (
            select(Document)
            .where(Document.dataset_id == dataset_id)
            .offset(offset)
            .limit(limit)
            .order_by(Document.created_at.desc())
        )
        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def get_by_s3_key(self, s3_key: str) -> Optional[Document]:
        query = select(Document).where(Document.s3_key == s3_key)
        result = await self._db.execute(query)
        return result.scalars().first()
