import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.geofeature import GeoFeature
from repositories.mixins.crud import CRUDRepositoryMixin


class GeoFeatureRepository(CRUDRepositoryMixin):
    def __init__(self, db: AsyncSession):
        super().__init__(GeoFeature, db)

    async def list_by_dataset(
        self, dataset_id: uuid.UUID, limit: int, offset: int, *, category: Optional[str] = None
    ) -> List[GeoFeature]:
        query = select(GeoFeature).where(GeoFeature.dataset_id == dataset_id)
        if category:
            query = query.where(GeoFeature.category == category)
        query = query.order_by(GeoFeature.created_at.desc()).offset(offset).limit(limit)
        result = await self._db.execute(query)
        return list(result.scalars().all())
