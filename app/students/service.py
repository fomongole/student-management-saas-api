import uuid

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.students.schemas import (
    StudentCreate,
    StudentUpdate,
    PaginatedStudentResponse
)
from app.students.schemas import StudentCreate
from app.students.models import Student
from app.students import repository as student_repo
from app.auth.models import User
from app.classes.models import Class
from app.auth import repository as auth_repo
from app.core.security import get_password_hash
from app.core.enums import UserRole
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    UserEmailAlreadyExistsException,
)

from app.notifications.service import dispatch_alert
from app.notifications.models import NotificationType


async def onboard_student(
    db: AsyncSession,
    student_in: StudentCreate,
    current_user: User,
    background_tasks: BackgroundTasks,
) -> Student:
    """
    Onboards a student into a school.

    Responsibilities:
    - Enforces RBAC (SCHOOL_ADMIN only)
    - Validates class ownership within school
    - Ensures student email uniqueness
    - Creates User + Student profile transactionally
    - Dispatches welcome notification asynchronously

    Security:
    - Prevents cross-school class injection
    - Prevents duplicate identity registration
    """

    # 1. RBAC enforcement
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException(
            "Only School Admins can admit students."
        )

    # 2. Validate class belongs to this school
    class_query = select(Class).where(
        Class.id == student_in.class_id,
        Class.school_id == current_user.school_id,
    )
    result = await db.execute(class_query)
    existing_class = result.scalar_one_or_none()

    if not existing_class:
        raise NotFoundException(
            "Class not found or does not belong to your school."
        )

    # 3. Email uniqueness
    if await auth_repo.get_user_by_email(db, student_in.email):
        raise UserEmailAlreadyExistsException()

    # 4. Build User entity
    new_user = User(
        email=student_in.email,
        hashed_password=get_password_hash(student_in.password),
        first_name=student_in.first_name,
        last_name=student_in.last_name,
        role=UserRole.STUDENT,
        school_id=current_user.school_id,
    )

    # 5. Build Student profile entity
    new_student = Student(
        class_id=student_in.class_id,
        admission_number=student_in.admission_number,
        date_of_birth=student_in.date_of_birth,
        guardian_name=student_in.guardian_name,
        guardian_contact=student_in.guardian_contact,
        school_id=current_user.school_id,
    )

    # 6. Persist transactionally
    saved_student = await student_repo.create_student_transaction(
        db,
        new_user,
        new_student,
    )

    # 7. Dispatch welcome notification asynchronously
    welcome_message = (
        f"Welcome to the school, {student_in.first_name}! "
        f"Your admission number is {student_in.admission_number}. "
        f"You can now log in using your email ({student_in.email}) "
        f"and the password provided during registration."
    )

    await dispatch_alert(
        db=db,
        background_tasks=background_tasks,
        recipient_id=saved_student.user_id,
        title="Welcome to your Student Portal",
        message=welcome_message,
        type=NotificationType.EMAIL,
        school_id=current_user.school_id,
    )

    return saved_student


# Add this alongside your existing onboard_student function
async def get_paginated_students(
    db: AsyncSession,
    current_user: User,
    skip: int,
    limit: int,
    class_id: uuid.UUID | None,
    search: str | None
) -> PaginatedStudentResponse:
    
    if current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.TEACHER]:
        raise ForbiddenException("You are not authorized to view the student directory.")

    total, students = await student_repo.get_students_with_pagination(
        db, current_user.school_id, skip, limit, class_id, search
    )
    
    # Flatten the SQLAlchemy entities for the frontend
    formatted_items = []
    for s in students:
        formatted_items.append({
            "id": s.id,
            "user_id": s.user_id,
            "class_id": s.class_id,
            "admission_number": s.admission_number,
            "first_name": s.user.first_name,
            "last_name": s.user.last_name,
            "email": s.user.email,
            "class_name": s.class_relationship.name,
            "guardian_name": s.guardian_name,
            "guardian_contact": s.guardian_contact
        })
        
    return PaginatedStudentResponse(total=total, items=formatted_items)


async def update_student_profile(
    db: AsyncSession,
    student_id: uuid.UUID,
    student_in: StudentUpdate,
    current_user: User
) -> Student:
    
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can update student profiles.")
        
    student = await student_repo.get_student_with_user(db, student_id, current_user.school_id)
    if not student:
        raise NotFoundException("Student not found.")
        
    # If they are changing classes, verify the new class actually belongs to this school
    if student_in.class_id:
        class_query = select(Class).where(
            Class.id == student_in.class_id, 
            Class.school_id == current_user.school_id
        )
        if not (await db.execute(class_query)).scalar_one_or_none():
            raise NotFoundException("Target class not found or invalid.")
            
    update_data = student_in.model_dump(exclude_unset=True)
    return await student_repo.update_student_transaction(db, student, update_data)

async def get_my_student_profile(db: AsyncSession, current_user: User):
    """Retrieves the student profile for the authenticated student."""
    if current_user.role != UserRole.STUDENT:
        raise ForbiddenException("Only students can access this endpoint.")
        
    student = await student_repo.get_student_by_user_id(db, current_user.id, current_user.school_id)
    
    if not student:
        raise NotFoundException("Student profile not found for this user.")
        
    # Format to match the StudentListResponse schema so the frontend gets the names
    return {
        "id": student.id,
        "user_id": student.user_id,
        "class_id": student.class_id,
        "admission_number": student.admission_number,
        "first_name": student.user.first_name,
        "last_name": student.user.last_name,
        "email": student.user.email,
        "class_name": student.class_relationship.name,
        "guardian_name": student.guardian_name,
        "guardian_contact": student.guardian_contact
    }