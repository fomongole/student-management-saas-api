import pytest
from httpx import AsyncClient
from app.core.config import settings

@pytest.mark.asyncio
async def test_create_super_admin_missing_token(async_client: AsyncClient):
    """Test that creating a super admin without the bootstrap token fails."""
    response = await async_client.post(
        f"{settings.API_V1_STR}/auth/super-admin",
        json={
            "email": "test@admin.com",
            "password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "Admin"
        }
    )
    assert response.status_code in [403, 422] 

@pytest.mark.asyncio
async def test_create_super_admin_success(async_client: AsyncClient):
    """Test successful super admin creation."""
    expected_token = getattr(settings, "BOOTSTRAP_TOKEN", settings.SECRET_KEY)
    
    response = await async_client.post(
        f"{settings.API_V1_STR}/auth/super-admin",
        headers={"bootstrap-token": expected_token},
        json={
            "email": "test@admin.com",
            "password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "Admin"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@admin.com"
    assert data["role"] == "SUPER_ADMIN"
    assert "hashed_password" not in data