from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DatasetBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    region: str | None = Field(default=None, max_length=120)

    model_config = ConfigDict(str_strip_whitespace=True)


class DatasetCreate(DatasetBase):
    pass


class DatasetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    region: str | None = Field(default=None, max_length=120)


class DatasetRead(DatasetBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
