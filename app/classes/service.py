from typing import Sequence
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.classes import repository
from app.classes.models import Class
from app.classes.schemas import ClassCreate, ClassUpdate
from app.auth.models import User
from app.core.enums import UserRole, AcademicLevel
from app.core.exceptions import (
    ClassAlreadyExistsException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
)

# ---------------------------------------------------------------------------
# Per-level caps: counts DISTINCT base class names (not total rows).
# Streams (P1 EAST, P1 WEST) and A-Level categories (S5 Sciences, S5 Arts)
# are variants of the same base class and do NOT count against this limit.
# ---------------------------------------------------------------------------
LEVEL_CLASS_LIMITS: dict[AcademicLevel, int] = {
    AcademicLevel.NURSERY:  3,   # e.g. Baby Class, Middle Class, Top Class
    AcademicLevel.PRIMARY:  7,   # P1 – P7
    AcademicLevel.O_LEVEL:  4,   # S1 – S4
    AcademicLevel.A_LEVEL:  2,   # S5 – S6 (each splits into Sciences / Arts)
}


async def create_new_class(db: AsyncSession, class_in: ClassCreate, current_user: User) -> Class:
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can manage classes.")

    # --- 1. Duplicate check (name + stream + category must be unique per school) ---
    existing_class = await repository.get_class_by_details(
        db=db,
        school_id=current_user.school_id,
        name=class_in.name,
        stream=class_in.stream,
        category=class_in.category,
    )
    if existing_class:
        raise ClassAlreadyExistsException()

    # --- 2. Per-level cap enforcement ---
    # Count distinct base class names already at this level.
    # A new name only counts if it's genuinely NEW (not just a new stream/category
    # variant of an already-registered base name).
    distinct_name_count = await repository.count_distinct_class_names_by_level(
        db=db,
        school_id=current_user.school_id,
        level=class_in.level,
    )

    is_new_base_name = not await repository.get_class_by_details(
        db=db,
        school_id=current_user.school_id,
        name=class_in.name,
        stream=None,       # Check for ANY variant with this name regardless of stream
        category=None,     # We'll handle this below with a raw name existence check
    )

    # More precise: check if ANY class with this base name already exists at this level.
    # If yes → it's just a new stream/category variant, not a new base class → no cap hit.
    name_already_registered = await _base_class_name_exists(
        db, current_user.school_id, class_in.name, class_in.level
    )

    limit = LEVEL_CLASS_LIMITS[class_in.level]
    if not name_already_registered and distinct_name_count >= limit:
        raise ConflictException(
            code="CLASS_LIMIT_REACHED",
            message=(
                f"This school has reached the maximum of {limit} "
                f"class(es) for the {class_in.level} level."
            ),
        )

    return await repository.create_class(
        db=db,
        class_in=class_in,
        school_id=current_user.school_id,
    )


async def _base_class_name_exists(
    db: AsyncSession, 
    school_id: uuid.UUID, 
    name: str, 
    level: AcademicLevel
) -> bool:
    """
    Helper: returns True if ANY class row with this (school, name, level)
    already exists — regardless of stream or category.
    This is what determines whether we're adding a variant or a brand-new class.
    """
    from sqlalchemy import select
    from app.classes.models import Class as ClassModel
    query = select(ClassModel.id).where(
        ClassModel.school_id == school_id,
        ClassModel.name == name,
        ClassModel.level == level,
    ).limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def get_school_classes(db: AsyncSession, current_user: User) -> Sequence[Class]:
    # Allow teachers to read the class list too if needed
    if current_user.role not in [UserRole.SCHOOL_ADMIN, UserRole.TEACHER]:
        raise ForbiddenException("Unauthorized.")

    return await repository.get_all_classes_for_school(
        db=db,
        school_id=current_user.school_id,
    )
    

async def update_class_details(
    db: AsyncSession, 
    class_id: uuid.UUID, 
    class_in: ClassUpdate, 
    current_user: User
) -> Class:
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can update classes.")

    target_class = await repository.get_class_by_id(
        db=db,
        class_id=class_id,
        school_id=current_user.school_id,
    )
    if not target_class:
        raise NotFoundException("Class not found.")

    update_data = class_in.model_dump(exclude_unset=True)

    # Resolve the final state after this patch to validate category consistency.
    new_level    = update_data.get("level",    target_class.level)
    new_category = update_data.get("category", target_class.category)

    if new_level == AcademicLevel.A_LEVEL and new_category is None:
        raise ConflictException(
            code="CATEGORY_REQUIRED",
            message="A-Level classes must have a category (SCIENCES or ARTS)."
        )
    if new_level != AcademicLevel.A_LEVEL and new_category is not None:
        raise ConflictException(
            code="CATEGORY_NOT_ALLOWED",
            message=f"Category is only applicable to A-Level classes, not {new_level}."
        )

    # --- Duplicate check against resolved final state ---
    new_name   = update_data.get("name",   target_class.name)
    new_stream = update_data.get("stream", target_class.stream)

    existing_class = await repository.get_class_by_details(
        db=db,
        school_id=current_user.school_id,
        name=new_name,
        stream=new_stream,
        category=new_category,
    )
    if existing_class and existing_class.id != target_class.id:
        raise ClassAlreadyExistsException()

    for field, value in update_data.items():
        setattr(target_class, field, value)

    db.add(target_class)
    await db.commit()
    
    # We MUST re-fetch the object so we don't return stale relationships
    return await repository.get_class_by_id(db, target_class.id, current_user.school_id)


async def remove_class(db: AsyncSession, class_id: uuid.UUID, current_user: User) -> None:
    if current_user.role != UserRole.SCHOOL_ADMIN:
        raise ForbiddenException("Only School Admins can delete classes.")

    # Call the highly optimized direct SQL execution
    deleted = await repository.delete_class_direct(
        db=db,
        class_id=class_id,
        school_id=current_user.school_id
    )

    if not deleted:
        raise NotFoundException("Class not found.")