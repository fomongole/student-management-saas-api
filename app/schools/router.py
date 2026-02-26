from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.schools import schemas, service

from typing import List
import uuid

router = APIRouter()

@router.post("/", response_model=schemas.SchoolResponse, status_code=status.HTTP_201_CREATED)
async def create_school(
    school_in: schemas.SchoolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Onboards a new School (Tenant).
    Requires a valid JWT token from a SUPER_ADMIN.
    """
    return await service.create_new_school(db, school_in, current_user)

@router.get("/dashboard", response_model=schemas.SuperAdminDashboardResponse)
async def get_platform_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns platform-wide SaaS metrics.
    Requires a valid JWT token from a SUPER_ADMIN.
    """
    return await service.generate_super_admin_dashboard(db, current_user)



@router.get("/", response_model=List[schemas.SchoolWithCountResponse], status_code=status.HTTP_200_OK)
async def list_all_schools(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a list of all registered schools and their active student counts.
    Ideal for populating the primary data table on the Super Admin dashboard.
    Requires a valid JWT token from a SUPER_ADMIN.
    """
    return await service.get_all_schools(db, current_user)

@router.patch("/{school_id}", response_model=schemas.SchoolResponse, status_code=status.HTTP_200_OK)
async def update_school(
    school_id: uuid.UUID,
    school_in: schemas.SchoolUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates a school's profile details.
    To suspend a school, pass {"is_active": false} in the JSON body.
    Requires a valid JWT token from a SUPER_ADMIN.
    """
    return await service.update_school_details(db, school_id, school_in, current_user)