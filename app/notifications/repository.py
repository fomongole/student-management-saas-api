import uuid
from sqlalchemy import select, and_, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.notifications.models import Notification, NotificationType, NotificationStatus

async def create_notification_record(
    db: AsyncSession, 
    recipient_id: uuid.UUID, 
    title: str, 
    message: str, 
    type: NotificationType,
    school_id: uuid.UUID
) -> Notification:
    """Logs the notification in the database with a PENDING status."""
    db_obj = Notification(
        recipient_id=recipient_id,
        title=title,
        message=message,
        type=type,
        school_id=school_id
    )
    db.add(db_obj)
    await db.flush() 
    return db_obj

async def update_notification_status(
    db: AsyncSession, 
    notification_id: uuid.UUID, 
    status: NotificationStatus
):
    """Optimized single-query status update."""
    stmt = (
        update(Notification)
        .where(Notification.id == notification_id)
        .values(status=status)
    )
    await db.execute(stmt)
    await db.commit()

async def get_user_notifications(db: AsyncSession, user_id: uuid.UUID, school_id: uuid.UUID) -> list[Notification]:
    """Fetches the latest alerts for the currently logged-in user."""
    query = (
        select(Notification)
        .where(and_(Notification.recipient_id == user_id, Notification.school_id == school_id))
        .order_by(desc(Notification.created_at))
        .limit(50)
    )
    result = await db.execute(query)
    return result.scalars().all()

async def mark_notification_as_read(
    db: AsyncSession, 
    notification_id: uuid.UUID, 
    user_id: uuid.UUID
) -> None:
    """Marks a single notification as read, ensuring it belongs to the user."""
    stmt = (
        update(Notification)
        .where(
            and_(
                Notification.id == notification_id,
                Notification.recipient_id == user_id
            )
        )
        .values(is_read=True)
    )
    await db.execute(stmt)
    await db.commit()

async def mark_all_as_read(
    db: AsyncSession, 
    user_id: uuid.UUID, 
    school_id: uuid.UUID
) -> None:
    """Bulk updates all unread notifications for a user."""
    stmt = (
        update(Notification)
        .where(
            and_(
                Notification.recipient_id == user_id,
                Notification.school_id == school_id,
                Notification.is_read == False
            )
        )
        .values(is_read=True)
    )
    await db.execute(stmt)
    await db.commit()