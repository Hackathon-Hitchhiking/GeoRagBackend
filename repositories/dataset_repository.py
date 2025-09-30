from typing import Optional

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.dataset import Dataset
from repositories.mixins.crud import CRUDRepositoryMixin


class DatasetRepository(CRUDRepositoryMixin):
    def __init__(self, db: AsyncSession):
        super().__init__(Dataset, db)

    def _build_list_query(
        self, limit: int, offset: int, name: Optional[str], region: Optional[str]
    ) -> Select:
        query = select(Dataset).offset(offset).limit(limit)
        if name:
            query = query.where(Dataset.name.ilike(f"%{name}%"))
        if region:
            query = query.where(Dataset.region.ilike(f"%{region}%"))
        return query.order_by(Dataset.created_at.desc())

    async def list(  # type: ignore[override]
        self, limit: int, offset: int, **filters
    ) -> list[Dataset]:
        name = filters.get("name")
        region = filters.get("region")
        query = self._build_list_query(limit, offset, name, region)
        result = await self._db.execute(query)
        return list(result.scalars().all())
