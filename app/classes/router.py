from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.classes import schemas, service

from typing import List
import uuid

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

@router.get("/", response_model=List[schemas.ClassResponse], status_code=status.HTTP_200_OK)
async def list_classes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all classes for the currently authenticated user's school.
    """
    return await service.get_school_classes(db, current_user)

@router.patch("/{class_id}", response_model=schemas.ClassResponse, status_code=status.HTTP_200_OK)
async def update_class(
    class_id: uuid.UUID,
    class_in: schemas.ClassUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates specific fields of an existing class.
    """
    return await service.update_class_details(db, class_id, class_in, current_user)

@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a class. Will fail if students or teachers are currently assigned to it.
    """
    await service.remove_class(db, class_id, current_user)