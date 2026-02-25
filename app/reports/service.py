from sqlalchemy.ext.asyncio import AsyncSession

from app.reports import repository, schemas
from app.auth.models import User
from app.core.enums import UserRole
from app.core.exceptions import ForbiddenException


async def generate_admin_dashboard(
    db: AsyncSession,
    year: int,
    term: int,
    current_user: User,
) -> schemas.AdminDashboardResponse:
    """
    Generates executive dashboard metrics for school administrators.

    Business Rules:
    - Only SCHOOL_ADMIN can access school-wide metrics.
    - Metrics are scoped strictly to the admin's school.
    - Population and financial metrics are aggregated at repository layer.

    Security:
    - Prevents cross-school data exposure.
    - Prevents privilege escalation by non-admin roles.
    """

    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException(
            "Only School Admins can access the executive dashboard."
        )

    population_data = await repository.get_population_metrics(
        db,
        current_user.school_id,
    )

    financial_data = await repository.get_financial_metrics(
        db,
        year,
        term,
        current_user.school_id,
    )

    return schemas.AdminDashboardResponse(
        population=schemas.PopulationSummary(**population_data),
        financials=schemas.FinancialSummary(**financial_data),
    )