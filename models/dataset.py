import uuid

from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.BaseModel import EntityMeta, TimestampMixin


class Dataset(EntityMeta, TimestampMixin):
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    region = Column(String(120), nullable=True)

    documents = relationship(
        "Document", back_populates="dataset", cascade="all,delete-orphan"
    )
    features = relationship(
        "GeoFeature", back_populates="dataset", cascade="all,delete-orphan"
    )
