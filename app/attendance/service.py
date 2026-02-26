from datetime import date
import uuid

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.attendance import schemas, repository
from app.auth.models import User
from app.core.enums import UserRole
from app.notifications.service import dispatch_alert
from app.notifications.models import NotificationType
from app.core.exceptions import (
    ForbiddenException,
    ConflictException,
)


async def mark_bulk_attendance(
    db: AsyncSession,
    data: schemas.AttendanceBulkCreate,
    current_user: User,
    background_tasks: BackgroundTasks,
) -> list:
    """
    Records bulk attendance entries with automated alert triggers.

    Policy:
    - Only SCHOOL_ADMIN or TEACHER may manage attendance.
    - Students must belong to the specified class and school.
    - Alerts triggered for ABSENT and LATE statuses (preventing duplicates).
    """

    if current_user.role not in (UserRole.SCHOOL_ADMIN, UserRole.TEACHER):
        raise ForbiddenException("Unauthorized to manage attendance.")

    student_ids = [r.student_id for r in data.records]

    is_valid = await repository.validate_students_in_class(
        db,
        student_ids,
        data.class_id,
        current_user.school_id,
    )

    if not is_valid:
        raise ConflictException(
            code="INVALID_ATTENDANCE_STUDENT_SET",
            message="One or more students are invalid for the selected class/school.",
        )

    synced_records, alerts_to_trigger = await repository.sync_attendance_records(
        db=db,
        class_id=data.class_id,
        subject_id=data.subject_id,
        attendance_date=data.attendance_date,
        records=data.records,
        school_id=current_user.school_id,
    )

    if alerts_to_trigger:
        # Only fetch user mappings if we actually have messages to send
        user_map = await repository.get_student_user_mapping(db, student_ids)

        for record in alerts_to_trigger:
            target_user_id = user_map.get(record.student_id)

            if target_user_id:
                remarks_text = f" Reason: {record.remarks}" if record.remarks else ""

                alert_message = (
                    f"ATTENDANCE ALERT: Student marked "
                    f"{record.status.value} for "
                    f"{data.attendance_date}.{remarks_text}"
                )

                await dispatch_alert(
                    db=db,
                    background_tasks=background_tasks,
                    recipient_id=target_user_id,
                    title=f"Student {record.status.value} Notice",
                    message=alert_message,
                    type=NotificationType.SMS,
                    school_id=current_user.school_id,
                )

    return synced_records

from typing import List

async def get_student_attendance_history(
    db: AsyncSession,
    student_id: uuid.UUID,
    current_user: User,
    start_date: date | None,
    end_date: date | None
) -> List[schemas.StudentAttendanceDetail]:
    
    # Optional: Add RBAC here. For example, a PARENT should only see their own child's history.
    if current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.TEACHER, UserRole.STUDENT, UserRole.PARENT]:
         raise ForbiddenException("Unauthorized.")
         
    # If the user is a STUDENT, ensure they are only requesting their own ID (logic omitted for brevity, but crucial for production)

    history = await repository.get_student_history(
        db, student_id, current_user.school_id, start_date, end_date
    )
    return history

async def get_daily_class_roll_call(
    db: AsyncSession,
    class_id: uuid.UUID,
    target_date: date,
    subject_id: uuid.UUID | None,
    current_user: User
) -> List[schemas.ClassDailyAttendanceResponse]:
    
    if current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.TEACHER]:
        raise ForbiddenException("Only staff can view class roll calls.")
        
    records = await repository.get_class_attendance_for_date(
        db, class_id, current_user.school_id, target_date, subject_id
    )
    
    formatted_response = []
    for student, attendance_record in records:
        formatted_response.append(schemas.ClassDailyAttendanceResponse(
            student_id=student.id,
            first_name=student.user.first_name,
            last_name=student.user.last_name,
            admission_number=student.admission_number,
            status=attendance_record.status if attendance_record else None,
            remarks=attendance_record.remarks if attendance_record else None
        ))
        
    return formatted_response