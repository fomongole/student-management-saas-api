import uuid
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantModel

class ParentStudentLink(TenantModel):
    """
    Bridging table resolving the Many-to-Many relationship 
    between Parent users and Student profiles.
    """
    __tablename__ = "parent_student_links"

    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )
    
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), 
        index=True, 
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("parent_id", "student_id", name="_parent_student_link_uc"),
    )