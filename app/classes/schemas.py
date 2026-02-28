import uuid
from pydantic import BaseModel, ConfigDict, field_validator
from app.core.enums import AcademicLevel
from typing import Optional

class ClassCreate(BaseModel):
    name: str                           
    stream: str | None = None           
    level: AcademicLevel                
    capacity: int | None = None
    form_teacher_id: uuid.UUID | None = None

    @field_validator('name', 'stream')
    @classmethod
    def normalize_strings(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip().upper()
        return v

class ClassResponse(BaseModel):
    id: uuid.UUID
    name: str
    stream: str | None
    level: AcademicLevel
    capacity: int | None
    school_id: uuid.UUID
    form_teacher_id: uuid.UUID | None
    
    model_config = ConfigDict(from_attributes=True)

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    stream: Optional[str] = None
    level: Optional[AcademicLevel] = None
    capacity: Optional[int] = None
    form_teacher_id: Optional[uuid.UUID] = None

    @field_validator('name', 'stream')
    @classmethod
    def normalize_strings(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip().upper()
        return v