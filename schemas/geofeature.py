from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GeoFeatureBase(BaseModel):
    dataset_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    latitude: float
    longitude: float
    category: str | None = Field(default=None, max_length=120)
    media_s3_key: str | None = Field(default=None, max_length=512)

    model_config = ConfigDict(str_strip_whitespace=True)


class GeoFeatureCreate(GeoFeatureBase):
    pass


class GeoFeatureUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    category: str | None = Field(default=None, max_length=120)
    media_s3_key: str | None = Field(default=None, max_length=512)


class GeoFeatureRead(GeoFeatureBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
