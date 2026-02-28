import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

from app.db.base import TenantModel
from app.core.enums import AcademicLevel

if TYPE_CHECKING:
    from app.schools.models import School
    from app.teachers.models import Teacher

class Subject(TenantModel):
    """
    Represents a specific subject within a school's curriculum.
    Subjects are isolated by school_id and categorized by academic level.
    """
    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    
    level: Mapped[AcademicLevel] = mapped_column(
        PG_ENUM(AcademicLevel, name="academiclevel", create_type=False), 
        nullable=False
    )
    
    is_core: Mapped[bool] = mapped_column(Boolean, default=True)
    
    school: Mapped["School"] = relationship("School", back_populates="subjects")
    
    assigned_teachers: Mapped[list["Teacher"]] = relationship(
        "Teacher",
        secondary="teacher_subjects",
        back_populates="assigned_subjects",
        viewonly=True # We use this for reading names easily
    )

    __table_args__ = (
        UniqueConstraint('school_id', 'code', 'level', name='_school_subject_code_level_uc'),
    )

class TeacherSubject(TenantModel):
    """
    Bridge table linking Teachers to the Subjects they are qualified to teach.
    This enables a Many-to-Many relationship while maintaining tenant isolation.
    """
    __tablename__ = "teacher_subjects"

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"), 
        index=True
    )
    
    subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), 
        index=True
    )

    __table_args__ = (
        UniqueConstraint('teacher_id', 'subject_id', name='_teacher_subject_uc'),
    )