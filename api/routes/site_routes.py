"""
Planting Site Data Routes
Provides site information and photo upload
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from sqlalchemy import select
from agent.services.plant_database import DatabaseManager, PlantingSite, UploadedPhoto
from agent.services.site_data_loader import SiteDataLoader
from agent.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class SiteDetailResponse(BaseModel):
    """Planting site details"""
    site_id: str
    address: str
    latitude: float
    longitude: float
    avg_ndvi: float
    ndvi_category: str
    avg_slope: float
    slope_category: str
    area_sq_ft: int
    suitability_score: float
    recommended_max_height_ft: int
    recommended_max_spread_ft: int
    has_nearby_roads: bool
    has_nearby_buildings: bool
    osm_data: Optional[Dict[str, Any]]


# Initialize services
_db_manager = None
_site_loader = None
def get_db_manager() -> DatabaseManager:
    """Get database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(settings.database_url)
    return _db_manager


def get_site_loader() -> SiteDataLoader:
    """Get site data loader instance"""
    global _site_loader
    if _site_loader is None:
        _site_loader = SiteDataLoader(get_db_manager())
    return _site_loader


@router.get("/{site_id}", response_model=SiteDetailResponse)
async def get_site(site_id: str):
    """
    Get planting site details by ID

    **Path Parameters:**
    - `site_id`: Site identifier (UUID)

    **Returns:** Detailed site information with recommendations
    """
    try:
        site_loader = get_site_loader()

        # Load site data
        site_data = await site_loader.load_site_data(site_id)

        if not site_data:
            raise HTTPException(
                status_code=404,
                detail=f"Site not found: {site_id}"
            )

        # Categorize NDVI
        avg_ndvi = site_data['avg_ndvi']
        if avg_ndvi < 0.1:
            ndvi_category = 'bare_soil_or_pavement'
        elif avg_ndvi < 0.3:
            ndvi_category = 'sparse_vegetation'
        elif avg_ndvi < 0.6:
            ndvi_category = 'moderate_vegetation'
        else:
            ndvi_category = 'dense_vegetation'

        # Categorize slope
        avg_slope = site_data['avg_slope']
        if avg_slope < 5:
            slope_category = 'flat'
        elif avg_slope < 10:
            slope_category = 'gentle'
        elif avg_slope < 15:
            slope_category = 'moderate'
        else:
            slope_category = 'steep'

        # Calculate recommended tree size
        tree_size = site_loader.calculate_recommended_tree_size(site_data)

        return SiteDetailResponse(
            site_id=site_data['site_id'],
            address=site_data.get('address', 'Unknown'),
            latitude=site_data.get('latitude', 0.0),
            longitude=site_data.get('longitude', 0.0),
            avg_ndvi=round(avg_ndvi, 3),
            ndvi_category=ndvi_category,
            avg_slope=round(avg_slope, 2),
            slope_category=slope_category,
            area_sq_ft=site_data['area_sq_ft'],
            suitability_score=site_data.get('suitability_score', 0.5),
            recommended_max_height_ft=tree_size['max_height_ft'],
            recommended_max_spread_ft=tree_size['max_spread_ft'],
            has_nearby_roads=site_data.get('has_nearby_roads', False),
            has_nearby_buildings=site_data.get('has_nearby_buildings', False),
            osm_data=site_data.get('osm_data')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving site: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving site: {str(e)}"
        )


@router.get("/{site_id}/photos")
async def get_site_photos(site_id: str):
    """
    Get all photos for a site

    **Path Parameters:**
    - `site_id`: Site identifier

    **Returns:** List of photos and analyses
    """
    try:
        db_manager = get_db_manager()

        async with db_manager.get_session() as session:
            stmt = select(UploadedPhoto).where(UploadedPhoto.site_id == site_id)
            result = await session.execute(stmt)
            photos = result.scalars().all()

            return {
                'site_id': site_id,
                'photos': [
                    {
                        'photo_id': str(photo.photo_id),
                        'file_path': photo.file_path,
                        'analysis': photo.analysis_result,
                        'uploaded_at': photo.uploaded_at.isoformat()
                    }
                    for photo in photos
                ]
            }

    except Exception as e:
        logger.error(f"Error retrieving photos: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving photos: {str(e)}"
        )
