import uuid
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.parents.models import ParentStudentLink
from app.students.models import Student
from app.auth.models import User

async def validate_students_exist(db: AsyncSession, student_ids: list[uuid.UUID], school_id: uuid.UUID) -> bool:
    """
    PERFORMANCE FIX: Validates that all provided student IDs exist 
    and belong to the school in a single database query.
    """
    query = select(func.count(Student.id)).where(
        and_(Student.id.in_(student_ids), Student.school_id == school_id)
    )
    result = await db.execute(query)
    return result.scalar() == len(student_ids)

async def create_parent_and_links(
    db: AsyncSession, 
    new_user: User, 
    student_ids: list[uuid.UUID], 
    school_id: uuid.UUID
) -> list[ParentStudentLink]:
    """
    Transactional execution: Creates the parent account and their student links atomically.
    """
    db.add(new_user)
    await db.flush()
    
    links = []
    for s_id in student_ids:
        link = ParentStudentLink(
            parent_id=new_user.id,
            student_id=s_id,
            school_id=school_id
        )
        db.add(link)
        links.append(link)
        
    await db.flush() 
    await db.commit()
        
    return links

async def get_children_for_parent(db: AsyncSession, parent_id: uuid.UUID, school_id: uuid.UUID) -> list[Student]:
    """
    Fetches the actual Student profiles linked to a specific Parent.
    """
    query = (
        select(Student)
        .options(joinedload(Student.user)) 
        .join(ParentStudentLink, ParentStudentLink.student_id == Student.id)
        .where(
            and_(
                ParentStudentLink.parent_id == parent_id,
                ParentStudentLink.school_id == school_id
            )
        )
    )
    result = await db.execute(query)
    return result.scalars().all()

async def verify_parent_access(db: AsyncSession, parent_id: uuid.UUID, student_id: uuid.UUID, school_id: uuid.UUID) -> bool:
    """
    Security function: Used by other modules to ensure a parent 
    is legally linked to a student before returning sensitive data.
    """
    query = select(ParentStudentLink.id).where(
        and_(
            ParentStudentLink.parent_id == parent_id,
            ParentStudentLink.student_id == student_id,
            ParentStudentLink.school_id == school_id
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None

async def get_all_parents(db: AsyncSession, school_id: uuid.UUID) -> list[User]:
    """Fetches all users with the PARENT role for a specific school."""
    query = select(User).where(
        and_(User.role == "PARENT", User.school_id == school_id)
    ).order_by(User.last_name, User.first_name)
    
    result = await db.execute(query)
    return list(result.scalars().all())

async def add_links_to_existing_parent(
    db: AsyncSession, 
    parent_id: uuid.UUID, 
    student_ids: list[uuid.UUID], 
    school_id: uuid.UUID
) -> list[ParentStudentLink]:
    """Links new students to a parent, ignoring duplicates."""
    # 1. Check existing links to prevent IntegrityError crashes
    existing_query = select(ParentStudentLink.student_id).where(
        ParentStudentLink.parent_id == parent_id
    )
    existing_students = (await db.execute(existing_query)).scalars().all()
    
    new_links = []
    for s_id in student_ids:
        if s_id not in existing_students:
            link = ParentStudentLink(
                parent_id=parent_id,
                student_id=s_id,
                school_id=school_id
            )
            db.add(link)
            new_links.append(link)
            
    if new_links:
        await db.flush()
        await db.commit()
        
    return new_links

async def remove_parent_link(
    db: AsyncSession, 
    parent_id: uuid.UUID, 
    student_id: uuid.UUID, 
    school_id: uuid.UUID
) -> None:
    """Severs the tie between a parent and a student."""
    query = select(ParentStudentLink).where(
        and_(
            ParentStudentLink.parent_id == parent_id,
            ParentStudentLink.student_id == student_id,
            ParentStudentLink.school_id == school_id
        )
    )
    link = (await db.execute(query)).scalar_one_or_none()
    
    if link:
        await db.delete(link)
        await db.commit()