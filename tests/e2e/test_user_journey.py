"""End-to-End test for complete user journey."""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
async def test_complete_user_journey(client: AsyncClient):
    """
    Test complete user journey: Register → Login → Create Design → Get.
    
    This E2E test validates the entire user flow from registration through
    design creation and retrieval.
    """
    # Step 1: Register new user
    register_payload = {
        "email": "e2e_test@example.com",
        "password": "SecurePass123!",
        "full_name": "E2E Test User"
    }
    
    register_response = await client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201
    register_data = register_response.json()
    assert register_data["email"] == "e2e_test@example.com"
    assert register_data["full_name"] == "E2E Test User"
    user_id = register_data["id"]
    
    # Step 2: Login
    login_payload = {
        "email": "e2e_test@example.com",
        "password": "SecurePass123!"
    }
    
    login_response = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"
    access_token = login_data["access_token"]
    
    # Setup authorization headers
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Step 3: Create a design
    create_design_payload = {
        "product_type": "t-shirt",
        "design_data": {
            "text": "E2E Test Design",
            "font": "Bebas-Bold",
            "color": "#FF0000"
        },
        "use_ai_suggestions": False
    }
    
    create_response = await client.post(
        "/api/v1/designs",
        json=create_design_payload,
        headers=headers
    )
    assert create_response.status_code == 201
    design_data = create_response.json()
    assert design_data["product_type"] == "t-shirt"
    assert design_data["status"] == "draft"
    assert design_data["design_data"]["text"] == "E2E Test Design"
    assert design_data["user_id"] == user_id
    design_id = design_data["id"]
    
    # Step 4: Get specific design by ID to verify persistence
    get_response = await client.get(f"/api/v1/designs/{design_id}", headers=headers)
    assert get_response.status_code == 200
    retrieved_design = get_response.json()
    assert retrieved_design["id"] == design_id
    assert retrieved_design["product_type"] == "t-shirt"
    assert retrieved_design["status"] == "draft"
    assert retrieved_design["user_id"] == user_id
    assert retrieved_design["design_data"]["text"] == "E2E Test Design"
    assert retrieved_design["design_data"]["font"] == "Bebas-Bold"
    assert retrieved_design["design_data"]["color"] == "#FF0000"
    
    # Validate complete flow success
    print(f"✅ E2E Test Complete: User {user_id} created design {design_id}")
