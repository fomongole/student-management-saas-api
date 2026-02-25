from sqlalchemy.ext.asyncio import AsyncSession
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
    # without triggering an implicit lazy-load query!
    new_teacher.user = new_user
    
    return new_teacher