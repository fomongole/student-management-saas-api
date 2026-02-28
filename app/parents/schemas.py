import uuid
from pydantic import BaseModel, EmailStr, ConfigDict, Field

class ParentOnboardCreate(BaseModel):
    """Payload for an Admin creating a new Parent account."""
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
    """Data returned to the Parent Portal dashboard."""
    student_id: uuid.UUID
    first_name: str
    last_name: str 
    admission_number: str
    class_name: str
    
    model_config = ConfigDict(from_attributes=True)

class ParentListResponse(BaseModel):
    """Basic parent profile data for the Admin directory."""
    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)

class ParentLinkCreate(BaseModel):
    """Payload to add students to an EXISTING parent."""
    student_ids: list[uuid.UUID]