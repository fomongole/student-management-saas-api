from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.teachers import schemas, service
from fastapi import Query
import uuid

router = APIRouter()

@router.post("/", response_model=schemas.TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    teacher_in: schemas.TeacherCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Onboards a new teacher for the school."""
    return await service.onboard_teacher(db, teacher_in, current_user)

@router.get("/", response_model=schemas.PaginatedTeacherResponse, status_code=status.HTTP_200_OK)
async def list_teachers(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by Name, Email, or Employee No."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves a paginated list of teachers for the school."""
    return await service.get_paginated_teachers(db, current_user, skip, limit, search)

@router.get("/me", response_model=schemas.TeacherResponse, status_code=status.HTTP_200_OK)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves the teacher profile and assigned subjects for the logged-in teacher."""
    return await service.get_my_teacher_profile(db, current_user)

@router.patch("/{teacher_id}", response_model=schemas.TeacherResponse, status_code=status.HTTP_200_OK)
async def update_teacher(
    teacher_id: uuid.UUID,
    teacher_in: schemas.TeacherUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates a teacher's professional details or underlying user name."""
    return await service.update_teacher_profile(db, teacher_id, teacher_in, current_user)