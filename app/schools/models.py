from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Boolean, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel, TenantModel

if TYPE_CHECKING:
    from app.auth.models import User
    from app.classes.models import Class
    from app.students.models import Student
    from app.subjects.models import Subject
    from app.fees.models import FeeStructure

class School(BaseModel):
    __tablename__ = "schools"

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Soft Delete column. If null, school is active. If set, school is "deleted".
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # --- Relationships ---
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="school", cascade="all, delete-orphan"
    )

    classes: Mapped[List["Class"]] = relationship(
        "Class", back_populates="school", cascade="all, delete-orphan"
    )

    students: Mapped[List["Student"]] = relationship(
        "Student", back_populates="school", cascade="all, delete-orphan"
    )

    subjects: Mapped[List["Subject"]] = relationship(
        "Subject", back_populates="school", cascade="all, delete-orphan"
    )
    
    fee_structures: Mapped[List["FeeStructure"]] = relationship(
        "FeeStructure", back_populates="school", cascade="all, delete-orphan"
    )

    # One-to-one relationship with Configuration
    configuration: Mapped["SchoolConfiguration"] = relationship(
        "SchoolConfiguration", back_populates="school", uselist=False, cascade="all, delete-orphan"
    )

class SchoolConfiguration(TenantModel):
    """
    Stores school-specific settings like the current term and year.
    Uses TenantModel to ensure strict isolation via school_id.
    """
    __tablename__ = "school_configurations"

    current_academic_year: Mapped[int] = mapped_column(Integer, default=2026)
    current_term: Mapped[int] = mapped_column(Integer, default=1)
    currency_symbol: Mapped[str] = mapped_column(String(10), default="UGX")

    # Link back to school
    school: Mapped["School"] = relationship("School", back_populates="configuration")