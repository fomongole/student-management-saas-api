import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional

class ExamCreate(BaseModel):
    name: str = Field(..., example="End of Term 1")
    year: int = Field(..., example=2026)
    term: int = Field(..., example=1)
    subject_id: uuid.UUID

    @field_validator('name')
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return v.strip().upper()

class ExamUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    term: Optional[int] = None
    subject_id: Optional[uuid.UUID] = None

    @field_validator('name')
    @classmethod
    def normalize_name(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip().upper()
        return v

class StudentMarkIn(BaseModel):
    student_id: uuid.UUID
    score: float = Field(..., ge=0, le=100)
    teacher_comment: str | None = Field(None, max_length=255)

class BulkResultSubmit(BaseModel):
    exam_id: uuid.UUID
    class_id: uuid.UUID 
    results: list[StudentMarkIn]

class ExamResponse(BaseModel):
    id: uuid.UUID
    name: str
    year: int
    term: int
    subject_id: uuid.UUID
    school_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class ResultResponse(BaseModel):
    id: uuid.UUID
    exam_id: uuid.UUID
    student_id: uuid.UUID
    score: float
    teacher_comment: str | None
    school_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class StudentMarkSheetDetail(BaseModel):
    student_id: uuid.UUID
    first_name: str
    last_name: str
    admission_number: str
    score: Optional[float] = None
    teacher_comment: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)