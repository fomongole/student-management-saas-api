import uuid
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional, List

class TeacherCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    qualification: str | None = None
    specialization: str | None = None

class UserBrief(BaseModel):
    """A safe, stripped-down view of the User profile for the frontend."""
    first_name: str
    last_name: str
    email: EmailStr
    
    model_config = ConfigDict(from_attributes=True)

class TeacherSubjectBrief(BaseModel):
    """Minimal subject info for the Teacher table 'Current Load'."""
    id: uuid.UUID
    name: str
    code: str
    
    model_config = ConfigDict(from_attributes=True)

class TeacherResponse(BaseModel):
    id: uuid.UUID
    employee_number: str
    qualification: str | None
    specialization: str | None
    school_id: uuid.UUID
    user: UserBrief
    assigned_subjects: List[TeacherSubjectBrief] = []
    
    model_config = ConfigDict(from_attributes=True)

class TeacherUpdate(BaseModel):
    """Schema for updating a teacher and their underlying User profile."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    employee_number: Optional[str] = None
    qualification: Optional[str] = None
    specialization: Optional[str] = None

    @field_validator('employee_number')
    @classmethod
    def normalize_employee_number(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip().upper()
        return v

class PaginatedTeacherResponse(BaseModel):
    """Wraps the list response with a total count for server-side pagination."""
    total: int
    items: List[TeacherResponse]