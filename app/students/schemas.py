import uuid
from datetime import date
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List

class ParentBrief(BaseModel):
    """Brief representation of a linked parent."""
    first_name: str
    last_name: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)

class StudentCreate(BaseModel):
    # User Account Details
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    
    # Academic Details
    class_id: uuid.UUID
    date_of_birth: date | None = None

class StudentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    class_id: uuid.UUID
    admission_number: str # Still returned so the frontend can see the generated ID
    school_id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    class_id: Optional[uuid.UUID] = None
    date_of_birth: Optional[date] = None

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
    parents: List[ParentBrief] = [] # Returns actual linked parent profiles

class PaginatedStudentResponse(BaseModel):
    total: int
    items: List[StudentListResponse]