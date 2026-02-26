import uuid

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

from fastapi import Query
from typing import List

@router.get("/", response_model=List[schemas.ExamResponse])
async def list_exams(
    year: int | None = Query(None, description="Filter by academic year"),
    term: int | None = Query(None, description="Filter by term"),
    subject_id: uuid.UUID | None = Query(None, description="Filter by subject"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves a list of exam sessions for the school."""
    return await service.list_exam_sessions(db, current_user, year, term, subject_id)

@router.get("/{exam_id}/class/{class_id}", response_model=List[schemas.StudentMarkSheetDetail])
async def get_mark_sheet(
    exam_id: uuid.UUID,
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetches the mark sheet for a specific exam and class.
    Returns all students in the class with their current scores (if any).
    """
    return await service.generate_mark_sheet(db, exam_id, class_id, current_user)