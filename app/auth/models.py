import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel
from app.core.enums import UserRole

if TYPE_CHECKING:
    from app.schools.models import School

class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False)

    # Tenant isolation: nullable=True ONLY because SUPER_ADMINs don't belong to a school.
    # Every other role MUST have a school_id, which enforce in the service layer.
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"), 
        index=True, 
        nullable=True
    )
    
    school: Mapped["School"] = relationship("School", back_populates="users")