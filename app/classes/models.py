from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Enum as SQLEnum, UniqueConstraint, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantModel
from app.core.enums import AcademicLevel, ALevelCategory
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

    # --- A_LEVEL only ---
    # For A-Level, every class must declare its category (Sciences or Arts).
    # P1 EAST vs P1 WEST are handled purely by 'stream'.
    # S5 Sciences vs S5 Arts are handled by 'category'.
    # This column is NULL for all non-A_Level classes.
    category: Mapped[ALevelCategory | None] = mapped_column(
        SQLEnum(ALevelCategory), nullable=True
    )
    
    form_teacher_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("teachers.id", ondelete="SET NULL"), 
        index=True, 
        nullable=True
    )
    
    school: Mapped["School"] = relationship("School", back_populates="classes")
    
    form_teacher: Mapped["Teacher"] = relationship("Teacher")

    __table_args__ = (
        # Uniqueness: a school cannot have two identical class+stream+category combos.
        # For non-A_Level, category is NULL and NULLs are treated as distinct by Postgres,
        # so we use a partial unique index via the UniqueConstraint here which covers the
        # general case. The service layer enforces A_Level category requirements.
        UniqueConstraint('school_id', 'name', 'stream', 'category', name='_school_class_stream_category_uc'),

        # Database-level guard: category MUST be set for A_Level, MUST be NULL otherwise.
        CheckConstraint(
            "(level = 'A_LEVEL' AND category IS NOT NULL) OR (level != 'A_LEVEL' AND category IS NULL)",
            name='_category_required_for_a_level'
        ),
    )