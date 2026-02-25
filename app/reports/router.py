from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.reports import schemas, service

router = APIRouter()

@router.get("/dashboard", response_model=schemas.AdminDashboardResponse)
async def get_admin_dashboard(
    year: int,
    term: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetches high-level metrics for the School Administrator's dashboard."""
    return await service.generate_admin_dashboard(db, year, term, current_user)