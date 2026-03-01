"""
Class Service Layer

This module contains business logic for managing classes within a school.
It enforces:
- Role-based access control (Only SCHOOL_ADMIN can manage classes)
- School-level data isolation (users can only manage classes in their school)
- Duplicate prevention (same class name + stream per school)
"""

from typing import Sequence
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.classes import repository
from app.classes.models import Class
from app.classes.schemas import ClassCreate, ClassUpdate
from app.auth.models import User
from app.core.enums import UserRole
from app.core.exceptions import (
    ClassAlreadyExistsException,
    ForbiddenException,
    NotFoundException,
)

async def create_new_class(
    db: AsyncSession,
    class_in: ClassCreate,
    current_user: User
) -> Class:
    # Role check
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can manage classes.")

    if not current_user.school_id:
        raise ForbiddenException("User is not associated with any school.")

    # Duplicate check
    existing_class = await repository.get_class_by_details(
        db=db,
        school_id=current_user.school_id,
        name=class_in.name,
        stream=class_in.stream,
    )

    if existing_class:
        raise ClassAlreadyExistsException()

    # Create class
    return await repository.create_class(
        db=db,
        class_in=class_in,
        school_id=current_user.school_id,
    )


async def get_school_classes(
    db: AsyncSession,
    current_user: User
) -> Sequence[Class]:
    if not current_user.school_id:
        raise ForbiddenException("User is not associated with any school.")

    return await repository.get_all_classes_for_school(
        db=db,
        school_id=current_user.school_id,
    )
    

async def update_class_details(
    db: AsyncSession,
    class_id: uuid.UUID,
    class_in: ClassUpdate,
    current_user: User
) -> Class:
    # Role check
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can update classes.")

    if not current_user.school_id:
        raise ForbiddenException("User is not associated with any school.")

    # Fetch target class
    target_class = await repository.get_class_by_id(
        db=db,
        class_id=class_id,
        school_id=current_user.school_id,
    )

    if not target_class:
        raise NotFoundException("Class not found.")

    update_data = class_in.model_dump(exclude_unset=True)

    # Check for duplicates if name/stream changed
    new_name = update_data.get("name", target_class.name)
    new_stream = update_data.get("stream", target_class.stream)

    existing_class = await repository.get_class_by_details(
        db=db,
        school_id=current_user.school_id,
        name=new_name,
        stream=new_stream,
    )

    if existing_class and existing_class.id != target_class.id:
        raise ClassAlreadyExistsException()

    # Apply updates
    for field, value in update_data.items():
        setattr(target_class, field, value)

    db.add(target_class)
    await db.commit()
    
    # Do not use db.refresh(target_class) here because it unloads relationships.
    # Instead, re-fetch the full object using the repository method.
    return await repository.get_class_by_id(db, target_class.id, current_user.school_id)


async def remove_class(
    db: AsyncSession,
    class_id: uuid.UUID,
    current_user: User
) -> None:
    # Role check
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can delete classes.")

    if not current_user.school_id:
        raise ForbiddenException("User is not associated with any school.")

    target_class = await repository.get_class_by_id(
        db=db,
        class_id=class_id,
        school_id=current_user.school_id,
    )

    if not target_class:
        raise NotFoundException("Class not found.")

    # Execute deletion (Repository will handle constraint exceptions)
    await repository.delete_class(db=db, target_class=target_class)