from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.subjects import schemas, service

router = APIRouter()

@router.post("/", response_model=schemas.SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject_in: schemas.SubjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Adds a subject to the school curriculum."""
    return await service.create_new_subject(db, subject_in, current_user)

@router.post("/assign", response_model=list[schemas.TeacherSubjectResponse])
async def assign_subjects(
    assignment_in: schemas.SubjectAssignment,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assigns a list of subjects to a teacher."""
    return await service.assign_teacher_curriculum(db, assignment_in, current_user)