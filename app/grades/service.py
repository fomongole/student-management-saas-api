import uuid
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession

from app.grades import repository, schemas
from app.auth.models import User
from app.core.enums import UserRole
from app.grades.models import GradingScale
from app.parents import repository as parent_repo
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
)
from typing import Sequence


async def add_grading_tier(
    db: AsyncSession,
    tier_in: schemas.GradingScaleCreate,
    current_user: User,
):
    """Creates or updates grading scale tiers."""
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
    Generates a per-session report card with strict privacy enforcement.

    Key redesign: results are now grouped by exam session name so the
    report card mirrors how real school report cards work — a term can
    have multiple exam sessions (e.g. "Mid-Term Test", "End of Term Exam")
    and each appears as its own section with its own subtotals.
    """
    student = await repository.get_student_report_data(
        db, student_id, year, term, current_user.school_id
    )

    if not student:
        raise NotFoundException("Student not found or unauthorized access.")

    # --- RBAC ---
    if current_user.role == UserRole.STUDENT:
        if student.user_id != current_user.id:
            raise ForbiddenException("You can only view your own report card.")

    elif current_user.role == UserRole.PARENT:
        is_linked = await parent_repo.verify_parent_access(
            db, current_user.id, student_id, current_user.school_id
        )
        if not is_linked:
            raise ForbiddenException("You are not linked to this student.")

    # Filter to this term's results only
    relevant_results = [
        r for r in student.results
        if r.exam.year == year and r.exam.term == term
    ]

    if not relevant_results:
        # Return an empty but valid report card so the frontend can render
        # "No results yet" without a 404 crashing the page.
        return schemas.StudentReportCard(
            student_name=f"{student.user.first_name} {student.user.last_name}",
            class_name=student.class_relationship.name,
            term=term,
            year=year,
            sessions=[],
            overall_average=0.0,
            overall_total_points=0,
        )

    # Fetch all grading tiers ONCE into memory (avoids N+1 queries)
    all_tiers = await repository.get_all_grading_tiers(db, current_user.school_id)

    def resolve_grade(score: float):
        tier = next(
            (t for t in all_tiers if t.min_score <= score <= t.max_score), None
        )
        return (
            tier.grade_symbol if tier else "U",
            tier.label if tier else "Ungraded",
            tier.points if tier else 9,
        )

    # Group results by exam session name, preserving insertion order
    # so sessions appear in the order exams were created.
    session_buckets: dict[str, list] = defaultdict(list)
    for res in relevant_results:
        session_name = res.exam.name  # e.g. "Beginning of Term Test"
        session_buckets[session_name].append(res)

    sessions: list[schemas.ExamSessionReport] = []
    grand_total_score = 0.0
    grand_total_points = 0
    grand_count = 0

    for session_name, session_results in session_buckets.items():
        detailed: list[schemas.SubjectResultDetail] = []
        session_score_sum = 0.0
        session_points_sum = 0

        for res in session_results:
            grade_symbol, label, pts = resolve_grade(res.score)
            detailed.append(
                schemas.SubjectResultDetail(
                    subject_name=res.exam.subject.name,
                    subject_code=res.exam.subject.code,
                    score=res.score,
                    grade=grade_symbol,
                    label=label,
                    points=pts,
                    comment=res.teacher_comment,
                )
            )
            session_score_sum += res.score
            session_points_sum += pts

        n = len(detailed)
        sessions.append(
            schemas.ExamSessionReport(
                session_name=session_name,
                results=detailed,
                session_average=round(session_score_sum / n, 2) if n else 0.0,
                session_total_points=session_points_sum,
            )
        )
        grand_total_score += session_score_sum
        grand_total_points += session_points_sum
        grand_count += n

    return schemas.StudentReportCard(
        student_name=f"{student.user.first_name} {student.user.last_name}",
        class_name=student.class_relationship.name,
        term=term,
        year=year,
        sessions=sessions,
        overall_average=round(grand_total_score / grand_count, 2) if grand_count else 0.0,
        overall_total_points=grand_total_points,
    )


async def get_school_grading_scales(
    db: AsyncSession,
    current_user: User
) -> Sequence[GradingScale]:
    """Retrieves all grading tiers for the admin's school."""
    if current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.TEACHER]:
        raise ForbiddenException("Unauthorized to view academic settings.")

    return await repository.get_all_grading_tiers(db, current_user.school_id)


async def remove_grading_tier(
    db: AsyncSession,
    tier_id: uuid.UUID,
    current_user: User
) -> None:
    """Safely deletes a grading tier."""
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can modify academic policies.")

    tier = await repository.get_tier_by_id(db, tier_id, current_user.school_id)
    if not tier:
        raise NotFoundException("Grading tier not found.")

    await repository.delete_tier(db, tier)