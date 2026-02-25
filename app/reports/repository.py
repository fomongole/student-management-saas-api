import uuid
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.schools.models import School
from app.auth.models import User
from app.students.models import Student
from app.core.enums import UserRole
from app.fees.models import FeeStructure, FeePayment

async def get_population_metrics(db: AsyncSession, school_id: uuid.UUID) -> dict:
    """
    Optimized aggregation using relationships.
    """
    # 1. Count Students linked to this school
    student_count_query = select(func.count(Student.id)).where(Student.school_id == school_id)
    
    # 2. Grouped User counts (Teachers/Parents) linked to this school
    user_counts_query = (
        select(User.role, func.count(User.id).label("count")) 
        .where(User.school_id == school_id)
        .group_by(User.role)
    )

    student_res = await db.execute(student_count_query)
    user_res = await db.execute(user_counts_query)

    total_students = student_res.scalar() or 0
    role_counts = {row.role: row.count for row in user_res.all()}

    return {
        "total_students": total_students,
        "total_teachers": role_counts.get(UserRole.TEACHER, 0),
        "total_parents": role_counts.get(UserRole.PARENT, 0)
    }

async def get_financial_metrics(db: AsyncSession, year: int, term: int, school_id: uuid.UUID) -> dict:
    """
    Calculates exact school revenue by cross-referencing applicable Fee Structures 
    with current student population counts.
    """
    
    # --- STEP 1: CALCULATE TOTAL EXPECTED REVENUE (TOTAL BILLED) ---
    
    # A. Get all fee structures for this term
    fs_query = select(FeeStructure).where(
        and_(
            FeeStructure.year == year, 
            FeeStructure.term == term, 
            FeeStructure.school_id == school_id
        )
    )
    structures = (await db.execute(fs_query)).scalars().all()
    
    # B. Get student population grouped by class
    class_pop_query = (
        select(Student.class_id, func.count(Student.id).label("count"))
        .where(Student.school_id == school_id)
        .group_by(Student.class_id)
    )
    pop_rows = (await db.execute(class_pop_query)).all()
    
    # Create a dictionary mapping class_id to student count
    class_populations = {row.class_id: row.count for row in pop_rows}
    total_school_population = sum(class_populations.values())
    
    # C. Calculate actual expected billings
    total_billed = 0.0
    for fs in structures:
        if fs.class_id is None:
            # Global fee (e.g., General Library Fee) applies to all students
            total_billed += (fs.amount * total_school_population)
        else:
            # Class-specific fee (e.g., P4 Trip Fee) applies only to that class
            applicable_students = class_populations.get(fs.class_id, 0)
            total_billed += (fs.amount * applicable_students)


    # --- STEP 2: CALCULATE TOTAL COLLECTED ---
    
    paid_query = (
        select(func.coalesce(func.sum(FeePayment.amount_paid), 0))
        .join(FeeStructure, FeePayment.fee_structure_id == FeeStructure.id)
        .where(
            and_(
                FeeStructure.year == year,
                FeeStructure.term == term,
                FeePayment.school_id == school_id
            )
        )
    )
    
    total_paid = float((await db.execute(paid_query)).scalar() or 0)

    return {
        "total_billed": float(total_billed),
        "total_collected": total_paid,
        "outstanding_balance": float(total_billed - total_paid)
    }