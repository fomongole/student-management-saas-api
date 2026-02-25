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