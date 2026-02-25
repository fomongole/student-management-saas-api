import uuid
from typing import TYPE_CHECKING
from datetime import date
from sqlalchemy import String, Float, Integer, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantModel

if TYPE_CHECKING:
    from app.schools.models import School
    from app.classes.models import Class
    from app.students.models import Student

class FeeStructure(TenantModel):
    """
    Defines a billable item for a specific academic term.
    Example: 'Term 1 Tuition 2026', 'Library Fee'.
    """
    __tablename__ = "fee_structures"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    term: Mapped[int] = mapped_column(Integer, nullable=False)
    
    class_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("classes.id", ondelete="RESTRICT"), 
        index=True, 
        nullable=True
    )
    
    school: Mapped["School"] = relationship("School", back_populates="fee_structures")
    class_relationship: Mapped["Class"] = relationship("Class")


class FeePayment(TenantModel):
    """
    The immutable ledger of financial transactions.
    """
    __tablename__ = "fee_payments"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="RESTRICT"), 
        index=True, 
        nullable=False
    )
    
    fee_structure_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fee_structures.id", ondelete="RESTRICT"), 
        index=True, 
        nullable=False
    )
    
    amount_paid: Mapped[float] = mapped_column(Float, nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    student: Mapped["Student"] = relationship("Student")
    fee_structure: Mapped["FeeStructure"] = relationship("FeeStructure")