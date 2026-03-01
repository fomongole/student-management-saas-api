import uuid
from datetime import date
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from app.core.enums import EnrollmentStatus

class ParentBrief(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)

class StudentCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    class_id: uuid.UUID
    date_of_birth: date | None = None

class StudentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    class_id: uuid.UUID
    admission_number: str
    school_id: uuid.UUID
    enrollment_status: EnrollmentStatus
    
    model_config = ConfigDict(from_attributes=True)

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    class_id: Optional[uuid.UUID] = None
    date_of_birth: Optional[date] = None
    enrollment_status: Optional[EnrollmentStatus] = None

class StudentListResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    class_id: uuid.UUID
    admission_number: str
    first_name: str
    last_name: str
    email: EmailStr
    class_name: str
    enrollment_status: EnrollmentStatus
    parents: List[ParentBrief] = []

class PaginatedStudentResponse(BaseModel):
    total: int
    items: List[StudentListResponse]