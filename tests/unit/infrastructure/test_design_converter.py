"""Unit tests for Design converter."""

import pytest
from datetime import datetime, timezone
from app.infrastructure.database.models.design_model import DesignModel
from app.infrastructure.database.converters.design_converter import to_entity, to_model
from app.domain.entities.design import Design, DesignStatus


@pytest.mark.unit
def test_design_converter_to_entity():
    """Test converting DesignModel to Design entity."""
    # Arrange
    now = datetime.now(timezone.utc)
    model = DesignModel(
        id="design-123",
        user_id="user-456",
        product_type="t-shirt",
        design_data={
            "text": "Test Design",
            "font": "Bebas-Bold",
            "color": "#FF0000"
        },
        status="draft",
        preview_url=None,
        thumbnail_url=None,
        is_deleted=False,
        created_at=now,
        updated_at=now
    )
    
    # Act
    entity = to_entity(model)
    
    # Assert
    assert isinstance(entity, Design)
    assert entity.id == "design-123"
    assert entity.user_id == "user-456"
    assert entity.product_type == "t-shirt"
    assert entity.design_data["text"] == "Test Design"
    assert entity.design_data["font"] == "Bebas-Bold"
    assert entity.design_data["color"] == "#FF0000"
    assert entity.status == DesignStatus.DRAFT
    assert entity.preview_url is None
    assert entity.is_deleted is False


@pytest.mark.unit
def test_design_converter_to_entity_with_json_string():
    """Test converting DesignModel with string design_data to entity."""
    # Arrange
    now = datetime.now(timezone.utc)
    model = DesignModel(
        id="design-123",
        user_id="user-456",
        product_type="mug",
        design_data='{"text": "JSON String", "font": "Roboto-Regular", "color": "#00FF00"}',
        status="published",
        preview_url="https://example.com/preview.png",
        thumbnail_url="https://example.com/thumb.png",
        is_deleted=False,
        created_at=now,
        updated_at=now
    )
    
    # Act
    entity = to_entity(model)
    
    # Assert
    assert isinstance(entity, Design)
    assert entity.design_data["text"] == "JSON String"
    assert entity.design_data["font"] == "Roboto-Regular"
    assert entity.status == DesignStatus.PUBLISHED
    assert entity.preview_url == "https://example.com/preview.png"


@pytest.mark.unit
def test_design_converter_to_model_new():
    """Test converting Design entity to new DesignModel."""
    # Arrange
    entity = Design.create(
        user_id="user-789",
        product_type="t-shirt",
        design_data={
            "text": "New Design",
            "font": "Montserrat-Bold",
            "color": "#0000FF"
        }
    )
    
    # Act
    model = to_model(entity)
    
    # Assert
    assert isinstance(model, DesignModel)
    assert model.id == entity.id
    assert model.user_id == "user-789"
    assert model.product_type == "t-shirt"
    assert model.design_data["text"] == "New Design"
    assert model.status == "draft"  # String value
    assert model.is_deleted is False


@pytest.mark.unit
def test_design_converter_to_model_update_existing():
    """Test updating existing DesignModel from Design entity."""
    # Arrange
    entity = Design.create(
        user_id="user-update",
        product_type="mug",
        design_data={
            "text": "Updated",
            "font": "Bebas-Bold",
            "color": "#FFFF00"
        }
    )
    entity.mark_rendering()
    
    existing_model = DesignModel()
    existing_model.id = "old-id"
    existing_model.status = "draft"
    
    # Act
    updated_model = to_model(entity, existing_model)
    
    # Assert
    assert updated_model is existing_model  # Same instance
    assert updated_model.id == entity.id  # Updated
    assert updated_model.status == "rendering"  # Updated
    assert updated_model.product_type == "mug"


@pytest.mark.unit
def test_design_converter_roundtrip():
    """Test converting Design → Model → Design preserves data."""
    # Arrange
    original_entity = Design.create(
        user_id="roundtrip-user",
        product_type="t-shirt",
        design_data={
            "text": "Roundtrip Test",
            "font": "Pacifico-Regular",
            "color": "#FF00FF"
        }
    )
    
    # Act
    model = to_model(original_entity)
    converted_entity = to_entity(model)
    
    # Assert
    assert converted_entity.id == original_entity.id
    assert converted_entity.user_id == original_entity.user_id
    assert converted_entity.product_type == original_entity.product_type
    assert converted_entity.design_data == original_entity.design_data
    assert converted_entity.status == original_entity.status
    assert converted_entity.is_deleted == original_entity.is_deleted


@pytest.mark.unit
def test_design_converter_status_enum_conversion():
    """Test status enum conversion in both directions."""
    # Arrange
    entity = Design.create(
        user_id="user-status",
        product_type="t-shirt",
        design_data={"text": "Status Test", "font": "Bebas-Bold", "color": "#000000"}
    )
    
    # Test different statuses
    statuses = [
        (DesignStatus.DRAFT, "draft"),
        (DesignStatus.RENDERING, "rendering"),
        (DesignStatus.PUBLISHED, "published"),
        (DesignStatus.FAILED, "failed")
    ]
    
    for enum_status, string_status in statuses:
        # Entity → Model
        entity.status = enum_status
        model = to_model(entity)
        assert model.status == string_status
        
        # Model → Entity
        model.status = string_status
        converted = to_entity(model)
        assert converted.status == enum_status
