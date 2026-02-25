from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.students import schemas, service

router = APIRouter()

@router.post("/", response_model=schemas.StudentResponse, status_code=status.HTTP_201_CREATED)
async def admit_student(
    student_in: schemas.StudentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admits a new student into a class and dispatches a welcome email."""
    return await service.onboard_student(db, student_in, current_user, background_tasks)