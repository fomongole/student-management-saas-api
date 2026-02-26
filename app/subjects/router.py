import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AcademicLevel
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

from fastapi import Query
from typing import List

@router.get("/", response_model=List[schemas.SubjectResponse], status_code=status.HTTP_200_OK)
async def list_subjects(
    level: AcademicLevel | None = Query(None, description="Filter by Academic Level"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves all subjects, optionally filtered by academic level."""
    return await service.list_school_subjects(db, current_user, level)

@router.get("/teachers/{teacher_id}", response_model=List[schemas.TeacherSubjectDetailResponse])
async def list_teacher_subjects(
    teacher_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves all subjects assigned to a specific teacher."""
    return await service.get_assigned_subjects_for_teacher(db, teacher_id, current_user)

@router.patch("/{subject_id}", response_model=schemas.SubjectResponse)
async def update_subject(
    subject_id: uuid.UUID,
    subject_in: schemas.SubjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates curriculum details."""
    return await service.update_subject_details(db, subject_id, subject_in, current_user)

@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    subject_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Removes a subject from the curriculum."""
    await service.remove_subject(db, subject_id, current_user)