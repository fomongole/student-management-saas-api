import uuid

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

@router.get("/", response_model=list[schemas.ParentListResponse])
async def list_parents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin endpoint to fetch the directory of parents."""
    return await service.get_school_parents(db, current_user)

@router.post("/{parent_id}/link", response_model=list[schemas.ParentStudentLinkResponse])
async def link_additional_students(
    parent_id: uuid.UUID,
    data: schemas.ParentLinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Links siblings/additional students to an existing parent account."""
    return await service.link_existing_parent(db, parent_id, data, current_user)

@router.delete("/{parent_id}/link/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_student(
    parent_id: uuid.UUID,
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Removes a student from a parent's portal access."""
    await service.sever_parent_link(db, parent_id, student_id, current_user)
    
@router.get("/", response_model=list[schemas.ParentListResponse])
async def list_parents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin endpoint to fetch the directory of parents and their linked children."""
    return await service.get_school_parents(db, current_user)

@router.patch("/{parent_id}", response_model=schemas.ParentListResponse)
async def edit_parent(
    parent_id: uuid.UUID,
    data: schemas.ParentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates parent details or suspends their account."""
    return await service.update_parent_profile(db, parent_id, data, current_user)

@router.delete("/{parent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_parent(
    parent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Hard deletes a parent account. Safe operation; does not delete students."""
    await service.remove_parent_account(db, parent_id, current_user)