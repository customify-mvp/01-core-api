"""Integration tests for design endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_create_design_success(authenticated_client):
    """Test POST /designs with valid data."""
    client, headers = authenticated_client
    
    response = await client.post(
        "/api/v1/designs",
        headers=headers,
        json={
            "product_type": "t-shirt",
            "design_data": {
                "text": "Test Design",
                "font": "Bebas-Bold",
                "color": "#FF0000"
            },
            "use_ai_suggestions": False
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["product_type"] == "t-shirt"
    assert data["status"] == "draft"
    assert data["design_data"]["text"] == "Test Design"
    assert "id" in data
    assert "user_id" in data


@pytest.mark.integration
async def test_create_design_unauthenticated(client: AsyncClient):
    """Test POST /designs without auth."""
    response = await client.post(
        "/api/v1/designs",
        json={
            "product_type": "t-shirt",
            "design_data": {
                "text": "Test",
                "font": "Bebas-Bold",
                "color": "#FF0000"
            }
        }
    )
    
    assert response.status_code == 403


@pytest.mark.integration
async def test_create_design_whitespace_text(authenticated_client):
    """Test POST /designs with whitespace-only text."""
    client, headers = authenticated_client
    
    response = await client.post(
        "/api/v1/designs",
        headers=headers,
        json={
            "product_type": "t-shirt",
            "design_data": {
                "text": "   ",  # Whitespace only
                "font": "Bebas-Bold",
                "color": "#FF0000"
            }
        }
    )
    
    assert response.status_code == 422  # Validation error
    assert "whitespace" in response.json()["detail"][0]["msg"].lower()


@pytest.mark.integration
async def test_create_design_invalid_color(authenticated_client):
    """Test POST /designs with invalid color format."""
    client, headers = authenticated_client
    
    response = await client.post(
        "/api/v1/designs",
        headers=headers,
        json={
            "product_type": "t-shirt",
            "design_data": {
                "text": "Test",
                "font": "Bebas-Bold",
                "color": "red"  # Invalid format
            }
        }
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.integration
async def test_list_designs(authenticated_client):
    """Test GET /designs pagination."""
    client, headers = authenticated_client
    
    # Create 3 designs
    for i in range(3):
        await client.post(
            "/api/v1/designs",
            headers=headers,
            json={
                "product_type": "t-shirt",
                "design_data": {
                    "text": f"Design {i}",
                    "font": "Bebas-Bold",
                    "color": "#FF0000"
                }
            }
        )
    
    # List designs
    response = await client.get("/api/v1/designs", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["designs"]) == 3
    assert data["total"] == 3
    assert data["skip"] == 0
    assert data["limit"] == 20
    assert data["has_more"] is False


@pytest.mark.integration
async def test_list_designs_pagination(authenticated_client):
    """Test GET /designs with pagination parameters."""
    client, headers = authenticated_client
    
    # Create 5 designs
    for i in range(5):
        await client.post(
            "/api/v1/designs",
            headers=headers,
            json={
                "product_type": "t-shirt",
                "design_data": {
                    "text": f"Design {i}",
                    "font": "Bebas-Bold",
                    "color": "#FF0000"
                }
            }
        )
    
    # Get first 2
    response = await client.get("/api/v1/designs?skip=0&limit=2", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["designs"]) == 2
    assert data["total"] == 5
    assert data["has_more"] is True
    
    # Get next 2
    response = await client.get("/api/v1/designs?skip=2&limit=2", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["designs"]) == 2
    assert data["total"] == 5
    assert data["has_more"] is True


@pytest.mark.integration
async def test_get_design_by_id(authenticated_client):
    """Test GET /designs/{id}."""
    client, headers = authenticated_client
    
    # Create design
    create_response = await client.post(
        "/api/v1/designs",
        headers=headers,
        json={
            "product_type": "mug",
            "design_data": {
                "text": "Coffee Time",
                "font": "Pacifico-Regular",
                "color": "#00FF00"
            }
        }
    )
    design_id = create_response.json()["id"]
    
    # Get design
    response = await client.get(f"/api/v1/designs/{design_id}", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == design_id
    assert data["product_type"] == "mug"
    assert data["design_data"]["text"] == "Coffee Time"


@pytest.mark.integration
async def test_get_design_not_found(authenticated_client):
    """Test GET /designs/{id} with non-existent ID."""
    client, headers = authenticated_client
    
    response = await client.get("/api/v1/designs/nonexistent-id", headers=headers)
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.integration
async def test_list_designs_unauthenticated(client: AsyncClient):
    """Test GET /designs without auth."""
    response = await client.get("/api/v1/designs")
    
    assert response.status_code == 403


@pytest.mark.integration
async def test_get_design_unauthenticated(client: AsyncClient):
    """Test GET /designs/{id} without auth."""
    response = await client.get("/api/v1/designs/some-id")
    
    assert response.status_code == 403
