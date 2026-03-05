from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Boolean, Text, DateTime, Integer, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.db.base import BaseModel, TenantModel
from app.core.enums import AcademicLevel

if TYPE_CHECKING:
    from app.auth.models import User
    from app.classes.models import Class
    from app.students.models import Student
    from app.subjects.models import Subject
    from app.fees.models import FeeStructure

class SchoolLevel(BaseModel):
    """
    Immutable mapping table linking a school to its supported academic levels 
    (e.g., Nursery, Primary, O_Level, A_Level).
    """
    __tablename__ = "school_levels"

    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), index=True, nullable=False)
    level: Mapped[AcademicLevel] = mapped_column(SQLEnum(AcademicLevel), nullable=False)

    __table_args__ = (
        # A school cannot have the exact same level assigned twice
        UniqueConstraint('school_id', 'level', name='_school_academic_level_uc'),
    )

class School(BaseModel):
    __tablename__ = "schools"

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Soft Delete column
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # --- Relationships ---
    academic_levels: Mapped[List["SchoolLevel"]] = relationship(
        "SchoolLevel", cascade="all, delete-orphan"
    )

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

    configuration: Mapped["SchoolConfiguration"] = relationship(
        "SchoolConfiguration", back_populates="school", uselist=False, cascade="all, delete-orphan"
    )

class SchoolConfiguration(TenantModel):
    __tablename__ = "school_configurations"

    current_academic_year: Mapped[int] = mapped_column(Integer, default=2026)
    current_term: Mapped[int] = mapped_column(Integer, default=1)
    currency_symbol: Mapped[str] = mapped_column(String(10), default="UGX")

    school: Mapped["School"] = relationship("School", back_populates="configuration")