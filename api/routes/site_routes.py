"""
Planting Site Data Routes
Provides site information and photo upload
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import base64
from pathlib import Path
import uuid

from sqlalchemy import select
from agent.services.plant_database import DatabaseManager, PlantingSite, UploadedPhoto
from agent.services.site_data_loader import SiteDataLoader
from agent.tools.photo_analyzer import PhotoAnalyzerTool
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


class PhotoUploadResponse(BaseModel):
    """Photo upload and analysis response"""
    photo_id: str
    site_id: str
    analysis: Dict[str, Any]
    file_path: str


# Initialize services
_db_manager = None
_site_loader = None
_photo_analyzer = None


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


def get_photo_analyzer() -> PhotoAnalyzerTool:
    """Get photo analyzer instance"""
    global _photo_analyzer
    if _photo_analyzer is None:
        _photo_analyzer = PhotoAnalyzerTool()
    return _photo_analyzer


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


@router.post("/{site_id}/photo", response_model=PhotoUploadResponse)
async def upload_photo(
    site_id: str,
    file: UploadFile = File(..., description="Photo file (JPEG/PNG)"),
    question: Optional[str] = Form(None, description="Specific question about the site")
):
    """
    Upload and analyze site photo

    **Path Parameters:**
    - `site_id`: Site identifier

    **Form Data:**
    - `file`: Image file (JPEG or PNG, max 10MB)
    - `question`: Optional specific question about the site

    **Returns:** Photo analysis results from Claude Vision
    """
    try:
        # Validate file type
        if file.content_type not in ['image/jpeg', 'image/png', 'image/jpg']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Must be JPEG or PNG"
            )

        # Read file
        file_content = await file.read()

        # Check file size (max 10MB)
        max_size_mb = settings.max_upload_size_mb if hasattr(settings, 'max_upload_size_mb') else 10
        if len(file_content) > max_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {max_size_mb}MB"
            )

        # Convert to base64
        image_base64 = base64.b64encode(file_content).decode('utf-8')

        logger.info(f"Analyzing photo for site: {site_id}, size: {len(file_content)} bytes")

        # Analyze photo using photo analyzer tool
        photo_analyzer = get_photo_analyzer()

        analysis_result = await photo_analyzer.run(
            image_base64=image_base64,
            question=question or "Analyze this planting site"
        )

        # Save photo to disk
        upload_dir = Path(settings.upload_dir if hasattr(settings, 'upload_dir') else 'uploads')
        upload_dir.mkdir(exist_ok=True)

        photo_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        file_path = upload_dir / f"{site_id}_{photo_id}.{file_extension}"

        with open(file_path, 'wb') as f:
            f.write(file_content)

        logger.info(f"Photo saved to: {file_path}")

        # Save photo record to database
        db_manager = get_db_manager()

        async with db_manager.get_session() as session:
            photo_record = UploadedPhoto(
                photo_id=photo_id,
                site_id=site_id,
                file_path=str(file_path),
                analysis_result=analysis_result
            )
            session.add(photo_record)
            await session.commit()

        return PhotoUploadResponse(
            photo_id=photo_id,
            site_id=site_id,
            analysis=analysis_result,
            file_path=str(file_path)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading photo: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading photo: {str(e)}"
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
