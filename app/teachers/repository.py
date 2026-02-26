from sqlalchemy.ext.asyncio import AsyncSession
from app.teachers.models import Teacher
from app.auth.models import User
from sqlalchemy.orm import joinedload
from sqlalchemy import select, func, or_, and_
import uuid

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
    # without triggering an implicit lazy-load query!
    new_teacher.user = new_user
    
    return new_teacher

async def get_teachers_with_pagination(
    db: AsyncSession, 
    school_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 50,
    search: str | None = None
) -> tuple[int, list[Teacher]]:
    """Fetches teachers with eager-loaded user profiles, supporting search and pagination."""
    query = select(Teacher).join(Teacher.user).where(Teacher.school_id == school_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Teacher.employee_number.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                User.email.ilike(search_term)
            )
        )
        
    # Get Total Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Fetch paginated records WITH user relationship loaded
    query = query.options(joinedload(Teacher.user)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return total, list(items)

async def get_teacher_with_user(db: AsyncSession, teacher_id: uuid.UUID, school_id: uuid.UUID) -> Teacher | None:
    """Fetches a single teacher and eager-loads the User entity."""
    query = select(Teacher).options(joinedload(Teacher.user)).where(
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
    
    await db.refresh(teacher)
    await db.refresh(user)
    teacher.user = user
    return teacher