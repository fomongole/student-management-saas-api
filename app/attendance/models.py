import uuid
from datetime import date
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Date, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

from app.db.base import TenantModel
from app.core.enums import AttendanceStatus

if TYPE_CHECKING:
    from app.students.models import Student
    from app.classes.models import Class
    from app.subjects.models import Subject

class Attendance(TenantModel):
    """
    Main attendance ledger. Tracks student presence on a daily or subject basis.
    Designed for multi-tenant isolation using school_id.
    """
    __tablename__ = "attendance"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    
    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL"), 
        index=True, 
        nullable=True
    )
    
    attendance_date: Mapped[date] = mapped_column(
        Date, 
        index=True, 
        default=date.today, 
        nullable=False
    )
    
    status: Mapped[AttendanceStatus] = mapped_column(
        PG_ENUM(AttendanceStatus, name="attendancestatus"), 
        nullable=False
    )
    
    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint('student_id', 'attendance_date', 'subject_id', name='_student_attendance_uc'),
    )

    student: Mapped["Student"] = relationship("Student")
    class_relationship: Mapped["Class"] = relationship("Class")
    subject: Mapped["Subject"] = relationship("Subject")