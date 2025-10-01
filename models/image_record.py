from __future__ import annotations

from typing import Any

from sqlalchemy import Float, Integer, LargeBinary, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.BaseModel import EntityMeta, TimestampMixin


class ImageRecord(TimestampMixin, EntityMeta):
    """A georeferenced image record mirrored from the ML service dataset."""

    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    feature_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    global_descriptor_key: Mapped[str] = mapped_column(
        String(512), unique=True, nullable=False
    )
    preview_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    image_hash: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    descriptor_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    descriptor_dim: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    keypoint_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    global_descriptor_dim: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    global_descriptor: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False, default=b""
    )
    local_feature_type: Mapped[str] = mapped_column(String(64), nullable=False)
    global_descriptor_type: Mapped[str] = mapped_column(String(64), nullable=False)
    matcher_type: Mapped[str] = mapped_column(String(64), nullable=False)

    def __repr__(self) -> str:
        return (
            "ImageRecord(id={id}, image_key={image_key}, lat={lat}, lon={lon})".format(
                id=self.id,
                image_key=self.image_key,
                lat=self.latitude,
                lon=self.longitude,
            )
        )

    def set_metadata(self, value: dict[str, Any] | None) -> None:
        """Helper for updating the JSON metadata payload."""
        self.metadata_json = value
