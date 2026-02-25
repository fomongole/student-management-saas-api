import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.grades import schemas, service

router = APIRouter()

@router.post("/", response_model=schemas.GradingScaleResponse, status_code=status.HTTP_201_CREATED)
async def create_grading_tier(
    tier_in: schemas.GradingScaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Define a grade (e.g., 80-100 = D1)."""
    return await service.add_grading_tier(db, tier_in, current_user)


@router.get("/report-card/{student_id}", response_model=schemas.StudentReportCard)
async def get_student_report(
    student_id: uuid.UUID,
    year: int,
    term: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates a comprehensive report card for a student."""
    return await service.generate_report_card(db, student_id, year, term, current_user)