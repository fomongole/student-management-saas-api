from datetime import date
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.attendance.models import Attendance
from app.attendance.schemas import StudentAttendanceIn
from app.students.models import Student
from app.core.enums import AttendanceStatus

# --- READ OPERATIONS ---

async def validate_students_in_class(
    db: AsyncSession, 
    student_ids: list[uuid.UUID], 
    class_id: uuid.UUID, 
    school_id: uuid.UUID
) -> bool:
    # Using func.count() instead of pulling all rows into memory
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

# --- WRITE OPERATIONS (UPSERT) ---

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
    
    # Using flush() generates the UUIDs for new records instantly in memory.
    # This prevents the N+1 query problem of running await db.refresh() in a loop.
    await db.flush() 
    await db.commit()
        
    return final_records, alerts_to_trigger