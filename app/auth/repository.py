from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.auth.models import User

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Fetches a user by their email address."""
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    return result.scalar_one_or_none()

import uuid
async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Fetches a user by their UUID."""
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user: User) -> User:
    """Saves a new user instance to the database."""
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user