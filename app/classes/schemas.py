import uuid
from pydantic import BaseModel, ConfigDict, field_validator
from app.core.enums import AcademicLevel

class ClassCreate(BaseModel):
    name: str                           # e.g., "P4", "S1"
    stream: str | None = None           # e.g., "Red", "East"
    level: AcademicLevel                # PRIMARY, O_LEVEL, A_LEVEL, etc.
    capacity: int | None = None

    @field_validator('name', 'stream')
    @classmethod
    def normalize_strings(cls, v: str | None) -> str | None:
        """Strips accidental spaces and standardizes casing to prevent DB duplicates."""
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
    
    model_config = ConfigDict(from_attributes=True)