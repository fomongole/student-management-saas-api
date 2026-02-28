import uuid
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.teachers.models import Teacher
from app.auth.models import User

async def create_teacher_transaction(db: AsyncSession, new_user: User, new_teacher: Teacher) -> Teacher:
    """Executes the database transaction to save the User and Teacher profiles."""
    # 1. Save the user first to generate the UUID
    db.add(new_user)
    await db.flush() 
    
    # 2. Attach the generated User ID to the Teacher profile
    new_teacher.user_id = new_user.id
    db.add(new_teacher)
    
    # 3. Commit both safely
    await db.commit()
    await db.refresh(new_teacher)
    
    # 4. Manually attach the user object so Pydantic can serialize the TeacherResponse
    new_teacher.user = new_user
    
    # Initialize empty subjects list for new teacher response
    new_teacher.assigned_subjects = []
    
    return new_teacher

async def get_teachers_with_pagination(
    db: AsyncSession, 
    school_id: uuid.UUID, 
    skip: int, 
    limit: int, 
    search: str | None
):
    # Base Query
    query = select(Teacher).where(Teacher.school_id == school_id)
    
    # Eager Load Relationships
    query = query.options(
        joinedload(Teacher.user),
        selectinload(Teacher.assigned_subjects) # Crucial for the modal checks
    )

    if search:
        query = query.join(User).where(
            or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                Teacher.employee_number.ilike(f"%{search}%")
            )
        )

    # Count & Execute
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.execute(count_query)
    
    result = await db.execute(query.offset(skip).limit(limit))
    return total.scalar_one(), result.scalars().all()

async def get_teacher_with_user(db: AsyncSession, teacher_id: uuid.UUID, school_id: uuid.UUID) -> Teacher | None:
    """Fetches a single teacher and eager-loads the User entity and assigned subjects."""
    query = select(Teacher).options(
        joinedload(Teacher.user),
        selectinload(Teacher.assigned_subjects)
    ).where(
        and_(Teacher.id == teacher_id, Teacher.school_id == school_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def update_teacher_transaction(db: AsyncSession, teacher: Teacher, update_data: dict) -> Teacher:
    """Updates the Teacher and underlying User model atomically."""
    user = teacher.user
    
    for key, value in update_data.items():
        if key in ['first_name', 'last_name']:
            setattr(user, key, value)
        elif hasattr(teacher, key):
            setattr(teacher, key, value)
            
    db.add(user)
    db.add(teacher)
    await db.commit()
    
    # Refresh and re-load relationships to ensure clean state
    query = select(Teacher).options(
        joinedload(Teacher.user),
        selectinload(Teacher.assigned_subjects)
    ).where(Teacher.id == teacher.id)
    
    result = await db.execute(query)
    updated_teacher = result.scalar_one()
    
    return updated_teacher

async def get_teacher_by_user_id(db: AsyncSession, user_id: uuid.UUID, school_id: uuid.UUID) -> Teacher | None:
    """Fetches a teacher profile using their linked User account ID."""
    query = select(Teacher).options(
        joinedload(Teacher.user),
        selectinload(Teacher.assigned_subjects)
    ).where(
        and_(Teacher.user_id == user_id, Teacher.school_id == school_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()