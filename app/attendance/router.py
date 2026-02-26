from datetime import date
import uuid

from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.attendance import schemas, service

from fastapi import Query

router = APIRouter()

@router.post("/", response_model=list[schemas.AttendanceResponse], status_code=status.HTTP_201_CREATED)
async def submit_attendance(
    data: schemas.AttendanceBulkCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marks attendance for a list of students and triggers alerts for absences."""
    return await service.mark_bulk_attendance(db, data, current_user, background_tasks)

@router.get("/class/{class_id}", response_model=list[schemas.ClassDailyAttendanceResponse])
async def get_class_roll_call(
    class_id: uuid.UUID,
    target_date: date = Query(..., description="The date for the roll call"),
    subject_id: uuid.UUID | None = Query(None, description="Optional: specific subject"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetches the roll call sheet for a specific class and date. 
    Returns all students in the class and their current attendance status (if marked).
    """
    return await service.get_daily_class_roll_call(db, class_id, target_date, subject_id, current_user)

@router.get("/student/{student_id}", response_model=list[schemas.StudentAttendanceDetail])
async def get_student_history(
    student_id: uuid.UUID,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetches the attendance history for a single student."""
    return await service.get_student_attendance_history(db, student_id, current_user, start_date, end_date)