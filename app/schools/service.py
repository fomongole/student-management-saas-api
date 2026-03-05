from sqlalchemy.ext.asyncio import AsyncSession
from app.schools import schemas, repository
from app.schools.models import School, SchoolConfiguration, SchoolLevel
from app.auth.models import User
from app.core.enums import UserRole, AcademicLevel
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    SchoolAlreadyExistsException,
    ConflictException,
)

import uuid
from typing import List, Dict, Any


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

    Root-cause fix: the original code built response dicts that omitted
    academic_levels entirely. The frontend was always receiving [] for every
    school, so SchoolLevelsModal had nothing to pre-tick and the levels column
    would always be empty.
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenException("Only Super Admins can view the full school directory.")

    rows = await repository.get_all_schools_with_counts(db)

    # Unpack the SQLAlchemy Row tuples (School, student_count) into a format
    # Pydantic can serialise. academic_levels is now included because the
    # repository eagerly loads it with selectinload().
    result = []
    for school, student_count in rows:
        result.append({
            "id": school.id,
            "name": school.name,
            "email": school.email,
            "phone": school.phone,
            "address": school.address,
            "is_active": school.is_active,
            "academic_levels": [{"level": sl.level} for sl in school.academic_levels],
            "student_count": student_count,
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

    # Re-fetch so academic_levels is eagerly loaded for the response
    return await repository.get_school_by_id(db, school_id)


async def update_school_levels(
    db: AsyncSession,
    school_id: uuid.UUID,
    level_in: schemas.SchoolLevelUpdate,
    current_user: User,
) -> School:
    """
    Replaces the academic levels of a school.

    Only SUPER_ADMINs can call this — school-level changes are a platform-wide
    decision (e.g., a nursery expanding to include primary education).

    Safety rules:
    - Cannot remove a level that still has classes assigned to it.
      The admin must delete those classes first to prevent orphaned curriculum data.
    - Duplicate levels in the input list are silently de-duplicated.
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenException("Only Super Admins can modify a school's academic levels.")

    school = await repository.get_school_by_id(db, school_id)
    if not school:
        raise NotFoundException("School not found.")

    # De-duplicate the incoming list while preserving order
    new_levels: List[AcademicLevel] = list(dict.fromkeys(level_in.academic_levels))

    # Determine which levels are being REMOVED by comparing against current levels
    current_level_values = {sl.level for sl in school.academic_levels}
    new_level_values     = set(new_levels)
    levels_being_removed = list(current_level_values - new_level_values)

    # --- Safety check: block removal if classes exist at those levels ---
    if levels_being_removed:
        orphaned_class_count = await repository.get_classes_at_removed_levels(
            db, school_id, levels_being_removed
        )
        if orphaned_class_count > 0:
            raise ConflictException(
                code="CLASSES_EXIST_AT_REMOVED_LEVEL",
                message=(
                    f"Cannot remove level(s) {[l.value for l in levels_being_removed]} "
                    f"because {orphaned_class_count} class(es) are still assigned to them. "
                    "Please delete those classes first."
                ),
            )

    # --- Atomic replace ---
    await repository.replace_school_levels(db, school_id, new_levels)

    # Re-fetch so the response reflects the new state with levels eagerly loaded
    return await repository.get_school_by_id(db, school_id)


async def get_active_settings(db: AsyncSession, current_user: User) -> SchoolConfiguration:
    """Any authenticated user in the school can view settings (needed for dashboards)."""
    return await repository.get_school_config(db, current_user.school_id)


async def update_settings(
    db: AsyncSession,
    config_in: schemas.SchoolConfigUpdate,
    current_user: User
) -> SchoolConfiguration:
    """Only School Admins can change configuration."""
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can modify system configurations.")

    config = await repository.get_school_config(db, current_user.school_id)
    update_data = config_in.model_dump(exclude_unset=True)

    return await repository.update_school_config_transaction(db, config, update_data)