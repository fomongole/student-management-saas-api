from sqlalchemy.ext.asyncio import AsyncSession
from app.schools import schemas, repository
from app.schools.models import School
from app.auth.models import User
from app.core.enums import UserRole
from app.core.exceptions import (
    ForbiddenException,
    SchoolAlreadyExistsException,
)


async def create_new_school(
    db: AsyncSession,
    school_in: schemas.SchoolCreate,
    current_user: User,
) -> School:

    if current_user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenException(
            "Only Super Admins can onboard schools."
        )

    existing_school = await repository.get_school_by_email(db, school_in.email)
    if existing_school:
        raise SchoolAlreadyExistsException()

    return await repository.create_school(db, school_in)


async def generate_super_admin_dashboard(
    db: AsyncSession,
    current_user: User,
) -> schemas.SuperAdminDashboardResponse:

    if current_user.role != UserRole.SUPER_ADMIN:
        raise ForbiddenException(
            "Only SaaS Platform Owners can view these metrics."
        )

    metrics = await repository.get_platform_metrics(db)

    return schemas.SuperAdminDashboardResponse(
        platform_metrics=schemas.PlatformMetrics(**metrics)
    )