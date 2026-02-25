from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.teachers import schemas, service

router = APIRouter()

@router.post("/", response_model=schemas.TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    teacher_in: schemas.TeacherCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Onboards a new teacher for the school."""
    return await service.onboard_teacher(db, teacher_in, current_user)