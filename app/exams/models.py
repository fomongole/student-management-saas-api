import uuid
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantModel

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.subjects.models import Subject
    from app.students.models import Student

class Exam(TenantModel):
    """
    Defines an assessment session (e.g., 'Term 1 Mid-term 2026').
    """
    __tablename__ = "exams"

    # Descriptive name: "End of Term 1", "Mock Exam"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Academic cycle
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    term: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Linked curriculum
    subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )

    __table_args__ = (
        # A school cannot have two exams with the same name for the same subject in the same term
        UniqueConstraint('school_id', 'name', 'year', 'term', 'subject_id', name='_school_exam_subject_uc'),
    )
    
    subject: Mapped["Subject"] = relationship("Subject")

class Result(TenantModel):
    """
    Stores individual student scores for a specific exam.
    """
    __tablename__ = "results"

    exam_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    
    # Raw numeric score (0.0 to 100.0)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    
    teacher_comment: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        # A student can only have one result per exam session
        UniqueConstraint('exam_id', 'student_id', name='_exam_student_result_uc'),
    )
    
    student: Mapped["Student"] = relationship("Student", back_populates="results")
    exam: Mapped["Exam"] = relationship("Exam")