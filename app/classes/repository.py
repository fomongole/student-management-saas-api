import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.classes.models import Class
from app.classes.schemas import ClassCreate
from typing import Sequence

from app.teachers.models import Teacher

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
        school_id=school_id,  # Enforce Multi-tenancy!
        form_teacher_id=class_in.form_teacher_id 
    )
    db.add(new_class)
    await db.commit()
    await db.refresh(new_class)
    return new_class

async def get_all_classes_for_school(db: AsyncSession, school_id: uuid.UUID) -> Sequence[Class]:
    """Fetches all classes belonging to a specific school."""
    query = (
        select(Class)
        .where(Class.school_id == school_id)
        .options(joinedload(Class.form_teacher).joinedload(Teacher.user))
        .order_by(Class.level, Class.name, Class.stream)
    )
    result = await db.execute(query)
    return result.scalars().all()

async def get_class_by_id(db: AsyncSession, class_id: uuid.UUID, school_id: uuid.UUID) -> Class | None:
    """Fetches a specific class, ensuring it belongs to the requesting admin's school."""
    query = (
        select(Class)
        .where(Class.id == class_id, Class.school_id == school_id)
        .options(joinedload(Class.form_teacher).joinedload(Teacher.user))
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def delete_class(db: AsyncSession, class_obj: Class) -> None:
    """Deletes a class from the database."""
    await db.delete(class_obj)
    await db.commit()