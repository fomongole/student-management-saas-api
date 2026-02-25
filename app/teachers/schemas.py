import uuid
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator

class TeacherCreate(BaseModel):
    # User Account Details
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    
    # Professional Details
    employee_number: str
    qualification: str | None = None
    specialization: str | None = None

    @field_validator('employee_number')
    @classmethod
    def normalize_employee_number(cls, v: str) -> str:
        """Strips accidental spaces and standardizes casing."""
        return v.strip().upper()

class UserBrief(BaseModel):
    """A safe, stripped-down view of the User profile for the frontend."""
    first_name: str
    last_name: str
    email: EmailStr
    
    model_config = ConfigDict(from_attributes=True)

class TeacherResponse(BaseModel):
    id: uuid.UUID
    employee_number: str
    specialization: str | None
    school_id: uuid.UUID
    user: UserBrief
    
    model_config = ConfigDict(from_attributes=True)