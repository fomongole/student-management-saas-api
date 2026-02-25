from sqlalchemy.ext.asyncio import AsyncSession

from app.subjects import schemas
from app.subjects.models import Subject, TeacherSubject
from app.subjects import repository as subject_repo
from app.auth.models import User
from app.core.enums import UserRole
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
    """
    Creates a new subject within a school.

    Business Rules:
    - Only SCHOOL_ADMIN may create subjects
    - Subject code must be unique within level & school
    - Subject must belong to admin's school
    """

    # 1. RBAC enforcement
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Unauthorized.")

    # 2. Uniqueness check
    existing = await subject_repo.get_subject_by_code_and_level(
        db,
        current_user.school_id,
        subject_in.code,
        subject_in.level,
    )

    if existing:
        raise ConflictException(
            code="SUBJECT_ALREADY_EXISTS",
            message="Subject code already exists for this level.",
        )

    # 3. Persist
    return await subject_repo.create_subject(
        db,
        subject_in,
        current_user.school_id,
    )

async def assign_teacher_curriculum(
    db: AsyncSession,
    assignment_in: schemas.SubjectAssignment,
    current_user: User,
) -> list[TeacherSubject]:
    """
    Assigns multiple subjects to a teacher.

    Business Rules:
    - Only SCHOOL_ADMIN may assign subjects
    - Teacher must belong to the requesting admin's school
    - All subjects must belong to same school
    - Assignment executed transactionally
    """

    # 1. Missing RBAC enforcement FIXED
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can assign subjects.")

    # 2. Validate teacher ownership
    teacher = await subject_repo.get_teacher_by_id_and_school(
        db,
        assignment_in.teacher_id,
        current_user.school_id,
    )

    if not teacher:
        raise NotFoundException(
            "Teacher not found in your school."
        )

    # 3. Validate subject ownership
    found_subjects = await subject_repo.get_subjects_by_ids_and_school(
        db,
        assignment_in.subject_ids,
        current_user.school_id,
    )

    if len(found_subjects) != len(assignment_in.subject_ids):
        raise ConflictException(
            code="INVALID_SUBJECT_SELECTION",
            message="One or more subjects are invalid or belong to another school.",
        )

    # 4. Persist assignments
    return await subject_repo.assign_subjects_to_teacher(
        db,
        assignment_in.teacher_id,
        assignment_in.subject_ids,
        current_user.school_id,
    )