"""Task: Render design preview."""

import time
from app.infrastructure.workers.celery_app import celery_app
from app.infrastructure.workers.logging_config import logger
from app.infrastructure.database.sync_session import get_sync_db_session
from app.infrastructure.database.repositories.sync_design_repo import SyncDesignRepository
from app.domain.entities.design import DesignStatus


@celery_app.task(bind=True, name="render_design_preview")
def render_design_preview(self, design_id: str) -> dict:
    """
    Render design preview image.
    
    MVP version: Just marks as published (no actual rendering yet).
    Full implementation will use PIL/Pillow to render text on mockup.
    
    Args:
        design_id: Design ID to render
    
    Returns:
        dict with status and preview_url
    """
    logger.info(f"Starting render for design {design_id}")
    
    try:
        with get_sync_db_session() as session:
            repo = SyncDesignRepository(session)
            
            # Get design
            design = repo.get_by_id(design_id)
            if design is None:
                raise ValueError(f"Design {design_id} not found")
            
            logger.debug(f"Design {design_id} found, marking as rendering")
            
            # Update status to rendering
            design.mark_rendering()
            repo.update(design)
            session.commit()
            
            # TODO: Actual rendering logic (PIL/Pillow)
            # For MVP, just simulate rendering delay
            logger.debug(f"Simulating render for design {design_id} (2s)")
            time.sleep(2)  # Simulate 2s render time
            
            # Generate mock preview URL (in real version, upload to S3)
            preview_url = f"https://cdn.customify.app/designs/{design_id}/preview.png"
            thumbnail_url = f"https://cdn.customify.app/designs/{design_id}/thumb.png"
            
            # Mark as published
            design.mark_published(preview_url, thumbnail_url)
            repo.update(design)
            session.commit()
            
            logger.info(f"Design {design_id} rendered successfully: {preview_url}")
            
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
                if design:
                    logger.warning(f"Marking design {design_id} as failed: {e}")
                    design.mark_failed(str(e))
                    repo.update(design)
                    session.commit()
        except Exception as mark_error:
            logger.error(f"Failed to mark design as failed: {mark_error}")
        
        # Re-raise for Celery retry
        raise


