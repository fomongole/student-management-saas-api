import uuid
from datetime import date
from sqlalchemy import String, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantModel

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
    guardian_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    guardian_contact: Mapped[str | None] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        UniqueConstraint('school_id', 'admission_number', name='_school_admission_uc'),
    )

    school: Mapped["School"] = relationship("School", back_populates="students")
    
    user: Mapped["User"] = relationship("User")
    class_relationship: Mapped["Class"] = relationship("Class")
    results: Mapped[list["Result"]] = relationship("Result", back_populates="student")