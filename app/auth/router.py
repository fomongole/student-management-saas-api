from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.db.session import get_db
from app.core.config import settings
from app.core.security import create_access_token
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
    Secured via a bootstrap token passed in the request headers to prevent unauthorized takeovers.
    """
    expected_token = getattr(settings, "BOOTSTRAP_TOKEN", settings.SECRET_KEY)
    
    if bootstrap_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid bootstrap token."
        )
        
    return await service.create_super_admin(db, user_in)

@router.post("/login/access-token", response_model=schemas.Token)
async def login_access_token(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = await service.authenticate_user(db, email=form_data.username, password=form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return {
        "access_token": create_access_token(
            subject=str(user.id),
            expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }
    
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
    
    This endpoint expects a valid JWT Bearer token in the Authorization header.
    It relies on the `get_current_user` dependency to validate the token and 
    fetch the user from the database. 
    
    The frontend will call this endpoint immediately after a successful login 
    (or on page refresh) to load the user's state, role, and school_id into memory 
    for UI rendering and route guarding.
    """
    return current_user