import uuid
import asyncio
import logging
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.notifications import repository
from app.notifications.models import NotificationType, NotificationStatus
from app.auth.models import User

logger = logging.getLogger(__name__)

async def send_notification_task(
    notification_id: uuid.UUID,
    recipient_id: uuid.UUID,
    title: str,
    message: str,
    type: NotificationType,
):
    """
    Background worker responsible for dispatching notifications.
    It ONLY opens a DB session at the very end to log the result, saving connection limits.
    """
    try:
        # Integration point (SendGrid / Twilio / etc.)
        await asyncio.sleep(1) 
        
        logger.info(f"[{type.value} SENT to {recipient_id}] {title}")
        final_status = NotificationStatus.SENT

    except Exception as e:
        logger.error(f"Failed to send {type.value} to {recipient_id}: {str(e)}")
        final_status = NotificationStatus.FAILED

    # Open a brief, independent session just to update the status
    async with AsyncSessionLocal() as db:
        await repository.update_notification_status(db, notification_id, final_status)


async def dispatch_alert(
    db: AsyncSession,
    background_tasks: BackgroundTasks,
    recipient_id: uuid.UUID,
    title: str,
    message: str,
    type: NotificationType,
    school_id: uuid.UUID,
):
    """
    Public service entry point for triggering alerts.
    """
    
    # 1. Save the record as PENDING using the main request's DB session.
    # If the HTTP request fails and rolls back, this notification magically disappears.
    notification = await repository.create_notification_record(
        db, recipient_id, title, message, type, school_id
    )

    # 2. Hand off the slow network request to the background worker
    background_tasks.add_task(
        send_notification_task,
        notification.id,
        recipient_id,
        title,
        message,
        type,
    )


async def fetch_my_notifications(
    db: AsyncSession,
    current_user: User,
):
    """
    Retrieves inbox notifications for authenticated user.
    """
    return await repository.get_user_notifications(
        db,
        current_user.id,
        current_user.school_id,
    )