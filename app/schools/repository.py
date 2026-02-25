import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.schools.models import School
from app.schools.schemas import SchoolCreate
from app.auth.models import User
from app.students.models import Student

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