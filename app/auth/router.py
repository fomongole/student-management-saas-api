from fastapi import APIRouter, Depends, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.auth import schemas, service
from app.core.dependencies import get_current_user
from app.auth.models import User

router = APIRouter()

@router.post("/super-admin", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_super_admin(
    user_in: schemas.UserCreate, 
    bootstrap_token: str = Header(..., description="Secret token required for initial setup"),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates the global SUPER_ADMIN account.
    """
    return await service.create_super_admin(db, user_in, bootstrap_token)

@router.post("/login/access-token", response_model=schemas.Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    return await service.process_login(db, form_data.username, form_data.password)
    
@router.post("/school-admin", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register_school_admin(
    user_in: schemas.SchoolAdminCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a SCHOOL_ADMIN for a specific tenant.
    Requires a valid JWT token from a SUPER_ADMIN.
    """
    return await service.create_school_admin(db, user_in, current_user)

@router.get(
    "/me", 
    response_model=schemas.UserResponse, 
    status_code=status.HTTP_200_OK
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve the profile of the currently authenticated user.
    """
    return current_user