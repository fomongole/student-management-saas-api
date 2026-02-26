from sqlalchemy.ext.asyncio import AsyncSession
from app.schools import schemas, repository
from app.schools.models import School
from app.auth.models import User
from app.core.enums import UserRole
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    SchoolAlreadyExistsException,
)

import uuid
from typing import List, Dict, Any
from app.core.exceptions import NotFoundException


async def create_new_school(
    db: AsyncSession,
    school_in: schemas.SchoolCreate,
    current_user: User,
) -> School:

    if current_user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenException(
            "Only Super Admins can onboard schools."
        )

    existing_school = await repository.get_school_by_email(db, school_in.email)
    if existing_school:
        raise SchoolAlreadyExistsException()

    return await repository.create_school(db, school_in)


async def generate_super_admin_dashboard(
    db: AsyncSession,
    current_user: User,
) -> schemas.SuperAdminDashboardResponse:

    if current_user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenException(
            "Only SaaS Platform Owners can view these metrics."
        )

    metrics = await repository.get_platform_metrics(db)

    return schemas.SuperAdminDashboardResponse(
        platform_metrics=schemas.PlatformMetrics(**metrics)
    )


async def get_all_schools(db: AsyncSession, current_user: User) -> List[Dict[str, Any]]:
    """
    Retrieves all non-deleted schools with their current student counts.
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenException("Only Super Admins can view the full school directory.")

    # Calls the optimized outerjoin query you already wrote in repository.py
    rows = await repository.get_all_schools_with_counts(db)
    
    # Unpack the SQLAlchemy Row tuples (School, student_count) into a format Pydantic can serialize
    result = []
    for school, student_count in rows:
        result.append({
            "id": school.id,
            "name": school.name,
            "email": school.email,
            "phone": school,
            "address": school.address,
            "is_active": school.is_active,
            "student_count": student_count
        })
        
    return result


async def update_school_details(
    db: AsyncSession, 
    school_id: uuid.UUID, 
    school_in: schemas.SchoolUpdate, 
    current_user: User
) -> School:
    """
    Updates school details or toggles suspension status.
    """
    # Note: Later, you might allow SCHOOL_ADMIN to update their *own* school's address/phone.
    # For now, keeping it strict to SUPER_ADMIN for SaaS-level management.
    if current_user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenException("Only Super Admins can modify school profiles.")

    school = await repository.get_school_by_id(db, school_id)
    if not school:
        raise NotFoundException("School not found.")

    # exclude_unset=True ensures we only update fields the client explicitly sent
    update_data = school_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(school, field, value)

    db.add(school)
    await db.commit()
    await db.refresh(school)
    
    return school