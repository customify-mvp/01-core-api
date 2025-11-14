"""Task: Render design preview."""

import asyncio
from app.infrastructure.workers.celery_app import celery_app
from app.infrastructure.workers.logging_config import logger
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.database.repositories.design_repo_impl import DesignRepositoryImpl
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
        # Run async code in sync Celery task
        result = asyncio.run(_render_design_async(design_id))
        logger.info(f"Completed render for design {design_id}")
        return result
    except Exception as e:
        logger.error(f"Render failed for design {design_id}: {e}", exc_info=True)
        
        # Mark design as failed
        asyncio.run(_mark_design_failed(design_id, str(e)))
        
        # Re-raise for Celery retry
        raise


async def _render_design_async(design_id: str) -> dict:
    """Async implementation of render logic."""
    async with AsyncSessionLocal() as session:
        repo = DesignRepositoryImpl(session)
        
        # Get design
        design = await repo.get_by_id(design_id)
        if design is None:
            raise ValueError(f"Design {design_id} not found")
        
        logger.debug(f"Design {design_id} found, marking as rendering")
        
        # Update status to rendering
        design.mark_rendering()
        await repo.update(design)
        await session.commit()
        
        # TODO: Actual rendering logic (PIL/Pillow)
        # For MVP, just simulate rendering delay
        logger.debug(f"Simulating render for design {design_id} (2s)")
        await asyncio.sleep(2)  # Simulate 2s render time
        
        # Generate mock preview URL (in real version, upload to S3)
        preview_url = f"https://cdn.customify.app/designs/{design_id}/preview.png"
        thumbnail_url = f"https://cdn.customify.app/designs/{design_id}/thumb.png"
        
        # Mark as published
        design.mark_published(preview_url, thumbnail_url)
        await repo.update(design)
        await session.commit()
        
        logger.info(f"Design {design_id} rendered successfully: {preview_url}")
        
        return {
            "status": "success",
            "design_id": design_id,
            "preview_url": preview_url,
            "thumbnail_url": thumbnail_url
        }


async def _mark_design_failed(design_id: str, error_message: str):
    """Mark design as failed."""
    async with AsyncSessionLocal() as session:
        repo = DesignRepositoryImpl(session)
        design = await repo.get_by_id(design_id)
        if design:
            logger.warning(f"Marking design {design_id} as failed: {error_message}")
            design.mark_failed(error_message)
            await repo.update(design)
            await session.commit()

