import uuid
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional

class ParentOnboardCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    student_ids: list[uuid.UUID] = Field(..., description="List of Student IDs to link to this parent.")

class ParentStudentLinkResponse(BaseModel):
    id: uuid.UUID
    parent_id: uuid.UUID
    student_id: uuid.UUID
    school_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class LinkedChildResponse(BaseModel):
    student_id: uuid.UUID
    first_name: str
    last_name: str 
    admission_number: str
    class_name: str
    model_config = ConfigDict(from_attributes=True)

class ParentListResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    is_active: bool
    children: list[LinkedChildResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class ParentLinkCreate(BaseModel):
    student_ids: list[uuid.UUID]

class ParentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None