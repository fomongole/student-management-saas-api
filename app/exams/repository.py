import uuid
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.exams.models import Exam, Result
from app.exams import schemas

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