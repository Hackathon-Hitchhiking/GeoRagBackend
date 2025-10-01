from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class ImageRecordBase(BaseModel):
    image_key: str = Field(..., max_length=512)
    feature_key: str = Field(..., max_length=512)
    global_descriptor_key: str = Field(..., max_length=512)
    preview_key: str | None = Field(default=None, max_length=512)
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = Field(default=None, max_length=512)
    metadata: dict[str, Any] | None = Field(
        default=None,
        alias="metadata",
        validation_alias=AliasChoices("metadata_json", "metadata"),
    )
    image_hash: str = Field(..., max_length=128)
    descriptor_count: int = 0
    descriptor_dim: int = 0
    keypoint_count: int = 0
    global_descriptor_dim: int = 0
    global_descriptor: bytes = b""
    local_feature_type: str = Field(..., max_length=64)
    global_descriptor_type: str = Field(..., max_length=64)
    matcher_type: str = Field(..., max_length=64)

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        ser_json_bytes="base64",
    )


class ImageRecordCreate(ImageRecordBase):
    pass


class ImageRecordUpdate(BaseModel):
    preview_key: str | None = Field(default=None, max_length=512)
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = Field(default=None, max_length=512)
    metadata: dict[str, Any] | None = Field(
        default=None,
        alias="metadata",
        validation_alias=AliasChoices("metadata_json", "metadata"),
    )
    descriptor_count: int | None = None
    descriptor_dim: int | None = None
    keypoint_count: int | None = None
    global_descriptor_dim: int | None = None
    global_descriptor: bytes | None = None
    local_feature_type: str | None = Field(default=None, max_length=64)
    global_descriptor_type: str | None = Field(default=None, max_length=64)
    matcher_type: str | None = Field(default=None, max_length=64)

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        ser_json_bytes="base64",
    )


class ImageRecordRead(ImageRecordBase):
    id: int
    created_at: datetime
    updated_at: datetime
    signed_image_url: str | None = None
    signed_preview_url: str | None = None

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        ser_json_bytes="base64",
    )
