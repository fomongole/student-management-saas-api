import uuid
from pydantic import BaseModel, ConfigDict, field_validator
from app.core.enums import AcademicLevel
from typing import Optional, List

# Add teacher_id to the Create schema
class SubjectCreate(BaseModel):
    name: str           
    code: str           
    level: AcademicLevel
    is_core: bool = True
    teacher_id: Optional[uuid.UUID] = None

    @field_validator('name', 'code')
    @classmethod
    def normalize_strings(cls, v: str) -> str:
        if v:
            return v.strip().upper()
        return v

class SubjectTeacherBrief(BaseModel):
    """Minimal teacher info for the Subject table."""
    id: uuid.UUID
    first_name: str
    last_name: str

    @field_validator('first_name', mode='before')
    @classmethod
    def get_first_name(cls, v, info):
        # This helper extracts the name from the linked User model
        if hasattr(info.data.get('user'), 'first_name'):
            return info.data['user'].first_name
        return v

class SubjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    level: AcademicLevel
    is_core: bool
    school_id: uuid.UUID
    teachers: List[SubjectTeacherBrief] = [] 
    
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

class SubjectUpdate(BaseModel):
    """Schema for updating a subject. All fields are optional."""
    name: Optional[str] = None
    code: Optional[str] = None
    level: Optional[AcademicLevel] = None
    is_core: Optional[bool] = None

    @field_validator('name', 'code')
    @classmethod
    def normalize_strings(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip().upper()
        return v

class TeacherSubjectDetailResponse(BaseModel):
    """Returns the actual subject details assigned to a teacher."""
    id: uuid.UUID
    teacher_id: uuid.UUID
    subject: SubjectResponse  # Nested relationship data
    
    model_config = ConfigDict(from_attributes=True)