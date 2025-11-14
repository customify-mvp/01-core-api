"""
Storage Layer Validation Script

Tests the storage implementation (local or S3) without needing the full API.
"""

import sys
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Add app to path
sys.path.insert(0, os.path.abspath('.'))

from app.config import settings
from app.infrastructure.storage import get_storage_repository


def create_test_image(text: str = "Storage Test", color: str = "#FF0000") -> BytesIO:
    """Create a test image using PIL."""
    # Create 600x600 image
    image = Image.new('RGB', (600, 600), color=color)
    draw = ImageDraw.Draw(image)
    
    # Try to load a font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except:
        font = ImageFont.load_default()
    
    # Draw text (centered)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (600 - text_width) / 2
    y = (600 - text_height) / 2
    
    draw.text((x, y), text, fill='#FFFFFF', font=font)
    
    # Save to buffer
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer


def test_storage():
    """Test storage implementation."""
    print("=" * 60)
    print("STORAGE LAYER VALIDATION")
    print("=" * 60)
    print()
    
    # Check configuration
    print("Configuration:")
    print(f"  USE_LOCAL_STORAGE: {settings.USE_LOCAL_STORAGE}")
    print(f"  AWS_REGION: {settings.AWS_REGION}")
    print(f"  S3_BUCKET_NAME: {settings.S3_BUCKET_NAME}")
    print(f"  S3_PUBLIC_BUCKET: {settings.S3_PUBLIC_BUCKET}")
    print(f"  CLOUDFRONT_DOMAIN: {settings.CLOUDFRONT_DOMAIN or '(not set)'}")
    print()
    
    # Get storage repository
    print("Getting storage repository...")
    storage = get_storage_repository()
    print(f"  Using: {storage.__class__.__name__}")
    print()
    
    # Test design ID
    test_design_id = "test-design-12345"
    
    try:
        # Create test image
        print("Creating test image...")
        image_buffer = create_test_image("Storage Test", "#FF0000")
        print("  ✅ Image created (600x600)")
        print()
        
        # Upload preview
        print("Uploading preview...")
        image_buffer.seek(0)
        preview_url = storage.upload_design_preview(test_design_id, image_buffer)
        print(f"  ✅ Preview uploaded")
        print(f"  URL: {preview_url}")
        print()
        
        # Create thumbnail
        print("Creating thumbnail...")
        image_buffer.seek(0)
        image = Image.open(image_buffer)
        image.thumbnail((200, 200), Image.Resampling.LANCZOS)
        
        thumbnail_buffer = BytesIO()
        image.save(thumbnail_buffer, format='PNG')
        thumbnail_buffer.seek(0)
        print("  ✅ Thumbnail created (200x200)")
        print()
        
        # Upload thumbnail
        print("Uploading thumbnail...")
        thumbnail_url = storage.upload_design_thumbnail(test_design_id, thumbnail_buffer)
        print(f"  ✅ Thumbnail uploaded")
        print(f"  URL: {thumbnail_url}")
        print()
        
        # Delete assets
        print("Cleaning up...")
        deleted = storage.delete_design_assets(test_design_id)
        if deleted:
            print("  ✅ Assets deleted")
        else:
            print("  ⚠️  Assets deletion returned False")
        print()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_storage()
