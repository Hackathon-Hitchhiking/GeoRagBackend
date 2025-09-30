import uuid

from sqlalchemy import Column, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.BaseModel import EntityMeta, TimestampMixin


class GeoFeature(EntityMeta, TimestampMixin):
    __tablename__ = "geo_features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(
        UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    category = Column(String(120), nullable=True)
    media_s3_key = Column(String(512), nullable=True)

    dataset = relationship("Dataset", back_populates="features")
