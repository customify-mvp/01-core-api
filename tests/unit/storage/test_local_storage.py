"""Unit tests for local storage repository."""

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from app.infrastructure.storage.local_storage import LocalStorageRepository


@pytest.fixture
def temp_storage(tmp_path):
    """
    Create temporary storage directory for testing.

    Args:
        tmp_path: pytest temporary directory fixture

    Returns:
        LocalStorageRepository instance with temp directory
    """
    storage = LocalStorageRepository(base_path=str(tmp_path))
    return storage


class TestLocalStorageRepository:
    """Tests for LocalStorageRepository."""

    def test_upload_design_preview_creates_file(self, temp_storage):
        """Test uploading design preview creates file."""
        # Create fake image
        image = Image.new("RGB", (600, 600), color="red")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        # Upload
        url = temp_storage.upload_design_preview("test-design-id", buffer)

        # Verify URL format
        assert "test-design-id" in url
        assert "preview.png" in url
        assert url.startswith("http://localhost:8000/static/")

        # Check file exists
        file_path = Path(temp_storage.base_path) / "designs" / "test-design-id" / "preview.png"
        assert file_path.exists()
        assert file_path.is_file()

    def test_upload_design_preview_creates_directory(self, temp_storage):
        """Test that upload creates necessary directories."""
        image = Image.new("RGB", (100, 100), color="blue")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        temp_storage.upload_design_preview("new-design-id", buffer)

        # Check directory structure
        design_dir = Path(temp_storage.base_path) / "designs" / "new-design-id"
        assert design_dir.exists()
        assert design_dir.is_dir()

    def test_upload_design_thumbnail_creates_file(self, temp_storage):
        """Test uploading thumbnail creates file."""
        image = Image.new("RGB", (200, 200), color="green")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        url = temp_storage.upload_design_thumbnail("test-thumb-id", buffer)

        assert "thumbnail.png" in url

        file_path = Path(temp_storage.base_path) / "designs" / "test-thumb-id" / "thumbnail.png"
        assert file_path.exists()

    def test_upload_multiple_files_same_design(self, temp_storage):
        """Test uploading both preview and thumbnail for same design."""
        design_id = "multi-file-design"

        # Upload preview
        preview_image = Image.new("RGB", (600, 600), color="yellow")
        preview_buffer = BytesIO()
        preview_image.save(preview_buffer, format="PNG")
        preview_buffer.seek(0)

        preview_url = temp_storage.upload_design_preview(design_id, preview_buffer)

        # Upload thumbnail
        thumb_image = Image.new("RGB", (200, 200), color="cyan")
        thumb_buffer = BytesIO()
        thumb_image.save(thumb_buffer, format="PNG")
        thumb_buffer.seek(0)

        thumb_url = temp_storage.upload_design_thumbnail(design_id, thumb_buffer)

        # Both should exist
        design_dir = Path(temp_storage.base_path) / "designs" / design_id
        assert (design_dir / "preview.png").exists()
        assert (design_dir / "thumbnail.png").exists()

        assert preview_url != thumb_url

    def test_delete_design_assets_removes_files(self, temp_storage):
        """Test deleting design assets removes all files."""
        design_id = "delete-test-id"

        # Create files first
        image = Image.new("RGB", (100, 100), color="magenta")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        temp_storage.upload_design_preview(design_id, buffer)

        buffer.seek(0)
        temp_storage.upload_design_thumbnail(design_id, buffer)

        # Verify files exist
        design_dir = Path(temp_storage.base_path) / "designs" / design_id
        assert design_dir.exists()
        assert (design_dir / "preview.png").exists()
        assert (design_dir / "thumbnail.png").exists()

        # Delete
        result = temp_storage.delete_design_assets(design_id)

        assert result is True

        # Verify deleted
        assert not design_dir.exists()

    def test_delete_nonexistent_design_returns_false(self, temp_storage):
        """Test deleting design that doesn't exist returns False."""
        result = temp_storage.delete_design_assets("nonexistent-design-id")

        assert result is False

    def test_upload_overwrites_existing_file(self, temp_storage):
        """Test uploading to same ID overwrites existing file."""
        design_id = "overwrite-test"

        # Upload first image (red)
        image1 = Image.new("RGB", (100, 100), color="red")
        buffer1 = BytesIO()
        image1.save(buffer1, format="PNG")
        buffer1.seek(0)

        temp_storage.upload_design_preview(design_id, buffer1)

        # Upload second image (blue) with same ID
        image2 = Image.new("RGB", (100, 100), color="blue")
        buffer2 = BytesIO()
        image2.save(buffer2, format="PNG")
        buffer2.seek(0)

        temp_storage.upload_design_preview(design_id, buffer2)

        # Verify file was overwritten (should be blue now)
        file_path = Path(temp_storage.base_path) / "designs" / design_id / "preview.png"
        assert file_path.exists()

        # Open and check color
        with Image.open(file_path) as img:
            pixel = img.getpixel((50, 50))
            assert pixel == (0, 0, 255)  # Blue

    def test_base_path_is_customizable(self, tmp_path):
        """Test that base path can be customized."""
        custom_path = tmp_path / "custom_storage"
        storage = LocalStorageRepository(base_path=str(custom_path))

        assert storage.base_path == custom_path
        assert custom_path.exists()
        assert custom_path.is_dir()

    def test_url_format_is_consistent(self, temp_storage):
        """Test that generated URLs follow consistent format."""
        design_id = "url-format-test"

        image = Image.new("RGB", (100, 100), color="white")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        preview_url = temp_storage.upload_design_preview(design_id, buffer)

        buffer.seek(0)
        thumbnail_url = temp_storage.upload_design_thumbnail(design_id, buffer)

        # Both should start with same base
        assert preview_url.startswith("http://localhost:8000/static/designs/")
        assert thumbnail_url.startswith("http://localhost:8000/static/designs/")

        # Both should contain design_id
        assert design_id in preview_url
        assert design_id in thumbnail_url
