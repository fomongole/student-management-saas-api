import uuid
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.students.models import Student
from app.auth.models import User

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