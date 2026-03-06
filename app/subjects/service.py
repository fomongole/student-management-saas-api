import uuid
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.subjects import schemas
from app.subjects.models import Subject, TeacherSubject
from app.subjects import repository as subject_repo
from app.schools import repository as school_repo
from app.auth.models import User
from app.core.enums import AcademicLevel, UserRole
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    ConflictException,
)

async def create_new_subject(
    db: AsyncSession,
    subject_in: schemas.SubjectCreate,
    current_user: User,
) -> Subject:
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Unauthorized.")

    # Verify school is licensed for this level
    school = await school_repo.get_school_by_id(db, current_user.school_id)
    registered_levels = [sl.level for sl in school.academic_levels]
    if subject_in.level not in registered_levels:
        raise ConflictException("LEVEL_NOT_REGISTERED", f"Your school is not registered for the {subject_in.level.value} level.")

    existing = await subject_repo.get_subject_by_code_and_level(
        db, current_user.school_id, subject_in.code, subject_in.level,
    )
    if existing:
        raise ConflictException("SUBJECT_ALREADY_EXISTS", "Subject code already exists for this level.")

    return await subject_repo.create_subject(db, subject_in, current_user.school_id)

async def assign_teacher_curriculum(db: AsyncSession, assignment_in: schemas.SubjectAssignment, current_user: User) -> list[TeacherSubject]:
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can assign subjects.")
    
    teacher = await subject_repo.get_teacher_by_id_and_school(db, assignment_in.teacher_id, current_user.school_id)
    if not teacher:
        raise NotFoundException("Teacher not found in your school.")
        
    found_subjects = await subject_repo.get_subjects_by_ids_and_school(db, assignment_in.subject_ids, current_user.school_id)
    if len(found_subjects) != len(assignment_in.subject_ids):
        raise ConflictException("INVALID_SUBJECT_SELECTION", "One or more subjects are invalid.")
        
    return await subject_repo.assign_subjects_to_teacher(db, assignment_in.teacher_id, assignment_in.subject_ids, current_user.school_id)
    
async def list_school_subjects(db: AsyncSession, current_user: User, level: AcademicLevel | None) -> Sequence[Subject]:
    if current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.TEACHER]:
        raise ForbiddenException("Unauthorized to view curriculum.")
    return await subject_repo.get_all_subjects(db, current_user.school_id, level)

async def get_assigned_subjects_for_teacher(db: AsyncSession, teacher_id: uuid.UUID, current_user: User) -> Sequence[TeacherSubject]:
    if current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.TEACHER]:
        raise ForbiddenException("Unauthorized to view assignments.")
    return await subject_repo.get_teacher_assignments(db, teacher_id, current_user.school_id)

async def update_subject_details(
    db: AsyncSession, 
    subject_id: uuid.UUID, 
    subject_in: schemas.SubjectUpdate, 
    current_user: User
) -> Subject:
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can update subjects.")
        
    subject = await subject_repo.get_subject_by_id(db, subject_id, current_user.school_id)
    if not subject:
        raise NotFoundException("Subject not found.")
        
    update_data = subject_in.model_dump(exclude_unset=True)
    
    new_level = update_data.get("level", subject.level)
    new_code = update_data.get("code", subject.code)

    # 1. SECURITY LOCK: Check Level Registration if level changed
    if new_level != subject.level:
        school = await school_repo.get_school_by_id(db, current_user.school_id)
        registered_levels = [sl.level for sl in school.academic_levels]
        if new_level not in registered_levels:
            raise ConflictException("LEVEL_NOT_REGISTERED", f"School is not registered for {new_level.value}.")

    # 2. Duplicate check on update to prevent 500 DB Integrity Errors
    if new_code != subject.code or new_level != subject.level:
        existing = await subject_repo.get_subject_by_code_and_level(
            db, current_user.school_id, new_code, new_level
        )
        if existing and existing.id != subject.id:
            raise ConflictException(
                "SUBJECT_ALREADY_EXISTS", 
                f"A subject with code '{new_code}' already exists for the {new_level.value} level."
            )

    for field, value in update_data.items():
        setattr(subject, field, value)
        
    db.add(subject)
    await db.commit()
    return await subject_repo.get_subject_by_id(db, subject.id, current_user.school_id)

async def remove_subject(db: AsyncSession, subject_id: uuid.UUID, current_user: User) -> None:
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can delete subjects.")
    deleted = await subject_repo.delete_subject_direct(db, subject_id, current_user.school_id)
    if not deleted:
        raise NotFoundException("Subject not found.")