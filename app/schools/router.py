from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.schools import schemas, service

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