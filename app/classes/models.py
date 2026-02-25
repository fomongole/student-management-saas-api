from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantModel
from app.core.enums import AcademicLevel

if TYPE_CHECKING:
    from app.schools.models import School

class Class(TenantModel):
    __tablename__ = "classes"

    # e.g., "P4", "S1", "Top Class"
    name: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    
    # Primary calls them "Sections" (e.g., Red, Blue) 
    # High School calls them "Streams" (e.g., East, West, A, B)
    # Using a generic 'stream' column to handle both
    stream: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Tells the system how to handle grading and subjects later
    level: Mapped[AcademicLevel] = mapped_column(SQLEnum(AcademicLevel), nullable=False)
    
    # Max capacity for the physical room
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    school: Mapped["School"] = relationship("School", back_populates="classes")

    # A school cannot have two "S1 East" classes.
    # We enforce this at the database level across the specific tenant.
    __table_args__ = (
        UniqueConstraint('school_id', 'name', 'stream', name='_school_class_stream_uc'),
    )