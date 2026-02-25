from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import declared_attr

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 models."""
    pass

class BaseModel(Base):
    """
    An abstract base model that provides:
    - UUID primary key
    - created_at timestamp
    - updated_at timestamp
    """
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc)
    )

class TenantModel(BaseModel):
    """
    Abstract mixin for all models that belong to a specific school.
    Ensures strict data isolation per tenant.
    """
    __abstract__ = True

    @declared_attr
    def school_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(
            UUID(as_uuid=True), 
            ForeignKey("schools.id", ondelete="CASCADE"), 
            index=True, 
            nullable=False
        )