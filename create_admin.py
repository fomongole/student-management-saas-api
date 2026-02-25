import asyncio
from sqlalchemy import select

# Import the registry first to "wake up" all models
import app.db.models 

from app.db.session import AsyncSessionLocal 
from app.auth.models import User
from app.core.enums import UserRole
from app.core.security import get_password_hash 

async def create_super_admin():
    async with AsyncSessionLocal() as db:
        query = select(User).where(User.email == "fomongole@saas.com")
        result = await db.execute(query)
        if result.scalar_one_or_none():
            print("⚠️ Super Admin already exists.")
            return

        admin = User(
            email="fomongole@saas.com",
            hashed_password=get_password_hash("StrongAdminPassword2026!"),
            first_name="Global",
            last_name="Admin",
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            school_id=None 
        )
        db.add(admin)
        await db.commit()
        print("✅ Super Admin 'fomongole@saas.com' created successfully.")

if __name__ == "__main__":
    asyncio.run(create_super_admin())