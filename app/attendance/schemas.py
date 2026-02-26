from datetime import date
import uuid
from pydantic import BaseModel, ConfigDict
from app.core.enums import AttendanceStatus
from typing import List, Optional

class StudentAttendanceIn(BaseModel):
    student_id: uuid.UUID
    status: AttendanceStatus
    remarks: str | None = None

class AttendanceBulkCreate(BaseModel):
    class_id: uuid.UUID
    subject_id: uuid.UUID | None = None
    attendance_date: date = date.today()
    records: list[StudentAttendanceIn]

class AttendanceResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    status: str
    attendance_date: date
    remarks: str | None = None
    
    model_config = ConfigDict(from_attributes=True)

class StudentAttendanceDetail(BaseModel):
    """Used when viewing a specific student's history."""
    id: uuid.UUID
    attendance_date: date
    status: AttendanceStatus
    subject_id: Optional[uuid.UUID] = None
    remarks: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ClassDailyAttendanceResponse(BaseModel):
    """Used to populate the teacher's roll-call screen."""
    student_id: uuid.UUID
    first_name: str
    last_name: str
    admission_number: str
    status: Optional[AttendanceStatus] = None # Will be None if not marked yet
    remarks: Optional[str] = None