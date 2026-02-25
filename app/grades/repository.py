import uuid
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.grades.models import GradingScale
from app.grades import schemas
from app.exams.models import Exam, Result
from app.students.models import Student

async def get_tier_by_symbol(db: AsyncSession, symbol: str, school_id: uuid.UUID) -> GradingScale | None:
    """SQL logic to find a specific grading tier by its symbol."""
    query = select(GradingScale).where(
        and_(GradingScale.grade_symbol == symbol, GradingScale.school_id == school_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_all_grading_tiers(db: AsyncSession, school_id: uuid.UUID) -> list[GradingScale]:
    """
    PERFORMANCE FIX: Fetches all grading tiers for a school into memory 
    to prevent N+1 DB queries during report card generation.
    """
    query = select(GradingScale).where(GradingScale.school_id == school_id)
    result = await db.execute(query)
    return list(result.scalars().all())

async def sync_grading_tier(db: AsyncSession, tier_in: schemas.GradingScaleCreate, school_id: uuid.UUID) -> GradingScale:
    """
    Enterprise Upsert Logic:
    1. Checks if the symbol (e.g., 'D2') already exists for this school.
    2. Updates existing values if found, otherwise creates a new record.
    """
    existing_tier = await get_tier_by_symbol(db, tier_in.grade_symbol, school_id)
    
    if existing_tier:
        # Update existing record logic
        for key, value in tier_in.model_dump().items():
            setattr(existing_tier, key, value)
        target_obj = existing_tier
    else:
        # Create new record logic
        target_obj = GradingScale(**tier_in.model_dump(), school_id=school_id)
        db.add(target_obj)
        
    await db.commit()
    await db.refresh(target_obj)
    return target_obj

async def get_student_report_data(
    db: AsyncSession, 
    student_id: uuid.UUID, 
    year: int, 
    term: int,
    school_id: uuid.UUID
) -> Student | None:
    """
    Production Fetcher: Pulls the student profile with all nested results,
    subject details, and class information in a single optimized query.
    """
    query = (
        select(Student)
        .options(
            joinedload(Student.user),                
            joinedload(Student.class_relationship),  
            joinedload(Student.results)              
            .joinedload(Result.exam)                 
            .joinedload(Exam.subject)                
        )
        .where(
            and_(
                Student.id == student_id,
                Student.school_id == school_id
            )
        )
    )
    
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()