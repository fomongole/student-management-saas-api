from sqlalchemy.ext.asyncio import AsyncSession

from app.parents import repository, schemas
from app.auth.models import User
from app.core.enums import UserRole
from app.core.security import get_password_hash
from app.auth import repository as auth_repo
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    UserEmailAlreadyExistsException,
)

async def onboard_parent(
    db: AsyncSession,
    data: schemas.ParentOnboardCreate,
    current_user: User,
):
    """
    Creates a Parent Portal account and links it to students atomically.
    """
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can onboard parents.")

    if await auth_repo.get_user_by_email(db, data.email):
        raise UserEmailAlreadyExistsException()

    # PERFORMANCE: Validate all students belong to this school in ONE query
    is_valid = await repository.validate_students_exist(
        db, data.student_ids, current_user.school_id
    )
    
    if not is_valid:
        raise NotFoundException("One or more Student IDs were not found in your school.")

    new_parent_user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        role=UserRole.PARENT,
        school_id=current_user.school_id,
    )

    return await repository.create_parent_and_links(
        db,
        new_parent_user,
        data.student_ids,
        current_user.school_id,
    )

async def fetch_my_children(
    db: AsyncSession,
    current_user: User,
):
    """
    Returns the authenticated parent's linked children.
    """
    if current_user.role != UserRole.PARENT:
        raise ForbiddenException("Only Parents can access this portal endpoint.")

    students = await repository.get_children_for_parent(
        db, current_user.id, current_user.school_id
    )

    return [
        schemas.LinkedChildResponse(
            student_id=s.id,
            first_name=s.user.first_name,
            last_name=s.user.last_name, 
            admission_number=s.admission_number,
            class_id=s.class_id,
        )
        for s in students
    ]