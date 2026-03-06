import uuid
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List
from app.core.enums import AcademicLevel

class SchoolCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    address: str | None = None
    academic_levels: List[AcademicLevel] = Field(..., min_length=1, description="Cannot be changed after creation.")

class SchoolLevelResponse(BaseModel):
    level: AcademicLevel
    model_config = ConfigDict(from_attributes=True)

class SchoolResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    phone: str | None
    address: str | None
    is_active: bool
    academic_levels: List[SchoolLevelResponse] = []

    model_config = ConfigDict(from_attributes=True)

class SchoolUpdate(BaseModel):
    """
    Schema for updating a school's profile details.
    'academic_levels' is NOT here — using the dedicated PATCH /levels endpoint.
    """
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

class SchoolLevelUpdate(BaseModel):
    """
    Schema for a Super Admin to replace a school's academic levels.
    This is a full replacement (PUT semantics), not a partial patch.

    Design choice: replacing all levels at once prevents orphaned partial state
    and keeps the operation atomic. The service layer validates the new list
    before wiping the old one.
    """
    academic_levels: List[AcademicLevel] = Field(
        ..., 
        min_length=1, 
        description="Full replacement list of academic levels for the school."
    )

class SchoolConfigResponse(BaseModel):
    current_academic_year: int
    current_term: int
    currency_symbol: str
    model_config = ConfigDict(from_attributes=True)

class SchoolConfigUpdate(BaseModel):
    current_academic_year: Optional[int] = None
    current_term: Optional[int] = Field(None, ge=1, le=3)
    currency_symbol: Optional[str] = None

class PlatformMetrics(BaseModel):
    total_schools: int
    active_schools: int
    total_users: int

class SuperAdminDashboardResponse(BaseModel):
    platform_metrics: PlatformMetrics

class SchoolWithCountResponse(SchoolResponse):
    student_count: int