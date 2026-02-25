from datetime import date
import uuid
from pydantic import BaseModel, ConfigDict
from app.core.enums import AttendanceStatus

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