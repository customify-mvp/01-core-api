"""Unit tests for Design entity."""

import pytest
from app.domain.entities.design import Design, DesignStatus


@pytest.mark.unit
def test_design_create():
    """Test Design.create() factory method."""
    design = Design.create(
        user_id="user-123",
        product_type="t-shirt",
        design_data={
            "text": "Hello World",
            "font": "Bebas-Bold",
            "color": "#FF0000"
        }
    )
    
    assert design.id is not None
    assert design.user_id == "user-123"
    assert design.product_type == "t-shirt"
    assert design.design_data["text"] == "Hello World"
    assert design.status == DesignStatus.DRAFT
    assert design.created_at is not None


@pytest.mark.unit
def test_design_validate_success():
    """Test Design.validate() with valid data."""
    design = Design.create(
        user_id="user-123",
        product_type="t-shirt",
        design_data={
            "text": "Valid Text",
            "font": "Bebas-Bold",
            "color": "#FF0000"
        }
    )
    
    # Should not raise ValueError
    design.validate()


@pytest.mark.unit
def test_design_validate_missing_text():
    """Test Design.validate() raises error when text missing after creation."""
    design = Design.create(
        user_id="user-123",
        product_type="t-shirt",
        design_data={
            "text": "Test",
            "font": "Bebas-Bold",
            "color": "#FF0000"
        }
    )
    
    # Remove text to trigger validation error
    del design.design_data["text"]
    
    with pytest.raises(ValueError, match="Missing required field: text"):
        design.validate()


@pytest.mark.unit
def test_design_validate_empty_text():
    """Test Design.validate() raises error for empty text."""
    design = Design.create(
        user_id="user-123",
        product_type="t-shirt",
        design_data={
            "text": "Test",
            "font": "Bebas-Bold",
            "color": "#FF0000"
        }
    )
    
    design.design_data["text"] = ""
    
    with pytest.raises(ValueError, match="Text cannot be empty"):
        design.validate()


@pytest.mark.unit
def test_design_validate_invalid_font():
    """Test Design.validate() raises error for invalid font."""
    design = Design.create(
        user_id="user-123",
        product_type="t-shirt",
        design_data={
            "text": "Test",
            "font": "Bebas-Bold",
            "color": "#FF0000"
        }
    )
    
    design.design_data["font"] = "InvalidFont"
    
    with pytest.raises(ValueError, match="Invalid font"):
        design.validate()


@pytest.mark.unit
def test_design_validate_invalid_color_format():
    """Test Design.validate() raises error for invalid color format."""
    design = Design.create(
        user_id="user-123",
        product_type="t-shirt",
        design_data={
            "text": "Test",
            "font": "Bebas-Bold",
            "color": "#FF0000"
        }
    )
    
    design.design_data["color"] = "red"  # Invalid format
    
    with pytest.raises(ValueError, match="Invalid color format"):
        design.validate()


@pytest.mark.unit
def test_design_mark_published():
    """Test Design.mark_published() changes status."""
    design = Design.create(
        user_id="user-123",
        product_type="t-shirt",
        design_data={
            "text": "Test",
            "font": "Bebas-Bold",
            "color": "#FF0000"
        }
    )
    
    assert design.status == DesignStatus.DRAFT
    
    # First mark as rendering
    design.mark_rendering()
    assert design.status == DesignStatus.RENDERING
    
    # Then mark as published
    design.mark_published(preview_url="https://example.com/preview.png")
    
    assert design.status == DesignStatus.PUBLISHED
    assert design.preview_url == "https://example.com/preview.png"


@pytest.mark.unit
def test_design_mark_failed():
    """Test Design.mark_failed() changes status."""
    design = Design.create(
        user_id="user-123",
        product_type="t-shirt",
        design_data={
            "text": "Test",
            "font": "Bebas-Bold",
            "color": "#FF0000"
        }
    )
    
    assert design.status == DesignStatus.DRAFT
    
    # First mark as rendering
    design.mark_rendering()
    assert design.status == DesignStatus.RENDERING
    
    # Then mark as failed
    design.mark_failed(error_message="Rendering failed")
    
    assert design.status == DesignStatus.FAILED
    assert design.design_data["error_message"] == "Rendering failed"


@pytest.mark.unit
def test_design_update_data():
    """Test Design.update_data() updates design_data."""
    design = Design.create(
        user_id="user-123",
        product_type="t-shirt",
        design_data={
            "text": "Test",
            "font": "Bebas-Bold",
            "color": "#FF0000"
        }
    )
    
    assert design.preview_url is None
    
    # Update design data
    new_data = {
        "text": "Updated Text",
        "font": "Montserrat-Bold",
        "color": "#00FF00"
    }
    design.update_data(new_data)
    
    assert design.design_data["text"] == "Updated Text"
    assert design.design_data["font"] == "Montserrat-Bold"
    assert design.design_data["color"] == "#00FF00"
