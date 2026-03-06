from collections import defaultdict
import uuid
from sqlalchemy import delete, select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.parents.models import ParentStudentLink
from app.students.models import Student
from app.auth.models import User

async def validate_students_exist(db: AsyncSession, student_ids: list[uuid.UUID], school_id: uuid.UUID) -> bool:
    """
    Validates that all provided student IDs exist 
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
    """Fetches the actual Student profiles linked to a specific Parent."""
    query = (
        select(Student)
        .options(
            joinedload(Student.user),
            joinedload(Student.class_relationship)
        ) 
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

async def get_all_parents_with_children(db: AsyncSession, school_id: uuid.UUID) -> list[dict]:
    """
    Highly optimized fetch of all parents and their linked students.
    """
    # 1. Fetch Parents
    parent_query = select(User).where(and_(User.role == "PARENT", User.school_id == school_id))
    parents = (await db.execute(parent_query)).scalars().all()
    
    if not parents:
        return []
        
    # 2. Fetch all linked students for these parents in one query
    links_query = (
        select(ParentStudentLink.parent_id, Student)
        .join(Student, Student.id == ParentStudentLink.student_id)
        .options(joinedload(Student.user), joinedload(Student.class_relationship))
        .where(ParentStudentLink.school_id == school_id)
    )
    links = (await db.execute(links_query)).all()
    
    # 3. Map children to their respective parent IDs
    children_map = defaultdict(list)
    for parent_id, student in links:
        children_map[parent_id].append({
            "student_id": student.id,
            "first_name": student.user.first_name,
            "last_name": student.user.last_name,
            "admission_number": student.admission_number,
            "class_name": student.class_relationship.name
        })
        
    # 4. Construct response dictionary
    result = []
    for p in parents:
        result.append({
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "email": p.email,
            "is_active": p.is_active,
            "children": children_map.get(p.id, [])
        })
    return result

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
        
async def update_parent_user(db: AsyncSession, parent_id: uuid.UUID, school_id: uuid.UUID, update_data: dict) -> User | None:
    query = select(User).where(and_(User.id == parent_id, User.school_id == school_id, User.role == "PARENT"))
    parent = (await db.execute(query)).scalar_one_or_none()
    
    if not parent:
        return None
        
    for key, value in update_data.items():
        setattr(parent, key, value)
        
    db.add(parent)
    await db.commit()
    await db.refresh(parent)
    return parent

async def delete_parent_user(db: AsyncSession, parent_id: uuid.UUID, school_id: uuid.UUID) -> bool:
    stmt = delete(User).where(and_(User.id == parent_id, User.school_id == school_id, User.role == "PARENT"))
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0