from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import uuid


class GradingScaleCreate(BaseModel):
    grade_symbol: str
    min_score: float
    max_score: float
    label: str
    points: int


class GradingScaleResponse(BaseModel):
    id: uuid.UUID
    grade_symbol: str
    min_score: float
    max_score: float
    label: str
    points: int

    model_config = ConfigDict(from_attributes=True)


class SubjectResultDetail(BaseModel):
    """A single subject's result within one exam session."""
    subject_name: str
    subject_code: str
    score: float
    grade: str       # e.g. "D1", "B3"
    label: str       # e.g. "Distinction", "Credit"
    points: int
    comment: Optional[str] = None


class ExamSessionReport(BaseModel):
    """
    All results for one named exam session within a term.

    Example: "Beginning of Term Test" or "End of Term Exam".
    A term can have any number of these — the school decides.
    """
    session_name: str
    results: List[SubjectResultDetail]
    session_average: float
    session_total_points: int


class StudentReportCard(BaseModel):
    """
    Full academic report for a student for a given term.

    Results are organised into exam sessions so the student (and PDF) clearly
    sees "Beginning of Term — Maths: 85%" vs "End of Term — Maths: 91%"
    without conflating them.
    """
    student_name: str
    class_name: str
    term: int
    year: int
    sessions: List[ExamSessionReport]
    overall_average: float
    overall_total_points: int