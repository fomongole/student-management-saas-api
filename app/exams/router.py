from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.exams import schemas, service

router = APIRouter()

@router.post("/", response_model=schemas.ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam_session(
    exam_in: schemas.ExamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registers a new examination session (e.g., Term 1 Finals)."""
    return await service.create_new_exam(db, exam_in, current_user)

@router.post("/submit-results", response_model=list[schemas.ResultResponse], status_code=status.HTTP_201_CREATED)
async def submit_student_results(
    data: schemas.BulkResultSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk mark entry for a class of students. Handles updates automatically."""
    return await service.submit_marks(db, data, current_user)