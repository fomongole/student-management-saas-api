import uuid
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.fees import schemas, service

router = APIRouter()

@router.post("/structure", response_model=schemas.FeeStructureResponse, status_code=status.HTTP_201_CREATED)
async def create_structure(
    structure_in: schemas.FeeStructureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a new billable fee item."""
    return await service.setup_fee_structure(db, structure_in, current_user)

@router.post("/payment", response_model=schemas.FeePaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_payment(
    payment_in: schemas.FeePaymentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Records a student's fee payment and triggers an alert."""
    return await service.process_student_payment(db, payment_in, current_user, background_tasks)

@router.get("/balance/{student_id}", response_model=schemas.StudentBalanceResponse)
async def check_balance(
    student_id: uuid.UUID,
    year: int,
    term: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves the financial balance for a student."""
    return await service.get_student_balance(db, student_id, year, term, current_user)