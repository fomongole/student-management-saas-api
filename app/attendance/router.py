from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.attendance import schemas, service

router = APIRouter()

@router.post("/", response_model=list[schemas.AttendanceResponse], status_code=status.HTTP_201_CREATED)
async def submit_attendance(
    data: schemas.AttendanceBulkCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marks attendance for a list of students and triggers alerts for absences."""
    return await service.mark_bulk_attendance(db, data, current_user, background_tasks)