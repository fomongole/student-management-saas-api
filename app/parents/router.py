from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.parents import schemas, service

router = APIRouter()

@router.post("/onboard", response_model=list[schemas.ParentStudentLinkResponse], status_code=status.HTTP_201_CREATED)
async def onboard_parent_account(
    data: schemas.ParentOnboardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin creates a parent account and links them to students."""
    return await service.onboard_parent(db, data, current_user)

@router.get("/my-children", response_model=list[schemas.LinkedChildResponse])
async def get_my_children(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Parent fetches a list of their linked students."""
    return await service.fetch_my_children(db, current_user)