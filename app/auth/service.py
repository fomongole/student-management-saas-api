from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import schemas, repository
from app.auth.models import User
from app.auth.schemas import UserCreate
from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.enums import UserRole
from app.schools.repository import get_school_by_id
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    UserEmailAlreadyExistsException,
)
from fastapi import HTTPException, status

async def create_super_admin(db: AsyncSession, user_in: UserCreate, bootstrap_token: str) -> User:
    """Business logic for creating a Super Admin, including token validation."""
    expected_token = getattr(settings, "BOOTSTRAP_TOKEN", settings.SECRET_KEY)
    
    if bootstrap_token != expected_token:
        raise ForbiddenException("Invalid bootstrap token.")

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


async def process_login(db: AsyncSession, email: str, password: str) -> dict:
    """Orchestrates authentication, business rule validation, and token generation."""
    user = await repository.get_user_by_email(db, email)
    
    # 1. Check existence and password
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
        
    # 2. Check User status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
        
    # 3. Check Tenant (School) suspension status
    if user.school_id is not None and user.school:
        if not user.school.is_active or user.school.deleted_at is not None:
            raise ForbiddenException("Your school's account has been suspended. Please contact the platform administrator.")
    
    # 4. Generate Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


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