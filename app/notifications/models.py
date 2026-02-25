import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from app.db.base import TenantModel

if TYPE_CHECKING:
    from app.auth.models import User

class NotificationType(str, Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    IN_APP = "IN_APP"

class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"

class Notification(TenantModel):
    """
    Audit ledger for all outbound and in-app communications.
    """
    __tablename__ = "notifications"

    recipient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType), default=NotificationType.IN_APP)
    status: Mapped[NotificationStatus] = mapped_column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)

    recipient: Mapped["User"] = relationship("User")