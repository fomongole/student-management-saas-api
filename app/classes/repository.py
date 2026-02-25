import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.classes.models import Class
from app.classes.schemas import ClassCreate

async def get_class_by_details(db: AsyncSession, school_id: uuid.UUID, name: str, stream: str | None) -> Class | None:
    """Checks if a class with the same name and stream already exists in THIS specific school."""
    
    # Explicit null check for stream to prevent database constraint failures
    stream_condition = Class.stream.is_(None) if stream is None else Class.stream == stream
    
    query = select(Class).where(
        Class.school_id == school_id,
        Class.name == name,
        stream_condition
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_class(db: AsyncSession, class_in: ClassCreate, school_id: uuid.UUID) -> Class:
    """Saves a new class, strictly attaching it to the admin's school."""
    new_class = Class(
        name=class_in.name,
        stream=class_in.stream,
        level=class_in.level,
        capacity=class_in.capacity,
        school_id=school_id  # Enforce Multi-tenancy!
    )
    db.add(new_class)
    await db.commit()
    await db.refresh(new_class)
    return new_class