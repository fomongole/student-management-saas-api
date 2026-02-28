import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from app.subjects.models import Subject, TeacherSubject
from app.subjects.schemas import SubjectCreate
from app.teachers.models import Teacher
from app.core.enums import AcademicLevel

from typing import Sequence
from sqlalchemy.orm import joinedload, selectinload

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
    # 1. Atomic Create
    new_subject = Subject(
        name=subject_in.name,
        code=subject_in.code,
        level=subject_in.level,
        is_core=subject_in.is_core,
        school_id=school_id
    )
    db.add(new_subject)
    await db.flush() 
    
    if subject_in.teacher_id:
        assignment = TeacherSubject(
            teacher_id=subject_in.teacher_id,
            subject_id=new_subject.id,
            school_id=school_id
        )
        db.add(assignment)
    
    await db.commit()

    # 2. Explicitly load the relationship graph
    # This prevents the 500 error during serialization
    query = (
        select(Subject)
        .where(Subject.id == new_subject.id)
        .options(
            # Eager load teachers AND their user profiles in one go
            selectinload(Subject.assigned_teachers).joinedload(Teacher.user)
        )
    )
    result = await db.execute(query)
    return result.scalar_one()

async def assign_subjects_to_teacher(
    db: AsyncSession, 
    teacher_id: uuid.UUID, 
    subject_ids: list[uuid.UUID],
    school_id: uuid.UUID
) -> list[TeacherSubject]:
    """Synchronizes the teacher's subject assignments (adds new, removes unchecked)."""
    
    # 1. Fetch existing assignments AS FULL OBJECTS so we can delete them
    existing_query = select(TeacherSubject).where(
        and_(TeacherSubject.teacher_id == teacher_id, TeacherSubject.school_id == school_id)
    )
    existing_records = (await db.execute(existing_query)).scalars().all()
    
    # Create sets for easy math comparisons
    existing_subject_ids = {record.subject_id for record in existing_records}
    requested_subject_ids = set(subject_ids)
    
    # 2. DELETE subjects that were unchecked in the frontend
    ids_to_remove = existing_subject_ids - requested_subject_ids
    for record in existing_records:
        if record.subject_id in ids_to_remove:
            await db.delete(record)
            
    # 3. ADD new subjects that were freshly checked
    ids_to_add = requested_subject_ids - existing_subject_ids
    for s_id in ids_to_add:
        new_assignment = TeacherSubject(
            teacher_id=teacher_id,
            subject_id=s_id,
            school_id=school_id
        )
        db.add(new_assignment)
    
    # 4. Commit the transaction if anything changed
    if ids_to_remove or ids_to_add:
        await db.commit()
        
    # 5. Return the fresh list of assignments
    updated_query = select(TeacherSubject).where(
        and_(TeacherSubject.teacher_id == teacher_id, TeacherSubject.school_id == school_id)
    )
    return list((await db.execute(updated_query)).scalars().all())

async def get_all_subjects(db: AsyncSession, school_id: uuid.UUID, level: AcademicLevel | None = None) -> Sequence[Subject]:
    query = (
        select(Subject)
        .where(Subject.school_id == school_id)
        # Eager load teachers and their underlying user names
        .options(selectinload(Subject.assigned_teachers).joinedload(Teacher.user)) 
        .order_by(Subject.level, Subject.name)
    )
    if level:
        query = query.where(Subject.level == level)
        
    result = await db.execute(query)
    return result.scalars().all()

async def get_subject_by_id(db: AsyncSession, subject_id: uuid.UUID, school_id: uuid.UUID) -> Subject | None:
    """Fetches a single subject strictly within the tenant."""
    query = select(Subject).where(and_(Subject.id == subject_id, Subject.school_id == school_id))
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_teacher_assignments(
    db: AsyncSession, 
    teacher_id: uuid.UUID, 
    school_id: uuid.UUID
) -> Sequence[TeacherSubject]:
    """Fetches bridge records and eager-loads the underlying Subject details."""
    query = select(TeacherSubject).options(joinedload(TeacherSubject.subject)).where(
        and_(TeacherSubject.teacher_id == teacher_id, TeacherSubject.school_id == school_id)
    )
    result = await db.execute(query)
    return result.scalars().all()

async def delete_subject(db: AsyncSession, subject: Subject) -> None:
    """Deletes a subject. Cascades will handle removing TeacherSubject bridge records."""
    await db.delete(subject)
    await db.commit()