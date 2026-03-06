from datetime import datetime
import uuid
from sqlalchemy import select, delete, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.exc import IntegrityError

from app.teachers.models import Teacher
from app.auth.models import User
from app.core.exceptions import ConflictException

async def generate_employee_number(db: AsyncSession, school_id: uuid.UUID) -> str:
    current_year = datetime.now().year
    query = select(func.count(Teacher.id)).where(Teacher.school_id == school_id)
    count = (await db.execute(query)).scalar() or 0
    return f"EMP-{current_year}-{(count + 1):03d}"

async def create_teacher_transaction(db: AsyncSession, new_user: User, new_teacher: Teacher) -> Teacher:
    """Executes the database transaction to save the User and Teacher profiles."""
    db.add(new_user)
    await db.flush() 
    
    new_teacher.user_id = new_user.id
    db.add(new_teacher)
    
    await db.commit()
    
    # NOT using db.refresh(). Instead, re-fetching the complete object 
    # to guarantee all relationships (User, assigned_subjects) are loaded for Pydantic.
    return await get_teacher_with_user(db, new_teacher.id, new_teacher.school_id)

async def get_teachers_with_pagination(
    db: AsyncSession, 
    school_id: uuid.UUID, 
    skip: int, 
    limit: int, 
    search: str | None
):
    query = select(Teacher).where(Teacher.school_id == school_id)
    
    query = query.options(
        joinedload(Teacher.user),
        selectinload(Teacher.assigned_subjects)
    )

    if search:
        query = query.join(User).where(
            or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                Teacher.employee_number.ilike(f"%{search}%")
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.execute(count_query)
    
    result = await db.execute(query.offset(skip).limit(limit))
    return total.scalar_one(), result.scalars().all()

async def get_teacher_with_user(db: AsyncSession, teacher_id: uuid.UUID, school_id: uuid.UUID) -> Teacher | None:
    query = select(Teacher).options(
        joinedload(Teacher.user),
        selectinload(Teacher.assigned_subjects)
    ).where(
        and_(Teacher.id == teacher_id, Teacher.school_id == school_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def update_teacher_transaction(db: AsyncSession, teacher: Teacher, update_data: dict) -> Teacher:
    user = teacher.user
    
    for key, value in update_data.items():
        if key in ['first_name', 'last_name']:
            setattr(user, key, value)
        elif hasattr(teacher, key):
            setattr(teacher, key, value)
            
    db.add(user)
    db.add(teacher)
    await db.commit()
    
    return await get_teacher_with_user(db, teacher.id, teacher.school_id)

async def get_teacher_by_user_id(db: AsyncSession, user_id: uuid.UUID, school_id: uuid.UUID) -> Teacher | None:
    query = select(Teacher).options(
        joinedload(Teacher.user),
        selectinload(Teacher.assigned_subjects)
    ).where(
        and_(Teacher.user_id == user_id, Teacher.school_id == school_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


# Secure direct deletion
async def delete_teacher_direct(db: AsyncSession, teacher_id: uuid.UUID, school_id: uuid.UUID) -> bool:
    """
    Deletes the underlying User account, which automatically cascades in Postgres 
    to delete the Teacher profile and remove them from classes/subjects.
    """
    query = select(Teacher.user_id).where(Teacher.id == teacher_id, Teacher.school_id == school_id)
    user_id = (await db.execute(query)).scalar_one_or_none()
    
    if not user_id:
        return False
        
    stmt = delete(User).where(User.id == user_id, User.school_id == school_id)
    
    try:
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
    except IntegrityError:
        await db.rollback()
        raise ConflictException(
            code="TEACHER_RESTRICTED",
            message="Cannot delete this teacher due to strict database links."
        )