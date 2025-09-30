import uuid

from sqlalchemy import Column, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.BaseModel import EntityMeta, TimestampMixin


class Document(EntityMeta, TimestampMixin):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(
        UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    s3_key = Column(String(512), nullable=False, index=True)
    metadata = Column(JSON, nullable=True)

    dataset = relationship("Dataset", back_populates="documents")
    owner = relationship("User", back_populates="documents")
