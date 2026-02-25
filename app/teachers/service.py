from sqlalchemy.ext.asyncio import AsyncSession

from app.teachers.schemas import TeacherCreate
from app.teachers.models import Teacher
from app.teachers import repository as teacher_repo
from app.auth.models import User
from app.auth import repository as auth_repo
from app.core.security import get_password_hash
from app.core.enums import UserRole
from app.core.exceptions import (
    ForbiddenException,
    UserEmailAlreadyExistsException,
)


async def onboard_teacher(
    db: AsyncSession,
    teacher_in: TeacherCreate,
    current_user: User,
) -> Teacher:
    """
    Onboards a new teacher into the school.

    Responsibilities:
    - Enforces RBAC (only SCHOOL_ADMIN allowed)
    - Ensures teacher email uniqueness
    - Creates both User and Teacher profile atomically
    - Ensures teacher is scoped to admin's school

    Security:
    - Prevents cross-school contamination
    - Prevents privilege escalation
    """

    # 1. RBAC Enforcement
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException(
            "Only School Admins can onboard teachers."
        )

    # 2. Email uniqueness check
    existing_user = await auth_repo.get_user_by_email(db, teacher_in.email)
    if existing_user:
        raise UserEmailAlreadyExistsException()

    # 3. Construct User entity
    new_user = User(
        email=teacher_in.email,
        hashed_password=get_password_hash(teacher_in.password),
        first_name=teacher_in.first_name,
        last_name=teacher_in.last_name,
        role=UserRole.TEACHER,
        school_id=current_user.school_id,
    )

    # 4. Construct Teacher profile entity
    new_teacher = Teacher(
        employee_number=teacher_in.employee_number,
        qualification=teacher_in.qualification,
        specialization=teacher_in.specialization,
        school_id=current_user.school_id,
    )

    # 5. Persist transactionally
    return await teacher_repo.create_teacher_transaction(
        db,
        new_user,
        new_teacher,
    )