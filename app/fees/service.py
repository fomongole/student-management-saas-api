import uuid
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.fees import repository, schemas
from app.auth.models import User
from app.core.enums import UserRole
from app.students import repository as student_repo
from app.parents import repository as parent_repo
from app.notifications.service import dispatch_alert
from app.notifications.models import NotificationType
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    ConflictException,
)


async def setup_fee_structure(
    db: AsyncSession,
    structure_in: schemas.FeeStructureCreate,
    current_user: User,
):
    """
    Creates or updates a school's fee structure.

    Business Rules:
    - Only SCHOOL_ADMIN may manage fee structures.
    - Structure is strictly scoped to the admin's school.
    """

    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException(
            "Only School Admins can manage fee structures."
        )

    return await repository.create_fee_structure(
        db,
        structure_in,
        current_user.school_id,
    )


async def process_student_payment(
    db: AsyncSession,
    payment_in: schemas.FeePaymentCreate,
    current_user: User,
    background_tasks: BackgroundTasks,
):
    """
    Records a student payment transaction securely.

    Business Rules:
    - Only SCHOOL_ADMIN may record payments.
    - Payment reference must be unique (anti-fraud).
    - Student must belong to the same school.
    - Dispatch receipt notification asynchronously.
    """

    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException(
            "Only School Admins can record payments."
        )

    # Prevents duplicate reference (anti double-entry)
    if await repository.check_reference_exists(
        db,
        payment_in.reference_number,
        current_user.school_id,
    ):
        raise ConflictException(
            code="DUPLICATE_PAYMENT_REFERENCE",
            message="Payment reference number already exists.",
        )

    # Validate student ownership
    student = await student_repo.get_student(
        db,
        payment_in.student_id,
        current_user.school_id,
    )

    if not student:
        raise NotFoundException(
            "Student not found in this school."
        )

    # Persist payment ledger entry
    payment_record = await repository.record_payment(
        db,
        payment_in,
        current_user.school_id,
    )

    # Dispatch receipt notification
    message_body = (
        f"A payment of UGX {payment_in.amount_paid:,.2f} has been successfully recorded. "
        f"Receipt Reference: {payment_in.reference_number}"
    )

    await dispatch_alert(
        db=db,
        background_tasks=background_tasks,
        recipient_id=student.user_id,
        title="Fee Payment Received",
        message=message_body,
        type=NotificationType.EMAIL,
        school_id=current_user.school_id,
    )

    return payment_record


async def get_student_balance(
    db: AsyncSession,
    student_id: uuid.UUID,
    year: int,
    term: int,
    current_user: User,
) -> schemas.StudentBalanceResponse:
    """
    Calculates and returns a student's financial balance securely.

    Access Rules:
    - STUDENT may only view own balance.
    - PARENT may only view linked student.
    - ADMIN has full access within school scope.
    """

    # Validate student belongs to school
    student = await student_repo.get_student(
        db,
        student_id,
        current_user.school_id,
    )

    if not student:
        raise NotFoundException("Student not found.")

    # Strict privacy enforcement
    if current_user.role == UserRole.STUDENT:
        if student.user_id != current_user.id:
            raise ForbiddenException(
                "You can only view your own fee balance."
            )

    elif current_user.role == UserRole.PARENT:
        is_linked = await parent_repo.verify_parent_access(
            db,
            current_user.id,
            student_id,
            current_user.school_id,
        )

        if not is_linked:
            raise ForbiddenException(
                "You are not linked to this student."
            )

    financials = await repository.get_student_financial_summary(
        db,
        student_id,
        year,
        term,
        current_user.school_id,
    )

    return schemas.StudentBalanceResponse(
        student_id=student_id,
        total_billed=financials["total_billed"],
        total_paid=financials["total_paid"],
        outstanding_balance=financials["total_billed"]
        - financials["total_paid"],
    )