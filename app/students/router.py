from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.students import schemas, service
from fastapi import Query
import uuid

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


@router.get("/", response_model=schemas.PaginatedStudentResponse, status_code=status.HTTP_200_OK)
async def list_students(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    class_id: uuid.UUID | None = Query(None, description="Filter by a specific class"),
    search: str | None = Query(None, description="Search by Name, Email, or Admission No."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a paginated list of students belonging to the current user's school.
    Includes robust filtering to support frontend data tables.
    """
    return await service.get_paginated_students(db, current_user, skip, limit, class_id, search)

@router.get("/me", response_model=schemas.StudentListResponse, status_code=status.HTTP_200_OK)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves the student profile for the logged-in student."""
    return await service.get_my_student_profile(db, current_user)

@router.patch("/{student_id}", response_model=schemas.StudentResponse, status_code=status.HTTP_200_OK)
async def update_student(
    student_id: uuid.UUID,
    student_in: schemas.StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates a student's academic or personal details.
    Safely handles updates to both the `Student` entity and the underlying `User` entity.
    """
    return await service.update_student_profile(db, student_id, student_in, current_user)