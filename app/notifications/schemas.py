import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.notifications.models import NotificationType, NotificationStatus

class NotificationResponse(BaseModel):
    id: uuid.UUID
    title: str
    message: str
    type: NotificationType
    status: NotificationStatus
    is_read: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)