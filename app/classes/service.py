"""
Class Service Layer

This module contains business logic for managing classes within a school.
It enforces:

- Role-based access control (Only SCHOOL_ADMIN can manage classes)
- School-level data isolation (users can only manage classes in their school)
- Duplicate prevention (same class name + stream per school)
- Proper exception handling using custom domain exceptions

All database operations are delegated to the repository layer.
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
    """
    Create a new class for the current user's school.

    Rules:
    - Only SCHOOL_ADMIN can create classes
    - User must belong to a school
    - Class name + stream combination must be unique per school
    """

    # Role check
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can manage classes.")

    # School association check
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
    """
    Retrieve all classes belonging to the current user's school.

    Rules:
    - User must belong to a school
    """

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
    """
    Update class details.

    Rules:
    - Only SCHOOL_ADMIN can update classes
    - Class must belong to the user's school
    - Prevent duplicate name + stream combination
    """

    # Role check
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can update classes.")

    if not current_user.school_id:
        raise ForbiddenException("User is not associated with any school.")

    # Fetch target class (scoped to school)
    target_class = await repository.get_class_by_id(
        db=db,
        class_id=class_id,
        school_id=current_user.school_id,
    )

    if not target_class:
        raise NotFoundException("Class not found.")

    update_data = class_in.model_dump(exclude_unset=True)

    # If name or stream is being updated → check duplicate
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
    await db.refresh(target_class)

    return target_class

async def remove_class(
    db: AsyncSession,
    class_id: uuid.UUID,
    current_user: User
) -> None:
    """
    Delete a class.

    Rules:
    - Only SCHOOL_ADMIN can delete classes
    - Class must belong to the user's school

    Note:
    If students are linked to this class, an IntegrityError may be raised
    depending on the foreign key cascade settings.
    The global exception handler should handle that case.
    """

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

    await repository.delete_class(db=db, target_class=target_class)