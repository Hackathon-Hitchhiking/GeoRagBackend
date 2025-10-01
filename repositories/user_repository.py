from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repositories.mixins.crud import CRUDRepositoryMixin


class UserRepository(CRUDRepositoryMixin):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        result = await self._db.execute(query)
        return result.scalars().first()
