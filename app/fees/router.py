import uuid
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.auth.models import User
from app.fees import schemas, service

from fastapi import Query
from typing import List

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

@router.get("/structure", response_model=List[schemas.FeeStructureResponse])
async def get_structures(
    year: int | None = Query(None, description="Filter by year"),
    term: int | None = Query(None, description="Filter by term"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves all billable fee structures."""
    return await service.list_fee_structures(db, year, term, current_user)

@router.get("/payment/student/{student_id}", response_model=List[schemas.FeePaymentDetailResponse])
async def get_payment_history(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves the itemized payment history (receipts) for a student."""
    return await service.get_student_payment_history(db, student_id, current_user)

@router.patch("/structure/{structure_id}", response_model=schemas.FeeStructureResponse, status_code=status.HTTP_200_OK)
async def update_structure(
    structure_id: uuid.UUID,
    structure_in: schemas.FeeStructureUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates an existing fee structure."""
    return await service.update_fee_structure(db, structure_id, structure_in, current_user)