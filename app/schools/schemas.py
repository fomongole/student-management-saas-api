import uuid
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

class SchoolCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    address: str | None = None

class SchoolResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    phone: str | None
    address: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class PlatformMetrics(BaseModel):
    total_schools: int
    active_schools: int
    total_users: int

class SuperAdminDashboardResponse(BaseModel):
    platform_metrics: PlatformMetrics

class SchoolUpdate(BaseModel):
    """
    Schema for updating a school. All fields are optional.
    If 'is_active' is passed as False, it effectively suspends the tenant.
    """
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

class SchoolWithCountResponse(SchoolResponse):
    """
    Inherits from SchoolResponse but adds the dynamically calculated student count.
    Used specifically for the Super Admin data table.
    """
    student_count: int