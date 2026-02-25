import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.grades import repository, schemas
from app.auth.models import User
from app.core.enums import UserRole
from app.parents import repository as parent_repo
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
)

async def add_grading_tier(
    db: AsyncSession,
    tier_in: schemas.GradingScaleCreate,
    current_user: User,
):
    """
    Creates or updates grading scale tiers.
    """
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can define academic policies.")

    return await repository.sync_grading_tier(db, tier_in, current_user.school_id)

async def generate_report_card(
    db: AsyncSession,
    student_id: uuid.UUID,
    year: int,
    term: int,
    current_user: User,
) -> schemas.StudentReportCard:
    """
    Generates a report card with strict privacy enforcement and memory-optimized grading.
    """
    student = await repository.get_student_report_data(
        db, student_id, year, term, current_user.school_id
    )

    if not student:
        raise NotFoundException("Student not found or unauthorized access.")

    # Strict RBAC Enforcement
    if current_user.role == UserRole.STUDENT:
        if student.user_id != current_user.id:
            raise ForbiddenException("You can only view your own report card.")

    elif current_user.role == UserRole.PARENT:
        is_linked = await parent_repo.verify_parent_access(
            db, current_user.id, student_id, current_user.school_id
        )
        if not is_linked:
            raise ForbiddenException("You are not linked to this student.")

    # Filter term results
    relevant_results = [
        r for r in student.results
        if r.exam.year == year and r.exam.term == term
    ]

    if not relevant_results:
        raise NotFoundException(f"No results found for {year} Term {term}.")

    detailed_results = []
    total_points = 0
    total_score = 0

    # Fetch all grading tiers ONCE into memory
    all_tiers = await repository.get_all_grading_tiers(db, current_user.school_id)

    for res in relevant_results:
        # Evaluate the grade in memory rather than querying the DB per subject
        grade_tier = next(
            (t for t in all_tiers if t.min_score <= res.score <= t.max_score), 
            None
        )

        symbol = grade_tier.grade_symbol if grade_tier else "U"
        label = grade_tier.label if grade_tier else "Ungraded"
        pts = grade_tier.points if grade_tier else 9

        detailed_results.append(
            schemas.SubjectResultDetail(
                subject_name=res.exam.subject.name,
                subject_code=res.exam.subject.code,
                score=res.score,
                grade=symbol,
                label=label,
                points=pts,
                comment=res.teacher_comment,
            )
        )

        total_points += pts
        total_score += res.score

    return schemas.StudentReportCard(
        student_name=f"{student.user.first_name} {student.user.last_name}",
        class_name=student.class_relationship.name,
        term=term,
        year=year,
        results=detailed_results,
        total_points=total_points,
        average_score=round(total_score / len(relevant_results), 2),
    )