import uuid
from typing import Sequence

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.classes.models import Class
from app.classes.schemas import ClassCreate
from app.core.enums import AcademicLevel
from app.teachers.models import Teacher
from app.core.exceptions import ConflictException


async def get_class_by_details(
    db: AsyncSession, 
    school_id: uuid.UUID, 
    name: str, 
    stream: str | None,
    category: str | None = None
) -> Class | None:
    """Checks if a class with the same name/stream/category already exists in THIS specific school."""
    stream_condition = Class.stream.is_(None) if stream is None else Class.stream == stream
    category_condition = Class.category.is_(None) if category is None else Class.category == category
    
    query = select(Class).where(
        Class.school_id == school_id,
        Class.name == name,
        stream_condition,
        category_condition,
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def count_distinct_class_names_by_level(
    db: AsyncSession, 
    school_id: uuid.UUID, 
    level: AcademicLevel
) -> int:
    """
    Counts the number of DISTINCT base class names for a given level in a school.

    Design note: streams are variants of the same base class (P1 EAST, P1 WEST 
    are both "P1"), so we count distinct names — not total rows — to enforce 
    the per-level class creation cap correctly.

    Example:
        P1 EAST, P1 WEST, P2 NORTH → 2 distinct names (P1, P2)
        S5 Sciences, S5 Arts, S6 Sciences → 2 distinct names (S5, S6)
    """
    query = select(func.count(func.distinct(Class.name))).where(
        Class.school_id == school_id,
        Class.level == level,
    )
    result = await db.execute(query)
    return result.scalar() or 0


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
        category=class_in.category,
        capacity=class_in.capacity,
        school_id=school_id,
        form_teacher_id=class_in.form_teacher_id 
    )
    db.add(new_class)
    await db.commit()
    
    # Re-fetching the object here so SQLAlchemy loads the form_teacher
    # relationship. This prevents the 500 error when Pydantic serializes the response.
    return await get_class_by_id(db, new_class.id, school_id)


async def get_all_classes_for_school(db: AsyncSession, school_id: uuid.UUID) -> Sequence[Class]:
    """Fetches all classes belonging to a specific school."""
    query = (
        select(Class)
        .where(Class.school_id == school_id)
        .options(selectinload(Class.form_teacher).selectinload(Teacher.user))
        .order_by(Class.level, Class.name, Class.stream, Class.category)
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