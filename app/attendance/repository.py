from datetime import date
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.attendance.models import Attendance
from app.attendance.schemas import StudentAttendanceIn
from app.students.models import Student
from app.core.enums import AttendanceStatus


from sqlalchemy.orm import joinedload
from app.auth.models import User


async def validate_students_in_class(
    db: AsyncSession, 
    student_ids: list[uuid.UUID], 
    class_id: uuid.UUID, 
    school_id: uuid.UUID
) -> bool:
    query = select(func.count(Student.id)).where(
        and_(
            Student.id.in_(student_ids),
            Student.class_id == class_id,
            Student.school_id == school_id
        )
    )
    result = await db.execute(query)
    found_count = result.scalar()
    return found_count == len(student_ids)

async def get_student_user_mapping(db: AsyncSession, student_ids: list[uuid.UUID]) -> dict:
    query = select(Student.id, Student.user_id).where(Student.id.in_(student_ids))
    result = await db.execute(query)
    return {row.id: row.user_id for row in result.all() if row.user_id}

async def sync_attendance_records(
    db: AsyncSession, 
    class_id: uuid.UUID, 
    subject_id: uuid.UUID | None, 
    attendance_date: date,
    records: list[StudentAttendanceIn],
    school_id: uuid.UUID
) -> tuple[list[Attendance], list[StudentAttendanceIn]]:
    """
    Performs an Upsert (Update or Insert). 
    Returns a tuple: (Final Database Records, List of records that need SMS alerts)
    """
    student_ids = [r.student_id for r in records]
    
    query = select(Attendance).where(
        and_(
            Attendance.student_id.in_(student_ids),
            Attendance.attendance_date == attendance_date,
            Attendance.subject_id == subject_id,
            Attendance.school_id == school_id
        )
    )
    result = await db.execute(query)
    existing_map = {res.student_id: res for res in result.scalars().all()}
    
    final_records = []
    alerts_to_trigger = []
    
    for rec in records:
        if rec.student_id in existing_map:
            existing_record = existing_map[rec.student_id]
            
            # Anti-Spam Check: Only trigger alert if status CHANGED to Absent/Late
            if existing_record.status != rec.status and rec.status in (AttendanceStatus.ABSENT, AttendanceStatus.LATE):
                alerts_to_trigger.append(rec)
                
            existing_record.status = rec.status
            existing_record.remarks = rec.remarks
            final_records.append(existing_record)
        else:
            new_entry = Attendance(
                student_id=rec.student_id,
                class_id=class_id,
                subject_id=subject_id,
                attendance_date=attendance_date,
                status=rec.status,
                remarks=rec.remarks,
                school_id=school_id
            )
            db.add(new_entry)
            final_records.append(new_entry)
            
            # Brand new record: Trigger alert if Absent/Late
            if rec.status in (AttendanceStatus.ABSENT, AttendanceStatus.LATE):
                alerts_to_trigger.append(rec)
    
    await db.flush() 
    await db.commit()
        
    return final_records, alerts_to_trigger

async def get_student_history(
    db: AsyncSession, 
    student_id: uuid.UUID, 
    school_id: uuid.UUID,
    start_date: date | None = None,
    end_date: date | None = None
) -> list[Attendance]:
    """Fetches a student's attendance history, optionally filtered by a date range."""
    query = select(Attendance).where(
        and_(Attendance.student_id == student_id, Attendance.school_id == school_id)
    ).order_by(Attendance.attendance_date.desc())
    
    if start_date:
        query = query.where(Attendance.attendance_date >= start_date)
    if end_date:
        query = query.where(Attendance.attendance_date <= end_date)
        
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_class_attendance_for_date(
    db: AsyncSession,
    class_id: uuid.UUID,
    school_id: uuid.UUID,
    target_date: date,
    subject_id: uuid.UUID | None = None
) -> list[tuple[Student, Attendance | None]]:
    """
    The 'Roll Call' Query: Returns ALL students in a class, joined with their 
    attendance record for the specific date (if it exists).
    """
    attendance_conditions = [
        Attendance.student_id == Student.id,
        Attendance.attendance_date == target_date,
        Attendance.school_id == school_id
    ]
    
    # If subject_id is provided, match exactly. If None, ensure we only join on daily (None) records.
    if subject_id:
        attendance_conditions.append(Attendance.subject_id == subject_id)
    else:
         attendance_conditions.append(Attendance.subject_id.is_(None))

    query = (
        select(Student, Attendance)
        .join(Student.user)
        .options(joinedload(Student.user))
        .outerjoin(Attendance, and_(*attendance_conditions))
        .where(
            and_(Student.class_id == class_id, Student.school_id == school_id)
        )
        .order_by(User.last_name, User.first_name)
    )
    
    result = await db.execute(query)
    return list(result.all())