from __future__ import annotations

from typing import Any, Sequence, Type

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from errors.errors import ErrEntityNotFound


class CRUDRepositoryMixin:
    def __init__(self, model: Type[Any], db: AsyncSession):
        self.model = model
        self._db = db

    async def list(self, limit: int, offset: int, **filters) -> Sequence[Any]:
        logger.debug(f"{self.model.__name__} - Repository - list")
        query = select(self.model).offset(offset).limit(limit)

        for key, value in filters.items():
            if value is None:
                continue
            column = getattr(self.model, key, None)
            if column is None:
                continue
            query = query.where(column == value)

        result = await self._db.execute(query.order_by(self.model.id))
        return result.scalars().all()

    async def get(self, entity_id: Any) -> Any:
        logger.debug(f"{self.model.__name__} - Repository - get")
        instance = await self._db.get(self.model, entity_id)
        if instance is None:
            raise ErrEntityNotFound(f"{self.model.__name__} not found")
        return instance

    async def create(self, instance: Any) -> Any:
        logger.debug(f"{self.model.__name__} - Repository - create")
        self._db.add(instance)
        await self._db.commit()
        await self._db.refresh(instance)
        return instance

    async def update(self, instance: Any) -> Any:
        logger.debug(f"{self.model.__name__} - Repository - update")
        self._db.add(instance)
        await self._db.commit()
        await self._db.refresh(instance)
        return instance

    async def delete(self, entity_id: Any) -> None:
        logger.debug(f"{self.model.__name__} - Repository - delete")
        instance = await self.get(entity_id)
        await self._db.delete(instance)
        await self._db.commit()
        await self._db.flush()
