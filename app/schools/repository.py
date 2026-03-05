import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, delete

from app.schools.models import School, SchoolConfiguration, SchoolLevel
from app.schools.schemas import SchoolCreate
from app.auth.models import User
from app.students.models import Student
from app.core.enums import AcademicLevel


async def get_school_by_email(db: AsyncSession, email: str) -> School | None:
    """Checks if a school with this email already exists."""
    # Filter out soft-deleted schools
    query = select(School).where(School.email == email, School.deleted_at.is_(None))
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_school_by_id(db: AsyncSession, school_id: uuid.UUID) -> School | None:
    """Fetches a school by its UUID."""
    query = select(School).where(School.id == school_id, School.deleted_at.is_(None))
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_school(db: AsyncSession, school_in: SchoolCreate) -> School:
    """Saves a new school to the database."""
    new_school = School(
        name=school_in.name,
        email=school_in.email,
        phone=school_in.phone,
        address=school_in.address
    )
    db.add(new_school)
    await db.commit()
    await db.refresh(new_school)
    return new_school

async def get_platform_metrics(db: AsyncSession) -> dict:
    """
    Optimized SaaS-wide metrics.
    """
    # Only count non-deleted schools
    school_stats_query = select(
        func.count(School.id).label("total"),
        func.count(School.id).filter(School.is_active.is_(True)).label("active")
    ).where(School.deleted_at.is_(None))
    
    school_stats = (await db.execute(school_stats_query)).one()

    # Global User Count
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0

    return {
        "total_schools": school_stats.total,
        "active_schools": school_stats.active,
        "total_users": total_users
    }

async def get_all_schools_with_counts(db: AsyncSession) -> list:
    """
    The 'Money Query': Returns every school plus their current student counts.
    """
    query = (
        select(
            School,
            func.count(Student.id).label("student_count")
        )
        .outerjoin(Student, School.id == Student.school_id)
        .where(School.deleted_at.is_(None))
        .group_by(School.id)
    )
    result = await db.execute(query)
    return result.all()

async def get_school_config(db: AsyncSession, school_id: uuid.UUID) -> SchoolConfiguration:
    """Fetches school configuration or creates default if missing."""
    query = select(SchoolConfiguration).where(SchoolConfiguration.school_id == school_id)
    result = await db.execute(query)
    config = result.scalar_one_or_none()
    
    if not config:
        config = SchoolConfiguration(school_id=school_id)
        db.add(config)
        await db.commit()
        await db.refresh(config)
        
    return config

async def update_school_config_transaction(
    db: AsyncSession, 
    config: SchoolConfiguration, 
    update_data: dict
) -> SchoolConfiguration:
    """Strict repository-layer DB mutation."""
    for key, value in update_data.items():
        setattr(config, key, value)
    
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config

async def replace_school_levels(
    db: AsyncSession, 
    school_id: uuid.UUID, 
    new_levels: List[AcademicLevel]
) -> None:
    """
    Atomically replaces all academic levels for a school.

    Strategy: DELETE existing → INSERT new, all within one transaction.
    This is a hard replace (PUT semantics), not a diff-patch, which keeps 
    the logic simple, auditable, and race-condition-safe.

    WARNING: The service layer must validate that no existing class data would 
    be orphaned (e.g., classes at a level being removed) BEFORE calling this.
    """
    # 1. Wipe all current level entries for this school
    await db.execute(
        delete(SchoolLevel).where(SchoolLevel.school_id == school_id)
    )

    # 2. Insert the new level set
    for level in new_levels:
        db.add(SchoolLevel(school_id=school_id, level=level))

    await db.commit()

async def get_classes_at_removed_levels(
    db: AsyncSession,
    school_id: uuid.UUID,
    levels_being_removed: List[AcademicLevel],
) -> int:
    """
    Safety check: counts how many classes exist for levels about to be removed.
    Used by the service to block the update if data would be orphaned.
    """
    from app.classes.models import Class
    from sqlalchemy import func

    if not levels_being_removed:
        return 0

    query = select(func.count(Class.id)).where(
        Class.school_id == school_id,
        Class.level.in_(levels_being_removed),
    )
    result = await db.execute(query)
    return result.scalar() or 0