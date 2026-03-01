import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, delete
from sqlalchemy.exc import IntegrityError

from app.subjects.models import Subject, TeacherSubject
from app.subjects.schemas import SubjectCreate
from app.teachers.models import Teacher
from app.core.enums import AcademicLevel
from app.core.exceptions import ConflictException

from typing import Sequence
from sqlalchemy.orm import joinedload, selectinload

# --- READ OPERATIONS ---

async def get_subject_by_code_and_level(
    db: AsyncSession, 
    school_id: uuid.UUID, 
    code: str, 
    level: AcademicLevel
) -> Subject | None:
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
    query = select(Subject).where(
        and_(Subject.id.in_(subject_ids), Subject.school_id == school_id)
    )
    result = await db.execute(query)
    return result.scalars().all()

# --- WRITE OPERATIONS ---

async def create_subject(db: AsyncSession, subject_in: SubjectCreate, school_id: uuid.UUID) -> Subject:
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

    # Re-fetch to load relationships
    return await get_subject_by_id(db, new_subject.id, school_id)

async def assign_subjects_to_teacher(
    db: AsyncSession, 
    teacher_id: uuid.UUID, 
    subject_ids: list[uuid.UUID],
    school_id: uuid.UUID
) -> list[TeacherSubject]:
    
    existing_query = select(TeacherSubject).where(
        and_(TeacherSubject.teacher_id == teacher_id, TeacherSubject.school_id == school_id)
    )
    existing_records = (await db.execute(existing_query)).scalars().all()
    
    existing_subject_ids = {record.subject_id for record in existing_records}
    requested_subject_ids = set(subject_ids)
    
    ids_to_remove = existing_subject_ids - requested_subject_ids
    for record in existing_records:
        if record.subject_id in ids_to_remove:
            await db.delete(record)
            
    ids_to_add = requested_subject_ids - existing_subject_ids
    for s_id in ids_to_add:
        new_assignment = TeacherSubject(
            teacher_id=teacher_id,
            subject_id=s_id,
            school_id=school_id
        )
        db.add(new_assignment)
    
    if ids_to_remove or ids_to_add:
        await db.commit()
        
    updated_query = select(TeacherSubject).where(
        and_(TeacherSubject.teacher_id == teacher_id, TeacherSubject.school_id == school_id)
    )
    return list((await db.execute(updated_query)).scalars().all())

async def get_all_subjects(db: AsyncSession, school_id: uuid.UUID, level: AcademicLevel | None = None) -> Sequence[Subject]:
    query = (
        select(Subject)
        .where(Subject.school_id == school_id)
        .options(selectinload(Subject.assigned_teachers).joinedload(Teacher.user)) 
        .order_by(Subject.level, Subject.name)
    )
    if level:
        query = query.where(Subject.level == level)
        
    result = await db.execute(query)
    return result.scalars().all()

async def get_subject_by_id(db: AsyncSession, subject_id: uuid.UUID, school_id: uuid.UUID) -> Subject | None:
    """
    Fetches a single subject strictly within the tenant.
    Eagerly loads teachers to prevent 500 errors on edit serialization!
    """
    query = (
        select(Subject)
        .where(and_(Subject.id == subject_id, Subject.school_id == school_id))
        .options(selectinload(Subject.assigned_teachers).joinedload(Teacher.user))
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_teacher_assignments(
    db: AsyncSession, 
    teacher_id: uuid.UUID, 
    school_id: uuid.UUID
) -> Sequence[TeacherSubject]:
    query = select(TeacherSubject).options(joinedload(TeacherSubject.subject)).where(
        and_(TeacherSubject.teacher_id == teacher_id, TeacherSubject.school_id == school_id)
    )
    result = await db.execute(query)
    return result.scalars().all()

# Safe, direct deletion
async def delete_subject_direct(db: AsyncSession, subject_id: uuid.UUID, school_id: uuid.UUID) -> bool:
    stmt = delete(Subject).where(and_(Subject.id == subject_id, Subject.school_id == school_id))
    try:
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
    except IntegrityError:
        await db.rollback()
        raise ConflictException(
            code="SUBJECT_IN_USE",
            message="Cannot delete this subject because it has been assigned to an exam session."
        )