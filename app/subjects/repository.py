import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from app.subjects.models import Subject, TeacherSubject
from app.subjects.schemas import SubjectCreate
from app.teachers.models import Teacher
from app.core.enums import AcademicLevel

# --- READ OPERATIONS ---

async def get_subject_by_code_and_level(
    db: AsyncSession, 
    school_id: uuid.UUID, 
    code: str, 
    level: AcademicLevel
) -> Subject | None:
    """SQL logic to find a subject by code and level within a tenant."""
    query = select(Subject).where(
        and_(
            Subject.school_id == school_id, 
            Subject.code == code,
            Subject.level == level
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_teacher_by_id_and_school(
    db: AsyncSession, 
    teacher_id: uuid.UUID, 
    school_id: uuid.UUID
) -> Teacher | None:
    """SQL logic to verify a teacher exists and belongs to the school."""
    query = select(Teacher).where(
        and_(Teacher.id == teacher_id, Teacher.school_id == school_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_subjects_by_ids_and_school(
    db: AsyncSession, 
    subject_ids: list[uuid.UUID], 
    school_id: uuid.UUID
) -> list[Subject]:
    """SQL logic to fetch multiple subjects only if they belong to the tenant."""
    query = select(Subject).where(
        and_(Subject.id.in_(subject_ids), Subject.school_id == school_id)
    )
    result = await db.execute(query)
    return result.scalars().all()

# --- WRITE OPERATIONS ---

async def create_subject(db: AsyncSession, subject_in: SubjectCreate, school_id: uuid.UUID) -> Subject:
    """Saves a new subject to the database."""
    new_subject = Subject(
        name=subject_in.name,
        code=subject_in.code,
        level=subject_in.level,
        is_core=subject_in.is_core,
        school_id=school_id
    )
    db.add(new_subject)
    await db.commit()
    await db.refresh(new_subject)
    return new_subject

async def assign_subjects_to_teacher(
    db: AsyncSession, 
    teacher_id: uuid.UUID, 
    subject_ids: list[uuid.UUID],
    school_id: uuid.UUID
) -> list[TeacherSubject]:
    """Bulk inserts the bridge records for many-to-many assignment safely."""
    
    # 1. Fetch existing assignments to prevent IntegrityError crashes
    existing_query = select(TeacherSubject.subject_id).where(
        and_(TeacherSubject.teacher_id == teacher_id, TeacherSubject.school_id == school_id)
    )
    existing_subjects = (await db.execute(existing_query)).scalars().all()
    
    assignments = []
    for s_id in subject_ids:
        # Only assign if they don't already teach it
        if s_id not in existing_subjects:
            assignment = TeacherSubject(
                teacher_id=teacher_id,
                subject_id=s_id,
                school_id=school_id
            )
            db.add(assignment)
            assignments.append(assignment)
    
    if assignments:
        await db.flush()
        await db.commit()
        
    return assignments