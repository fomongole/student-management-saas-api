import uuid
from datetime import date
from pydantic import BaseModel, EmailStr, ConfigDict

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