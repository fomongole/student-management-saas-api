import uuid
from pydantic import BaseModel, ConfigDict, Field

class GradingScaleCreate(BaseModel):
    grade_symbol: str
    min_score: float = Field(..., ge=0)
    max_score: float = Field(..., le=100)
    label: str
    points: int

class GradingScaleResponse(BaseModel):
    id: uuid.UUID
    grade_symbol: str
    min_score: float
    max_score: float
    label: str
    points: int
    school_id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)
    
class SubjectResultDetail(BaseModel):
    subject_name: str
    subject_code: str
    score: float
    grade: str
    label: str
    points: int
    comment: str | None

class StudentReportCard(BaseModel):
    student_name: str
    class_name: str
    term: int
    year: int
    results: list[SubjectResultDetail]
    total_points: int
    average_score: float