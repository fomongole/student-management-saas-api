from sqlalchemy.ext.asyncio import AsyncSession

from app.reports import repository, schemas
from app.auth.models import User
from app.core.enums import UserRole
from app.core.exceptions import ForbiddenException
import io
import csv
from fastapi.responses import StreamingResponse


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

async def generate_defaulters_csv(db: AsyncSession, year: int, term: int, current_user: User) -> StreamingResponse:
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can export financial reports.")
        
    defaulters = await repository.get_fee_defaulters(db, year, term, current_user.school_id)
    
    # Create an in-memory string buffer for the CSV
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=["admission_number", "first_name", "last_name", "total_billed", "total_paid", "balance"])
    
    writer.writeheader()
    for row in defaulters:
        writer.writerow(row)
        
    # Reset the stream position to the beginning
    stream.seek(0)
    
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=fee_defaulters_{year}_term_{term}.csv"
    
    return response