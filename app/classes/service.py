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

async def create_new_class(db: AsyncSession, class_in: ClassCreate, current_user: User) -> Class:
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can manage classes.")

    existing_class = await repository.get_class_by_details(
        db=db,
        school_id=current_user.school_id,
        name=class_in.name,
        stream=class_in.stream,
    )

    if existing_class:
        raise ClassAlreadyExistsException()

    return await repository.create_class(
        db=db,
        class_in=class_in,
        school_id=current_user.school_id,
    )


async def get_school_classes(db: AsyncSession, current_user: User) -> Sequence[Class]:
    # Allow teachers to read the class list too if needed
    if current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.TEACHER]:
        raise ForbiddenException("Unauthorized.")

    return await repository.get_all_classes_for_school(
        db=db,
        school_id=current_user.school_id,
    )
    

async def update_class_details(db: AsyncSession, class_id: uuid.UUID, class_in: ClassUpdate, current_user: User) -> Class:
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can update classes.")

    target_class = await repository.get_class_by_id(
        db=db,
        class_id=class_id,
        school_id=current_user.school_id,
    )

    if not target_class:
        raise NotFoundException("Class not found.")

    update_data = class_in.model_dump(exclude_unset=True)

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

    for field, value in update_data.items():
        setattr(target_class, field, value)

    db.add(target_class)
    await db.commit()
    
    # We MUST re-fetch the object so we don't return stale relationships
    return await repository.get_class_by_id(db, target_class.id, current_user.school_id)


async def remove_class(db: AsyncSession, class_id: uuid.UUID, current_user: User) -> None:
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can delete classes.")

    # Call the highly optimized direct SQL execution
    deleted = await repository.delete_class_direct(
        db=db,
        class_id=class_id,
        school_id=current_user.school_id
    )

    if not deleted:
        raise NotFoundException("Class not found.")