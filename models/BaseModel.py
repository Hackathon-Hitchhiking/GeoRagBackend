from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import declarative_mixin
from sqlalchemy.ext.declarative import declarative_base

EntityMeta = declarative_base()


@declarative_mixin
class TimestampMixin:
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
