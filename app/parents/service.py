import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.parents import repository, schemas
from app.auth.models import User
from app.core.enums import UserRole
from app.core.security import get_password_hash
from app.auth import repository as auth_repo
from app.core.exceptions import (
    ConflictException,
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

    # Validates all students belong to this school in ONE query
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
            class_name=s.class_relationship.name,
        )
        for s in students
    ]
    
async def get_school_parents(db: AsyncSession, current_user: User) -> list[dict]:
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can view the parent directory.")
    return await repository.get_all_parents_with_children(db, current_user.school_id)

async def link_existing_parent(
    db: AsyncSession, 
    parent_id: uuid.UUID, 
    data: schemas.ParentLinkCreate, 
    current_user: User
):
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Unauthorized.")

    # Validates the new students belong to the school
    is_valid = await repository.validate_students_exist(db, data.student_ids, current_user.school_id)
    if not is_valid:
        raise ConflictException("INVALID_STUDENTS", "One or more students do not exist in your school.")

    return await repository.add_links_to_existing_parent(
        db, parent_id, data.student_ids, current_user.school_id
    )

async def sever_parent_link(
    db: AsyncSession, 
    parent_id: uuid.UUID, 
    student_id: uuid.UUID, 
    current_user: User
):
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Unauthorized.")
    await repository.remove_parent_link(db, parent_id, student_id, current_user.school_id)
    
async def update_parent_profile(db: AsyncSession, parent_id: uuid.UUID, data: schemas.ParentUpdate, current_user: User):
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Unauthorized.")
        
    update_data = data.model_dump(exclude_unset=True)
    
    # Check email conflict
    if "email" in update_data:
        existing = await auth_repo.get_user_by_email(db, update_data["email"])
        if existing and existing.id != parent_id:
            raise UserEmailAlreadyExistsException()
            
    updated = await repository.update_parent_user(db, parent_id, current_user.school_id, update_data)
    if not updated:
        raise NotFoundException("Parent not found.")
    
    # Refetching the whole list object so the UI gets the children array back immediately
    all_parents = await repository.get_all_parents_with_children(db, current_user.school_id)
    return next((p for p in all_parents if p["id"] == parent_id), None)

async def remove_parent_account(db: AsyncSession, parent_id: uuid.UUID, current_user: User):
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Unauthorized.")
        
    deleted = await repository.delete_parent_user(db, parent_id, current_user.school_id)
    if not deleted:
        raise NotFoundException("Parent not found.")