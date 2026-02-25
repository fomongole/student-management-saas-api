from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Boolean, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel

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