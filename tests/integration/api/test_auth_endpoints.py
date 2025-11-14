"""Integration tests for auth endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_register_success(client: AsyncClient):
    """Test POST /auth/register with valid data."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "register@test.com",
            "password": "Test1234",
            "full_name": "Register Test"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "register@test.com"
    assert data["full_name"] == "Register Test"
    assert "id" in data
    assert "password_hash" not in data  # Security: don't expose
    assert data["is_active"] is True
    assert data["is_verified"] is False


@pytest.mark.integration
async def test_register_duplicate_email(client: AsyncClient):
    """Test POST /auth/register with duplicate email."""
    # Register first user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@test.com",
            "password": "Test1234",
            "full_name": "First"
        }
    )
    
    # Try to register again with same email
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@test.com",
            "password": "Test1234",
            "full_name": "Second"
        }
    )
    
    assert response.status_code == 409  # Conflict
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.integration
async def test_register_invalid_password(client: AsyncClient):
    """Test POST /auth/register with weak password."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@test.com",
            "password": "weak",  # Too short
            "full_name": "Weak Test"
        }
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.integration
async def test_login_success(client: AsyncClient, test_user_data):
    """Test POST /auth/login with valid credentials."""
    # Register first
    await client.post("/api/v1/auth/register", json=test_user_data)
    
    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data
    assert data["expires_in"] == 10080  # 7 days in minutes
    assert data["user"]["email"] == test_user_data["email"]


@pytest.mark.integration
async def test_login_invalid_credentials(client: AsyncClient):
    """Test POST /auth/login with invalid credentials."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@test.com",
            "password": "WrongPass123"
        }
    )
    
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.integration
async def test_login_case_insensitive_email(client: AsyncClient):
    """Test POST /auth/login with case-insensitive email."""
    # Register with lowercase
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "case@test.com",
            "password": "Test1234",
            "full_name": "Case Test"
        }
    )
    
    # Login with uppercase
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "CASE@TEST.COM",
            "password": "Test1234"
        }
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.integration
async def test_get_me_authenticated(authenticated_client):
    """Test GET /auth/me with valid token."""
    client, headers = authenticated_client
    
    response = await client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "full_name" in data
    assert "is_active" in data
    assert "password_hash" not in data


@pytest.mark.integration
async def test_get_me_unauthenticated(client: AsyncClient):
    """Test GET /auth/me without token."""
    response = await client.get("/api/v1/auth/me")
    
    assert response.status_code == 403  # FastAPI HTTPBearer returns 403


@pytest.mark.integration
async def test_get_me_invalid_token(client: AsyncClient):
    """Test GET /auth/me with invalid token."""
    headers = {"Authorization": "Bearer invalid_token_here"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 401


@pytest.mark.integration
async def test_health_check(client: AsyncClient):
    """Test GET /health endpoint."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "customify-core-api"
    assert "database" in data
    assert data["database"] == "healthy"
