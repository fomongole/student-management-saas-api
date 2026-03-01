import uuid
from typing import Sequence

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.classes.models import Class
from app.classes.schemas import ClassCreate
from app.teachers.models import Teacher
from app.core.exceptions import ConflictException


async def get_class_by_details(db: AsyncSession, school_id: uuid.UUID, name: str, stream: str | None) -> Class | None:
    """Checks if a class with the same name and stream already exists in THIS specific school."""
    stream_condition = Class.stream.is_(None) if stream is None else Class.stream == stream
    
    query = select(Class).where(
        Class.school_id == school_id,
        Class.name == name,
        stream_condition
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_class_by_id(db: AsyncSession, class_id: uuid.UUID, school_id: uuid.UUID) -> Class | None:
    """Fetches a specific class, safely loading teacher info for the UI."""
    query = (
        select(Class)
        .where(Class.id == class_id, Class.school_id == school_id)
        .options(selectinload(Class.form_teacher).selectinload(Teacher.user))
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_class(db: AsyncSession, class_in: ClassCreate, school_id: uuid.UUID) -> Class:
    """Saves a new class."""
    new_class = Class(
        name=class_in.name,
        stream=class_in.stream,
        level=class_in.level,
        capacity=class_in.capacity,
        school_id=school_id,
        form_teacher_id=class_in.form_teacher_id 
    )
    db.add(new_class)
    await db.commit()
    
    # We MUST re-fetch the object here so SQLAlchemy loads the form_teacher
    # relationship. This prevents the 500 error when Pydantic serializes the response.
    return await get_class_by_id(db, new_class.id, school_id)


async def get_all_classes_for_school(db: AsyncSession, school_id: uuid.UUID) -> Sequence[Class]:
    """Fetches all classes belonging to a specific school."""
    query = (
        select(Class)
        .where(Class.school_id == school_id)
        .options(selectinload(Class.form_teacher).selectinload(Teacher.user))
        .order_by(Class.level, Class.name, Class.stream)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def delete_class_direct(db: AsyncSession, class_id: uuid.UUID, school_id: uuid.UUID) -> bool:
    """
    Industry-Standard Delete: Bypasses ORM memory completely to avoid async lazy-load crashes.
    Sends a direct DELETE statement to Postgres.
    """
    stmt = delete(Class).where(
        Class.id == class_id,
        Class.school_id == school_id
    )
    
    try:
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0  # Returns True if a row was actually deleted
        
    except IntegrityError:
        # Postgres blocked the deletion because foreign keys (like Students) exist!
        await db.rollback()
        raise ConflictException(
            code="CLASS_HAS_ENROLLMENTS",
            message="Cannot delete this class because it currently has students or fee structures linked to it."
        )