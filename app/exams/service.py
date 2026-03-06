from typing import List, Sequence
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.exams import repository, schemas
from app.attendance import repository as att_repo
from app.auth.models import User
from app.core.enums import UserRole
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    ConflictException,
)
from app.exams.models import Exam


async def create_new_exam(
    db: AsyncSession,
    exam_in: schemas.ExamCreate,
    current_user: User,
):
    """
    Creates a new exam session.

    Policy:
    - Only SCHOOL_ADMIN or TEACHER may create exam sessions.
    - Exam must be scoped to requester's school.
    - Prevent exact duplicates.
    """

    if current_user.role not in (UserRole.SCHOOL_ADMIN, UserRole.TEACHER):
        raise ForbiddenException("Unauthorized.")

    # Checking for duplicates
    existing_exam = await repository.get_exam_by_details(
        db,
        current_user.school_id,
        exam_in.name,
        exam_in.year,
        exam_in.term,
        exam_in.subject_id
    )

    if existing_exam:
        raise ConflictException(
            code="EXAM_ALREADY_EXISTS",
            message="An exam with this name, term, year, and subject already exists."
        )

    return await repository.create_exam(
        db,
        exam_in,
        current_user.school_id,
    )


async def submit_marks(
    db: AsyncSession,
    data: schemas.BulkResultSubmit,
    current_user: User,
):
    """
    Bulk submission of student results.

    Business Rules:
    - Only SCHOOL_ADMIN or TEACHER may submit marks.
    - Exam must belong to requester's school.
    - All students must belong to specified class and school.
    """

    # Permission check
    if current_user.role not in (UserRole.SCHOOL_ADMIN, UserRole.TEACHER):
        raise ForbiddenException("Unauthorized.")

    # Validate exam ownership
    exam = await repository.get_exam_by_id(
        db,
        data.exam_id,
        current_user.school_id,
    )

    if not exam:
        raise NotFoundException("Exam session not found.")

    # Validate students belong to class + school
    student_ids = [r.student_id for r in data.results]

    is_valid_group = await att_repo.validate_students_in_class(
        db,
        student_ids,
        data.class_id,
        current_user.school_id,
    )

    if not is_valid_group:
        raise ConflictException(
            code="INVALID_STUDENT_CLASS_MAPPING",
            message="One or more students do not belong to the specified class/school.",
        )

    return await repository.sync_results(
        db,
        data.exam_id,
        data.results,
        current_user.school_id,
    )

async def list_exam_sessions(
    db: AsyncSession,
    current_user: User,
    year: int | None,
    term: int | None,
    subject_id: uuid.UUID | None
) -> Sequence[Exam]:
    if current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.TEACHER]:
        raise ForbiddenException("Unauthorized.")
        
    return await repository.get_all_exams(db, current_user.school_id, year, term, subject_id)

async def generate_mark_sheet(
    db: AsyncSession,
    exam_id: uuid.UUID,
    class_id: uuid.UUID,
    current_user: User
) -> List[schemas.StudentMarkSheetDetail]:
    
    if current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.TEACHER]:
        raise ForbiddenException("Only staff can view class mark sheets.")
        
    # Ensure exam actually exists and belongs to the school
    exam = await repository.get_exam_by_id(db, exam_id, current_user.school_id)
    if not exam:
        raise NotFoundException("Exam session not found.")
        
    records = await repository.get_class_mark_sheet(
        db, exam_id, class_id, current_user.school_id
    )
    
    formatted_sheet = []
    for student, result in records:
        formatted_sheet.append(schemas.StudentMarkSheetDetail(
            student_id=student.id,
            first_name=student.user.first_name,
            last_name=student.user.last_name,
            admission_number=student.admission_number,
            score=result.score if result else None,
            teacher_comment=result.teacher_comment if result else None
        ))
        
    return formatted_sheet

async def update_exam_details(
    db: AsyncSession, exam_id: uuid.UUID, exam_in: schemas.ExamUpdate, current_user: User
):
    if current_user.role not in (UserRole.SCHOOL_ADMIN, UserRole.TEACHER):
        raise ForbiddenException("Unauthorized.")

    exam = await repository.get_exam_by_id(db, exam_id, current_user.school_id)
    if not exam:
        raise NotFoundException("Exam session not found.")

    update_data = exam_in.model_dump(exclude_unset=True)

    # Check duplicates if core fields change
    name = update_data.get("name", exam.name)
    year = update_data.get("year", exam.year)
    term = update_data.get("term", exam.term)
    subject_id = update_data.get("subject_id", exam.subject_id)

    existing = await repository.get_exam_by_details(
        db, current_user.school_id, name, year, term, subject_id
    )
    if existing and existing.id != exam.id:
        raise ConflictException("EXAM_ALREADY_EXISTS", "An identical exam session already exists.")

    return await repository.update_exam(db, exam, update_data)

async def remove_exam_session(db: AsyncSession, exam_id: uuid.UUID, current_user: User):
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can delete exam sessions.")

    deleted = await repository.delete_exam_protected(db, exam_id, current_user.school_id)
    if not deleted:
        raise NotFoundException("Exam session not found.")