from sqlalchemy.ext.asyncio import AsyncSession

from app.teachers import schemas
from app.teachers.schemas import TeacherCreate
from app.teachers.models import Teacher
from app.teachers import repository as teacher_repo
from app.auth.models import User
from app.auth import repository as auth_repo
from app.core.security import get_password_hash
from app.core.enums import UserRole
from app.core.exceptions import (
    ForbiddenException,
    UserEmailAlreadyExistsException,
)

import uuid
from app.core.exceptions import NotFoundException


async def onboard_teacher(
    db: AsyncSession,
    teacher_in: TeacherCreate,
    current_user: User,
) -> Teacher:

    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can onboard teachers.")

    if await auth_repo.get_user_by_email(db, teacher_in.email):
        raise UserEmailAlreadyExistsException()

    generated_emp_number = await teacher_repo.generate_employee_number(
        db, current_user.school_id
    )

    new_user = User(
        email=teacher_in.email,
        hashed_password=get_password_hash(teacher_in.password),
        first_name=teacher_in.first_name,
        last_name=teacher_in.last_name,
        role=UserRole.TEACHER,
        school_id=current_user.school_id,
    )

    new_teacher = Teacher(
        employee_number=generated_emp_number,
        qualification=teacher_in.qualification,
        specialization=teacher_in.specialization,
        school_id=current_user.school_id,
    )

    return await teacher_repo.create_teacher_transaction(db, new_user, new_teacher)

async def get_paginated_teachers(
    db: AsyncSession,
    current_user: User,
    skip: int,
    limit: int,
    search: str | None
) -> schemas.PaginatedTeacherResponse:
    
    if current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.TEACHER]:
        raise ForbiddenException("You are not authorized to view the staff directory.")

    total, teachers = await teacher_repo.get_teachers_with_pagination(
        db, current_user.school_id, skip, limit, search
    )
    
    return schemas.PaginatedTeacherResponse(total=total, items=teachers)

async def update_teacher_profile(
    db: AsyncSession,
    teacher_id: uuid.UUID,
    teacher_in: schemas.TeacherUpdate,
    current_user: User
) -> Teacher:
    
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can update teacher profiles.")
        
    teacher = await teacher_repo.get_teacher_with_user(db, teacher_id, current_user.school_id)
    if not teacher:
        raise NotFoundException("Teacher not found.")
            
    update_data = teacher_in.model_dump(exclude_unset=True)
    return await teacher_repo.update_teacher_transaction(db, teacher, update_data)

async def get_my_teacher_profile(db: AsyncSession, current_user: User) -> Teacher:
    """
    Retrieves the teacher profile for the currently authenticated user.
    """
    if current_user.role != UserRole.TEACHER:
        raise ForbiddenException("Only teachers can access this endpoint.")
        
    teacher = await teacher_repo.get_teacher_by_user_id(db, current_user.id, current_user.school_id)
    
    if not teacher:
        raise NotFoundException("Teacher profile not found for this user.")
        
    return teacher

async def remove_teacher(db: AsyncSession, teacher_id: uuid.UUID, current_user: User) -> None:
    """Enforces RBAC before deleting a teacher."""
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can remove teachers from the directory.")
        
    deleted = await teacher_repo.delete_teacher_direct(db, teacher_id, current_user.school_id)
    
    if not deleted:
        raise NotFoundException("Teacher not found.")