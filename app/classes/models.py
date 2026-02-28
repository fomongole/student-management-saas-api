from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Enum as SQLEnum, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantModel
from app.core.enums import AcademicLevel
import uuid

if TYPE_CHECKING:
    from app.schools.models import School
    from app.teachers.models import Teacher

class Class(TenantModel):
    __tablename__ = "classes"

    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    stream: Mapped[str | None] = mapped_column(String(50), nullable=True)
    level: Mapped[AcademicLevel] = mapped_column(SQLEnum(AcademicLevel), nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    form_teacher_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL"), 
        index=True, 
        nullable=True
    )
    
    school: Mapped["School"] = relationship("School", back_populates="classes")
    
    form_teacher: Mapped["Teacher"] = relationship("Teacher")

    __table_args__ = (
        UniqueConstraint('school_id', 'name', 'stream', name='_school_class_stream_uc'),
    )