import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models.dataset import Dataset
from models.geofeature import GeoFeature
from repositories.dataset_repository import DatasetRepository
from repositories.geofeature_repository import GeoFeatureRepository
from schemas.dataset import DatasetCreate, DatasetUpdate
from schemas.geofeature import GeoFeatureCreate, GeoFeatureUpdate


class DatasetService:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._dataset_repo = DatasetRepository(db)
        self._feature_repo = GeoFeatureRepository(db)

    async def list_datasets(
        self, limit: int, offset: int, *, name: Optional[str] = None, region: Optional[str] = None
    ) -> list[Dataset]:
        return await self._dataset_repo.list(limit, offset, name=name, region=region)

    async def get_dataset(self, dataset_id: uuid.UUID) -> Dataset:
        return await self._dataset_repo.get(dataset_id)

    async def create_dataset(self, payload: DatasetCreate) -> Dataset:
        dataset = Dataset(**payload.model_dump())
        dataset.id = uuid.uuid4()
        return await self._dataset_repo.create(dataset)

    async def update_dataset(self, dataset_id: uuid.UUID, payload: DatasetUpdate) -> Dataset:
        dataset = await self._dataset_repo.get(dataset_id)
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(dataset, key, value)
        return await self._dataset_repo.update(dataset)

    async def delete_dataset(self, dataset_id: uuid.UUID) -> None:
        await self._dataset_repo.delete(dataset_id)

    async def list_features(
        self,
        dataset_id: uuid.UUID,
        limit: int,
        offset: int,
        *,
        category: Optional[str] = None,
    ) -> list[GeoFeature]:
        await self._dataset_repo.get(dataset_id)
        return await self._feature_repo.list_by_dataset(
            dataset_id, limit, offset, category=category
        )

    async def create_feature(self, payload: GeoFeatureCreate) -> GeoFeature:
        await self._dataset_repo.get(payload.dataset_id)
        feature = GeoFeature(**payload.model_dump())
        feature.id = uuid.uuid4()
        return await self._feature_repo.create(feature)

    async def update_feature(
        self, feature_id: uuid.UUID, payload: GeoFeatureUpdate
    ) -> GeoFeature:
        feature = await self._feature_repo.get(feature_id)
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(feature, key, value)
        return await self._feature_repo.update(feature)

    async def delete_feature(self, feature_id: uuid.UUID) -> None:
        await self._feature_repo.delete(feature_id)
