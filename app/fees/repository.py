import uuid
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.fees.models import FeeStructure, FeePayment
from app.fees import schemas
from app.students.models import Student
from sqlalchemy.orm import joinedload
from typing import Sequence

async def create_fee_structure(db: AsyncSession, structure_in: schemas.FeeStructureCreate, school_id: uuid.UUID) -> FeeStructure:
    """Inserts a new billable fee structure."""
    db_obj = FeeStructure(**structure_in.model_dump(), school_id=school_id)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def record_payment(db: AsyncSession, payment_in: schemas.FeePaymentCreate, school_id: uuid.UUID) -> FeePayment:
    """Inserts an immutable payment record into the ledger."""
    db_obj = FeePayment(**payment_in.model_dump(), school_id=school_id)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def check_reference_exists(db: AsyncSession, reference_number: str, school_id: uuid.UUID) -> bool:
    """Prevents double-entry of the same bank receipt."""
    query = select(FeePayment).where(
        and_(FeePayment.reference_number == reference_number, FeePayment.school_id == school_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None

async def get_student_financial_summary(db: AsyncSession, student_id: uuid.UUID, year: int, term: int, school_id: uuid.UUID) -> dict:
    """Aggregates total billed vs total paid for a specific term."""
    
    # 1. Fetching the student's class to ensure we don't bill them for other classes
    student_query = select(Student.class_id).where(Student.id == student_id)
    student_class_id = (await db.execute(student_query)).scalar()

    # 2. Calculates Total Billed (Global fees + Class-specific fees)
    billed_query = select(func.coalesce(func.sum(FeeStructure.amount), 0)).where(
        and_(
            FeeStructure.year == year, 
            FeeStructure.term == term, 
            FeeStructure.school_id == school_id,
            or_(FeeStructure.class_id == student_class_id, FeeStructure.class_id.is_(None))
        )
    )
    billed_result = await db.execute(billed_query)
    total_billed = billed_result.scalar()

    # 3. Calculate Total Paid
    paid_query = (
        select(func.coalesce(func.sum(FeePayment.amount_paid), 0))
        .select_from(FeePayment)
        .join(FeeStructure)
        .where(
            and_(
                FeePayment.student_id == student_id,
                FeeStructure.year == year,
                FeeStructure.term == term,
                FeePayment.school_id == school_id
            )
        )
    )
    paid_result = await db.execute(paid_query)
    total_paid = paid_result.scalar()

    return {
        "total_billed": float(total_billed),
        "total_paid": float(total_paid),
        "outstanding_balance": float(total_billed - total_paid)
    }
    

async def get_all_fee_structures(
    db: AsyncSession, 
    school_id: uuid.UUID, 
    year: int | None = None, 
    term: int | None = None
) -> Sequence[FeeStructure]:
    """Fetches the billable items, optionally filtered by academic term."""
    query = select(FeeStructure).where(FeeStructure.school_id == school_id)
    
    if year:
        query = query.where(FeeStructure.year == year)
    if term:
        query = query.where(FeeStructure.term == term)
        
    query = query.order_by(FeeStructure.year.desc(), FeeStructure.term.desc(), FeeStructure.name)
    result = await db.execute(query)
    return result.scalars().all()

async def get_student_payments(
    db: AsyncSession, 
    student_id: uuid.UUID, 
    school_id: uuid.UUID
) -> Sequence[FeePayment]:
    """Fetches a student's payment history, eager-loading the fee structure details."""
    query = (
        select(FeePayment)
        .options(joinedload(FeePayment.fee_structure))
        .where(
            and_(FeePayment.student_id == student_id, FeePayment.school_id == school_id)
        )
        .order_by(FeePayment.payment_date.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()