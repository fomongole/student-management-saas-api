import uuid
from pydantic import BaseModel, ConfigDict, field_validator
from app.core.enums import AcademicLevel

class SubjectCreate(BaseModel):
    name: str           # e.g., "Mathematics"
    code: str           # e.g., "MTC"
    level: AcademicLevel
    is_core: bool = True

    @field_validator('name', 'code')
    @classmethod
    def normalize_strings(cls, v: str) -> str:
        """Strips accidental spaces and standardizes casing to prevent DB duplicates."""
        if v:
            return v.strip().upper()
        return v

class SubjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    level: AcademicLevel
    is_core: bool
    school_id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)
    
class SubjectAssignment(BaseModel):
    teacher_id: uuid.UUID
    # We accept a list so an admin can assign 3-4 subjects in one click
    subject_ids: list[uuid.UUID]

class TeacherSubjectResponse(BaseModel):
    id: uuid.UUID
    teacher_id: uuid.UUID
    subject_id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)