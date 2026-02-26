from app.classes import schemas
from app.core.exceptions import ClassAlreadyExistsException, ForbiddenException
from sqlalchemy.ext.asyncio import AsyncSession

from app.classes.schemas import ClassCreate
from app.classes.models import Class
from app.classes import repository
from app.auth.models import User
from app.core.enums import UserRole

async def create_new_class(db: AsyncSession, class_in: ClassCreate, current_user: User) -> Class:

    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can manage classes.")

    if not current_user.school_id:
        raise ForbiddenException("User is not associated with any school.")

    existing_class = await repository.get_class_by_details(
        db, current_user.school_id, class_in.name, class_in.stream
    )

    if existing_class:
        raise ClassAlreadyExistsException()

    return await repository.create_class(db, class_in, current_user.school_id)


from typing import Sequence
import uuid
from app.core.exceptions import NotFoundException

async def get_school_classes(db: AsyncSession, current_user: User) -> Sequence[Class]:
    if not current_user.school_id:
        raise ForbiddenException("User is not associated with any school.")
    return await repository.get_all_classes_for_school(db, current_user.school_id)

async def update_class_details(
    db: AsyncSession, 
    class_id: uuid.UUID, 
    class_in: schemas.ClassUpdate, 
    current_user: User
) -> Class:
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can update classes.")
        
    target_class = await repository.get_class_by_id(db, class_id, current_user.school_id)
    if not target_class:
        raise NotFoundException("Class not found.")

    update_data = class_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(target_class, field, value)

    db.add(target_class)
    await db.commit()
    await db.refresh(target_class)
    return target_class

async def remove_class(db: AsyncSession, class_id: uuid.UUID, current_user: User) -> None:
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can delete classes.")
        
    target_class = await repository.get_class_by_id(db, class_id, current_user.school_id)
    if not target_class:
        raise NotFoundException("Class not found.")
        
    # Note: If there are students linked to this class, SQLAlchemy will raise an IntegrityError 
    # depending on your foreign key cascade settings. Your global exception handler will catch it.
    await repository.delete_class(db, target_class)