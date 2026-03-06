import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantModel

if TYPE_CHECKING:
    from app.auth.models import User
    from app.subjects.models import Subject
    from app.classes.models import Class

class Teacher(TenantModel):
    __tablename__ = "teachers"

    # Link to their User account for login & basic info
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    
    # School-specific Employee ID
    employee_number: Mapped[str] = mapped_column(String(50), index=True)
    
    # E.g., "BSc Education", "PGDE"
    qualification: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # E.g., "Mathematics", "Science"
    specialization: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # An employee number must be unique within a specific school
    __table_args__ = (
        UniqueConstraint('school_id', 'employee_number', name='_school_employee_uc'),
    )

    user: Mapped["User"] = relationship("User")
    
    assigned_subjects: Mapped[list["Subject"]] = relationship(
        "Subject",
        secondary="teacher_subjects",
        back_populates="assigned_teachers",
        viewonly=True
    )


class TeacherAssignment(TenantModel):
    """
    Maps a Teacher to a Subject within a specific Class.
    Example: Mr. Smith (Teacher) teaches Math (Subject) in S1 East (Class).
    """
    __tablename__ = "teacher_assignments"

    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teachers.id", ondelete="CASCADE"), index=True, nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), index=True, nullable=False)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"), index=True, nullable=False)

    __table_args__ = (
        # A teacher shouldn't be assigned to the exact same subject in the same class twice
        UniqueConstraint('teacher_id', 'subject_id', 'class_id', name='_teacher_subject_class_uc'),
    )

    # --- Relationships ---
    teacher: Mapped["Teacher"] = relationship("Teacher")
    subject: Mapped["Subject"] = relationship("Subject")
    class_relationship: Mapped["Class"] = relationship("Class")