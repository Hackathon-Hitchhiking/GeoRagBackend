from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DocumentBase(BaseModel):
    dataset_id: UUID
    title: str = Field(min_length=1, max_length=255)
    summary: str | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class DocumentCreate(DocumentBase):
    s3_key: str | None = Field(default=None, max_length=512)
    inline_content: str | None = None
    content_type: str | None = Field(default="text/plain", max_length=120)

    @model_validator(mode="after")
    def validate_payload(self):  # type: ignore[override]
        if not self.s3_key and not self.inline_content:
            raise ValueError("Either s3_key or inline_content must be provided")
        return self


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    summary: str | None = None
    metadata: dict[str, Any] | None = None


class DocumentRead(DocumentBase):
    id: UUID
    owner_id: UUID | None = None
    s3_key: str
    signed_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
