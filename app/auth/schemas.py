import uuid
from pydantic import BaseModel, EmailStr, ConfigDict
from app.core.enums import UserRole

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    
    # This tells Pydantic it's okay to read data from a SQLAlchemy ORM model
    model_config = ConfigDict(from_attributes=True)
    
# Token Response
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str | None = None
    
# Inherits everything from UserCreate (email, password, etc.) but adds school_id
class SchoolAdminCreate(UserCreate):
    school_id: uuid.UUID