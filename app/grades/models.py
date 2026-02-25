import uuid
from sqlalchemy import String, Float, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantModel

class GradingScale(TenantModel):
    """
    Defines the grading tiers for a school. 
    Allows different scales per academic level (e.g., Primary vs O-Level).
    """
    __tablename__ = "grading_scales"

    # e.g., "A+", "D1", "B3", "F"
    grade_symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Range boundaries
    min_score: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # e.g., "Distinction", "Credit", "Pass", "Fail"
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # e.g A+ = 12 points, D1 = 10 points, B3 = 8 points, F = 0 points
    points: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        # A school cannot have overlapping grades for the same symbol
        UniqueConstraint('school_id', 'grade_symbol', name='_school_grade_symbol_uc'),
    )