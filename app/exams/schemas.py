import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List

class ExamCreate(BaseModel):
    """Schema for creating a new Exam session."""
    name: str = Field(..., example="End of Term 1")
    year: int = Field(..., example=2026)
    term: int = Field(..., example=1)
    subject_id: uuid.UUID

    @field_validator('name')
    @classmethod
    def normalize_name(cls, v: str) -> str:
        """Strips accidental spaces and standardizes casing."""
        return v.strip().upper()

class StudentMarkIn(BaseModel):
    """Schema for an individual student's score."""
    student_id: uuid.UUID
    score: float = Field(..., ge=0, le=100, description="Raw score between 0 and 100")
    teacher_comment: str | None = Field(None, max_length=255)

class BulkResultSubmit(BaseModel):
    """Schema for bulk mark entry by a teacher."""
    exam_id: uuid.UUID
    # we need to know the class context to verify students
    class_id: uuid.UUID 
    results: list[StudentMarkIn]

class ExamResponse(BaseModel):
    """Standard response for Exam metadata."""
    id: uuid.UUID
    name: str
    year: int
    term: int
    subject_id: uuid.UUID
    school_id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)

class ResultResponse(BaseModel):
    """Standard response for submitted marks."""
    id: uuid.UUID
    exam_id: uuid.UUID
    student_id: uuid.UUID
    score: float
    teacher_comment: str | None
    school_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class StudentMarkSheetDetail(BaseModel):
    """Combines Student data with their Result for the frontend grid."""
    student_id: uuid.UUID
    first_name: str
    last_name: str
    admission_number: str
    score: Optional[float] = None
    teacher_comment: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)