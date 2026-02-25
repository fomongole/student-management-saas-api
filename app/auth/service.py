from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import schemas, repository
from app.auth.models import User
from app.auth.schemas import UserCreate
from app.core.security import get_password_hash, verify_password
from app.core.enums import UserRole
from app.schools.repository import get_school_by_id
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    UserEmailAlreadyExistsException,
)


async def create_super_admin(db: AsyncSession, user_in: UserCreate) -> User:
    if await repository.get_user_by_email(db, user_in.email):
        raise UserEmailAlreadyExistsException()

    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        role=UserRole.SUPER_ADMIN,
        school_id=None,
    )

    return await repository.create_user(db, new_user)


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await repository.get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_school_admin(
    db: AsyncSession,
    user_in: schemas.SchoolAdminCreate,
    current_user: User,
) -> User:

    if current_user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenException(
            "Only Super Admins can create School Admins."
        )

    school = await get_school_by_id(db, user_in.school_id)
    if not school:
        raise NotFoundException("School does not exist.")

    if await repository.get_user_by_email(db, user_in.email):
        raise UserEmailAlreadyExistsException()

    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        role=UserRole.SCHOOL_ADMIN,
        school_id=user_in.school_id,
    )

    return await repository.create_user(db, new_user)