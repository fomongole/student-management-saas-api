import uuid
from datetime import date
from sqlalchemy import String, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

from app.db.base import TenantModel
from app.core.enums import EnrollmentStatus

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.schools.models import School
    from app.classes.models import Class
    from app.exams.models import Result
    from app.auth.models import User

class Student(TenantModel):
    __tablename__ = "students"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id", ondelete="RESTRICT"), index=True)
    
    admission_number: Mapped[str] = mapped_column(String(50), index=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    enrollment_status: Mapped[EnrollmentStatus] = mapped_column(
        PG_ENUM(EnrollmentStatus, name="enrollmentstatus", create_type=False),
        default=EnrollmentStatus.ACTIVE,
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint('school_id', 'admission_number', name='_school_admission_uc'),
    )

    school: Mapped["School"] = relationship("School", back_populates="students")
    user: Mapped["User"] = relationship("User")
    class_relationship: Mapped["Class"] = relationship("Class")
    results: Mapped[list["Result"]] = relationship("Result", back_populates="student")
    
    parents: Mapped[list["User"]] = relationship(
        "User",
        secondary="parent_student_links",
        primaryjoin="Student.id == foreign(ParentStudentLink.student_id)",
        secondaryjoin="foreign(ParentStudentLink.parent_id) == User.id",
        viewonly=True
    )