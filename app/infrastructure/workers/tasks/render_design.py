"""Task: Render design preview."""

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from app.infrastructure.workers.celery_app import celery_app
from app.infrastructure.workers.logging_config import logger
from app.infrastructure.database.sync_session import get_sync_db_session
from app.infrastructure.database.repositories.sync_design_repo import SyncDesignRepository
from app.infrastructure.storage import get_storage_repository
from app.domain.entities.design import DesignStatus


@celery_app.task(bind=True, name="render_design_preview")
def render_design_preview(self, design_id: str) -> dict:
    """
    Render design preview image using PIL and upload to storage.
    
    Flow:
    1. Get design from database
    2. Mark as RENDERING
    3. Generate image using PIL (text on colored background)
    4. Upload preview to S3/local storage
    5. Generate thumbnail (resized version)
    6. Upload thumbnail to S3/local storage
    7. Mark as PUBLISHED with URLs
    
    Args:
        design_id: Design ID to render
    
    Returns:
        dict with status, preview_url, and thumbnail_url
    """
    logger.info(f"Starting render for design {design_id}")
    
    try:
        with get_sync_db_session() as session:
            repo = SyncDesignRepository(session)
            storage = get_storage_repository()
            
            # Get design
            design = repo.get_by_id(design_id)
            if design is None:
                raise ValueError(f"Design {design_id} not found")
            
            logger.debug(f"Design {design_id} found, current status: {design.status.value}")
            
            # Update status to rendering
            design.mark_rendering()
            repo.update(design)
            session.commit()
            logger.info(f"Design {design_id} marked as rendering")
            
            # Render image (PIL)
            logger.debug(f"Rendering image for design {design_id}")
            image_buffer = _render_image(design.design_data, design.product_type)
            
            # Upload preview to storage (S3 or local)
            image_buffer.seek(0)
            preview_url = storage.upload_design_preview(design_id, image_buffer)
            logger.info(f"Uploaded preview: {preview_url}")
            
            # Generate thumbnail (resized version)
            logger.debug(f"Generating thumbnail for design {design_id}")
            thumbnail_buffer = _create_thumbnail(image_buffer)
            
            # Upload thumbnail to storage
            thumbnail_buffer.seek(0)
            thumbnail_url = storage.upload_design_thumbnail(design_id, thumbnail_buffer)
            logger.info(f"Uploaded thumbnail: {thumbnail_url}")
            
            # Mark as published
            design.mark_published(preview_url, thumbnail_url)
            repo.update(design)
            session.commit()
            
            logger.info(f"Design {design_id} rendered and published successfully")
            
            return {
                "status": "success",
                "design_id": design_id,
                "preview_url": preview_url,
                "thumbnail_url": thumbnail_url
            }
    
    except Exception as e:
        logger.error(f"Render failed for design {design_id}: {e}", exc_info=True)
        
        # Mark design as failed
        try:
            with get_sync_db_session() as session:
                repo = SyncDesignRepository(session)
                design = repo.get_by_id(design_id)
                if design and design.status == DesignStatus.RENDERING:
                    logger.warning(f"Marking design {design_id} as failed: {e}")
                    design.mark_failed(str(e))
                    repo.update(design)
                    session.commit()
        except Exception as mark_error:
            logger.error(f"Failed to mark design as failed: {mark_error}")
        
        # Re-raise for Celery retry
        raise


def _render_image(design_data: dict, product_type: str) -> BytesIO:
    """
    Render design using PIL.
    
    MVP version: Simple text on colored background.
    Future: Add product mockup templates, advanced typography.
    
    Args:
        design_data: Design configuration (text, font, color, fontSize)
        product_type: Product type (t-shirt, mug, etc.)
    
    Returns:
        BytesIO: PNG image buffer
    """
    # Image dimensions (600x600 for MVP)
    width, height = 600, 600
    
    # Get background color
    bg_color = design_data.get('color', '#FFFFFF')
    
    # Create blank image
    image = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(image)
    
    # Load font
    font_size = design_data.get('fontSize', 48)
    try:
        # Try common Linux font paths
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows
        ]
        
        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                logger.debug(f"Loaded font: {font_path}")
                break
            except:
                continue
        
        if font is None:
            logger.warning("Could not load TrueType font, using default")
            font = ImageFont.load_default()
    except Exception as e:
        logger.warning(f"Font loading error: {e}, using default")
        font = ImageFont.load_default()
    
    # Get text
    text = design_data.get('text', 'Design')
    
    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) / 2
    y = (height - text_height) / 2
    
    # Choose contrasting text color
    text_color = '#000000' if _is_light_color(bg_color) else '#FFFFFF'
    
    # Draw text
    draw.text((x, y), text, fill=text_color, font=font)
    
    # Save to buffer
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    
    logger.debug(f"Rendered {width}x{height} image with text: '{text}'")
    
    return buffer


def _create_thumbnail(image_buffer: BytesIO, size: tuple = (200, 200)) -> BytesIO:
    """
    Create thumbnail from image.
    
    Args:
        image_buffer: Original image buffer
        size: Thumbnail dimensions (default: 200x200)
    
    Returns:
        BytesIO: Thumbnail image buffer
    """
    # Reset buffer position
    image_buffer.seek(0)
    
    # Open image
    image = Image.open(image_buffer)
    
    # Create thumbnail (maintains aspect ratio)
    image.thumbnail(size, Image.Resampling.LANCZOS)
    
    # Save to new buffer
    thumbnail_buffer = BytesIO()
    image.save(thumbnail_buffer, format='PNG')
    thumbnail_buffer.seek(0)
    
    logger.debug(f"Created thumbnail: {image.size}")
    
    return thumbnail_buffer


def _is_light_color(hex_color: str) -> bool:
    """
    Check if color is light (for text contrast).
    
    Uses relative luminance formula (ITU-R BT.709).
    
    Args:
        hex_color: Hex color string (#RRGGBB)
    
    Returns:
        bool: True if color is light (luminance > 0.5)
    """
    # Remove # prefix
    hex_color = hex_color.lstrip('#')
    
    # Convert to RGB
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Calculate relative luminance
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    
    return luminance > 0.5



