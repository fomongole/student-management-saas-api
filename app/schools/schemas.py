import uuid
from pydantic import BaseModel, EmailStr, ConfigDict

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