from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.classes import schemas, service

router = APIRouter()

@router.post("/", response_model=schemas.ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_in: schemas.ClassCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a new class/stream for the logged-in School Admin's school.
    """
    return await service.create_new_class(db, class_in, current_user)