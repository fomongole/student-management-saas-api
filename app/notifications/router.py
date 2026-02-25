from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.notifications import schemas, service

router = APIRouter()

@router.get("/my-alerts", response_model=list[schemas.NotificationResponse])
async def get_my_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch the notification inbox for the logged-in user."""
    return await service.fetch_my_notifications(db, current_user)