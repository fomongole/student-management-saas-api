import uuid
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.exams.models import Exam, Result
from app.exams import schemas
from sqlalchemy.orm import joinedload
from app.students.models import Student
from app.auth.models import User
from typing import Sequence

async def get_exam_by_details(
    db: AsyncSession, school_id: uuid.UUID, name: str, year: int, term: int, subject_id: uuid.UUID
) -> Exam | None:
    """Checks if an identical exam already exists to prevent 500 DB crashes."""
    query = select(Exam).where(
        and_(
            Exam.school_id == school_id,
            Exam.name == name,
            Exam.year == year,
            Exam.term == term,
            Exam.subject_id == subject_id
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_exam(db: AsyncSession, exam_in: schemas.ExamCreate, school_id: uuid.UUID) -> Exam:
    """Persists a new exam session record."""
    new_exam = Exam(**exam_in.model_dump(), school_id=school_id)
    db.add(new_exam)
    await db.commit()
    await db.refresh(new_exam)
    return new_exam

async def get_exam_by_id(db: AsyncSession, exam_id: uuid.UUID, school_id: uuid.UUID) -> Exam | None:
    """Fetches exam metadata while enforcing school isolation."""
    query = select(Exam).where(and_(Exam.id == exam_id, Exam.school_id == school_id))
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def sync_results(
    db: AsyncSession, 
    exam_id: uuid.UUID, 
    results_in: list[schemas.StudentMarkIn], 
    school_id: uuid.UUID
) -> list[Result]:
    """
    Enterprise Upsert Logic:
    Updates existing scores or inserts new ones to prevent database duplication errors.
    """
    student_ids = [r.student_id for r in results_in]
    
    # Check for existing results to determine Update vs Insert
    query = select(Result).where(
        and_(Result.exam_id == exam_id, Result.student_id.in_(student_ids))
    )
    existing = await db.execute(query)
    existing_map = {res.student_id: res for res in existing.scalars().all()}
    
    final_records = []
    for res in results_in:
        if res.student_id in existing_map:
            record = existing_map[res.student_id]
            record.score = res.score
            record.teacher_comment = res.teacher_comment
        else:
            record = Result(
                exam_id=exam_id,
                student_id=res.student_id,
                score=res.score,
                teacher_comment=res.teacher_comment,
                school_id=school_id
            )
            db.add(record)
        final_records.append(record)
        
    await db.flush()
    await db.commit()
    return final_records

async def get_all_exams(
    db: AsyncSession, 
    school_id: uuid.UUID, 
    year: int | None = None, 
    term: int | None = None,
    subject_id: uuid.UUID | None = None
) -> Sequence[Exam]:
    """Fetches exam sessions with optional filtering for frontend dropdowns."""
    query = select(Exam).where(Exam.school_id == school_id).order_by(Exam.year.desc(), Exam.term.desc(), Exam.name)
    
    if year:
        query = query.where(Exam.year == year)
    if term:
        query = query.where(Exam.term == term)
    if subject_id:
        query = query.where(Exam.subject_id == subject_id)
        
    result = await db.execute(query)
    return result.scalars().all()

async def get_class_mark_sheet(
    db: AsyncSession,
    exam_id: uuid.UUID,
    class_id: uuid.UUID,
    school_id: uuid.UUID
) -> list[tuple[Student, Result | None]]:
    """
    Returns ALL students in a class, joined with their exam score (if it exists).
    Prevents N+1 queries by eager loading the User profile.
    """
    # Join condition for Results
    result_conditions = and_(
        Result.student_id == Student.id,
        Result.exam_id == exam_id,
        Result.school_id == school_id
    )

    query = (
        select(Student, Result)
        .join(Student.user)
        .options(joinedload(Student.user))
        .outerjoin(Result, result_conditions)
        .where(
            and_(Student.class_id == class_id, Student.school_id == school_id)
        )
        .order_by(User.last_name, User.first_name)
    )
    
    result = await db.execute(query)
    return list(result.all())