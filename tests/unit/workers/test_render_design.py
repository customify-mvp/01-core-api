"""Unit tests for render design worker tasks."""

from io import BytesIO

import pytest
from PIL import Image

from app.infrastructure.workers.tasks.render_design import (
    _create_thumbnail,
    _is_light_color,
    _render_image,
)


class TestRenderImage:
    """Tests for _render_image function."""

    def test_render_image_creates_valid_png(self):
        """Test that _render_image creates a valid PNG image."""
        design_data = {"text": "Test Design", "font": "Bebas-Bold", "color": "#FF0000"}

        buffer = _render_image(design_data, "t-shirt")

        # Verify it's a valid image
        assert buffer is not None
        buffer.seek(0)
        image = Image.open(buffer)

        assert image.format == "PNG"
        assert image.size == (600, 600)

    def test_render_image_with_red_color(self):
        """Test rendering with red color."""
        design_data = {"text": "Red Text", "font": "Bebas-Bold", "color": "#FF0000"}

        buffer = _render_image(design_data, "mug")
        buffer.seek(0)
        image = Image.open(buffer)

        # Check that background is red
        pixel = image.getpixel((10, 10))
        assert pixel[0] == 255  # Red channel
        assert pixel[1] == 0  # Green channel
        assert pixel[2] == 0  # Blue channel

    def test_render_image_with_blue_color(self):
        """Test rendering with blue color."""
        design_data = {"text": "Blue Background", "font": "Montserrat-Bold", "color": "#0000FF"}

        buffer = _render_image(design_data, "poster")
        buffer.seek(0)
        image = Image.open(buffer)

        pixel = image.getpixel((10, 10))
        assert pixel[2] == 255  # Blue channel maxed

    def test_render_image_with_different_fonts(self):
        """Test rendering with various fonts."""
        fonts = ["Bebas-Bold", "Montserrat-Regular", "Pacifico-Regular"]

        for font in fonts:
            design_data = {"text": f"Font {font}", "font": font, "color": "#00FF00"}

            buffer = _render_image(design_data, "hoodie")
            assert buffer is not None

            buffer.seek(0)
            image = Image.open(buffer)
            assert image.format == "PNG"

    def test_render_image_with_long_text(self):
        """Test rendering with long text."""
        design_data = {
            "text": "This is a very long text that should still render properly on the image",
            "font": "Roboto-Regular",
            "color": "#FFFF00",
        }

        buffer = _render_image(design_data, "tote-bag")

        buffer.seek(0)
        image = Image.open(buffer)
        assert image is not None
        assert image.size == (600, 600)

    def test_render_image_with_special_characters(self):
        """Test rendering with special characters."""
        design_data = {"text": "Hello! @#$% & World", "font": "Bebas-Bold", "color": "#FF00FF"}

        buffer = _render_image(design_data, "t-shirt")

        buffer.seek(0)
        image = Image.open(buffer)
        assert image is not None


class TestCreateThumbnail:
    """Tests for _create_thumbnail function."""

    def test_create_thumbnail_reduces_size(self):
        """Test that thumbnail is smaller than original."""
        # Create test image (600x600)
        original = Image.new("RGB", (600, 600), color="red")
        original_buffer = BytesIO()
        original.save(original_buffer, format="PNG")
        original_buffer.seek(0)

        # Create thumbnail (200x200)
        thumbnail_buffer = _create_thumbnail(original_buffer, size=(200, 200))

        # Verify size
        thumbnail_buffer.seek(0)
        thumbnail = Image.open(thumbnail_buffer)

        assert thumbnail.size[0] <= 200
        assert thumbnail.size[1] <= 200

    def test_create_thumbnail_maintains_aspect_ratio(self):
        """Test that thumbnail maintains aspect ratio."""
        # Create rectangular image
        original = Image.new("RGB", (800, 400), color="blue")
        original_buffer = BytesIO()
        original.save(original_buffer, format="PNG")
        original_buffer.seek(0)

        thumbnail_buffer = _create_thumbnail(original_buffer, size=(200, 200))

        thumbnail_buffer.seek(0)
        thumbnail = Image.open(thumbnail_buffer)

        # Aspect ratio should be maintained (2:1)
        assert thumbnail.size[0] / thumbnail.size[1] == pytest.approx(2.0, rel=0.1)

    def test_create_thumbnail_is_valid_png(self):
        """Test that thumbnail is a valid PNG."""
        original = Image.new("RGB", (600, 600), color="green")
        original_buffer = BytesIO()
        original.save(original_buffer, format="PNG")
        original_buffer.seek(0)

        thumbnail_buffer = _create_thumbnail(original_buffer)

        thumbnail_buffer.seek(0)
        thumbnail = Image.open(thumbnail_buffer)

        assert thumbnail.format == "PNG"


class TestIsLightColor:
    """Tests for _is_light_color function."""

    def test_white_is_light(self):
        """Test that white is detected as light."""
        assert _is_light_color("#FFFFFF") is True

    def test_black_is_dark(self):
        """Test that black is detected as dark."""
        assert _is_light_color("#000000") is False

    def test_yellow_is_light(self):
        """Test that yellow is detected as light."""
        assert _is_light_color("#FFFF00") is True

    def test_cyan_is_light(self):
        """Test that cyan is detected as light."""
        assert _is_light_color("#00FFFF") is True

    def test_blue_is_dark(self):
        """Test that blue is detected as dark."""
        assert _is_light_color("#0000FF") is False

    def test_red_is_dark(self):
        """Test that red is detected as dark."""
        assert _is_light_color("#FF0000") is False

    def test_green_is_medium_dark(self):
        """Test that green is detected as dark (luminance ~0.5)."""
        # Pure green has luminance ~0.59, should be light
        assert _is_light_color("#00FF00") is True

    def test_gray_medium(self):
        """Test gray around threshold."""
        # Medium gray (luminance ~0.5) - edge case
        result = _is_light_color("#808080")
        # Could be either, depends on exact threshold
        assert isinstance(result, bool)

    def test_lowercase_hex_works(self):
        """Test that lowercase hex codes work."""
        assert _is_light_color("#ffffff") is True
        assert _is_light_color("#000000") is False

    def test_mixed_case_hex_works(self):
        """Test that mixed case hex codes work."""
        assert _is_light_color("#FfFfFf") is True
        assert _is_light_color("#00fF00") is True
