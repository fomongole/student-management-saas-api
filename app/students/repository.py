from datetime import datetime
import uuid
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.students.models import Student
from app.auth.models import User

from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import func, or_
from app.classes.models import Class

async def generate_admission_number(db: AsyncSession, school_id: uuid.UUID) -> str:
    """
    Counts current students and generates a sequence: ADM-2026-0001
    Safe from race conditions due to the DB UniqueConstraint.
    """
    current_year = datetime.now().year
    query = select(func.count(Student.id)).where(Student.school_id == school_id)
    count = (await db.execute(query)).scalar() or 0
    
    return f"ADM-{current_year}-{(count + 1):04d}"


async def get_student(db: AsyncSession, student_id: uuid.UUID, school_id: uuid.UUID) -> Student | None:
    """
    Fetches a student by ID, strictly scoped to the tenant (school_id).
    Serves as a read-only validation endpoint for other modules (like Fees).
    """
    query = select(Student).where(
        and_(
            Student.id == student_id, 
            Student.school_id == school_id
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_student_transaction(db: AsyncSession, new_user: User, new_student: Student) -> Student:
    """
    Executes the database transaction to save the User and Student profiles securely.
    """
    # 1. Save the user first to generate the UUID
    db.add(new_user)
    await db.flush() 
    
    # 2. Attach the generated User ID to the Student profile and save it
    new_student.user_id = new_user.id
    db.add(new_student)
    
    # 3. Commit both to the database at the same time
    await db.commit()
    await db.refresh(new_student)
    
    # Attach the user object to prevent lazy-load crashes
    new_student.user = new_user
    
    return new_student


async def get_students_with_pagination(
    db: AsyncSession, 
    school_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 50,
    class_id: uuid.UUID | None = None,
    search: str | None = None
) -> tuple[int, list[Student]]:
    
    query = select(Student).join(Student.user).join(Student.class_relationship).where(
        Student.school_id == school_id
    )
    
    if class_id:
        query = query.where(Student.class_id == class_id)
        
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Student.admission_number.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
                User.email.ilike(search_term)
            )
        )
        
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    query = query.options(
        joinedload(Student.user), 
        joinedload(Student.class_relationship),
        selectinload(Student.parents) 
    ).offset(skip).limit(limit)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return total, list(items)

async def get_student_with_user(db: AsyncSession, student_id: uuid.UUID, school_id: uuid.UUID) -> Student | None:
    """Fetches a single student and eager-loads the User entity to prepare for updates."""
    query = select(Student).options(joinedload(Student.user)).where(
        and_(Student.id == student_id, Student.school_id == school_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def update_student_transaction(db: AsyncSession, student: Student, update_data: dict) -> Student:
    """Updates the Student and underlying User model in a single transaction."""
    user = student.user
    
    for key, value in update_data.items():
        if key in ['first_name', 'last_name']:
            setattr(user, key, value)
        elif hasattr(student, key):
            setattr(student, key, value)
            
    db.add(user)
    db.add(student)
    await db.commit()
    
    # Refresh to ensure we return the latest DB state
    await db.refresh(student)
    await db.refresh(user)
    student.user = user
    return student

async def get_student_by_user_id(db: AsyncSession, user_id: uuid.UUID, school_id: uuid.UUID) -> Student | None:
    """Fetches a student profile using their linked User account ID."""
    query = (
        select(Student)
        .options(
            joinedload(Student.user),
            joinedload(Student.class_relationship)
        )
        .where(
            and_(Student.user_id == user_id, Student.school_id == school_id)
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()