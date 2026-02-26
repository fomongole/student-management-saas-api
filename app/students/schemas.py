import uuid
from datetime import date
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List

class StudentCreate(BaseModel):
    # User Account Details
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    
    # Academic Details
    class_id: uuid.UUID
    admission_number: str
    date_of_birth: date | None = None
    guardian_name: str | None = None
    guardian_contact: str | None = None

class StudentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    class_id: uuid.UUID
    admission_number: str
    school_id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)

class StudentUpdate(BaseModel):
    """Schema for updating a student and their underlying User profile."""
    # User Profile Fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # Academic & Guardian Fields
    class_id: Optional[uuid.UUID] = None
    admission_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    guardian_name: Optional[str] = None
    guardian_contact: Optional[str] = None

class StudentListResponse(BaseModel):
    """Flattened response optimized for frontend data tables."""
    id: uuid.UUID
    user_id: uuid.UUID
    class_id: uuid.UUID
    admission_number: str
    first_name: str
    last_name: str
    email: EmailStr
    class_name: str
    guardian_name: Optional[str]
    guardian_contact: Optional[str]

class PaginatedStudentResponse(BaseModel):
    """Wraps the list response with a total count for server-side pagination."""
    total: int
    items: List[StudentListResponse]