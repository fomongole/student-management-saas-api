import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.notifications import schemas, service
from fastapi import status

router = APIRouter()

@router.get("/my-alerts", response_model=list[schemas.NotificationResponse])
async def get_my_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch the notification inbox for the logged-in user."""
    return await service.fetch_my_notifications(db, current_user)

@router.patch("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_as_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marks a specific notification as read."""
    await service.read_single_notification(db, notification_id, current_user)

@router.patch("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marks all notifications in the user's inbox as read."""
    await service.read_all_user_notifications(db, current_user)