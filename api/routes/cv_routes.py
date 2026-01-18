"""
Computer Vision Model Integration Routes
Bridges the existing CV model with the database and API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import uuid
from datetime import datetime
import sys
import os

# Add parent directory to path to import CV model
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from planting_site_detector import PlantingSiteDetector
from agent.services.plant_database import DatabaseManager, PlantingSite
from agent.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class AnalysisRequest(BaseModel):
    """CV analysis request"""
    address: str = Field(..., min_length=3, description="Address to analyze")
    buffer_m: int = Field(100, ge=50, le=500, description="Analysis radius in meters")
    save_images: bool = Field(True, description="Save imagery to disk")


class PlantingSiteResponse(BaseModel):
    """Planting site information"""
    site_id: str
    location_lat: float
    location_lon: float
    avg_ndvi: float
    ndvi_category: str
    avg_slope: float
    slope_category: str
    area_sq_ft: int
    suitability_score: float
    has_nearby_roads: bool
    has_nearby_buildings: bool


class AnalysisResponse(BaseModel):
    """CV analysis response"""
    analysis_id: str
    address: str
    latitude: float
    longitude: float
    planting_sites: List[PlantingSiteResponse]
    existing_trees_count: int
    imagery_saved: bool
    timestamp: str


# Initialize database
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """Get database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(settings.database_url)
    return _db_manager


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_address(request: AnalysisRequest):
    """
    Run CV model analysis on an address

    **Process:**
    1. Geocode address to coordinates
    2. Fetch satellite imagery from Google Earth Engine
    3. Detect existing trees using DeepForest
    4. Calculate NDVI and slope
    5. Filter infrastructure using OpenStreetMap
    6. Identify optimal planting sites
    7. Store results in database

    **Request:**
    - `address`: Full address (e.g., "123 Main St, San Francisco, CA")
    - `buffer_m`: Analysis radius (50-500 meters, default: 100)
    - `save_images`: Save RGB/NDVI/slope images to disk

    **Response:**
    - Analysis ID and planting site recommendations
    """
    try:
        logger.info(f"Starting CV analysis for address: {request.address}")

        # Initialize CV detector
        detector = PlantingSiteDetector()

        # Run analysis
        result = detector.analyze_address(
            address=request.address,
            buffer_m=request.buffer_m
        )

        logger.info(f"CV analysis complete - found {len(result['planting_sites'])} sites")

        # Generate analysis ID
        analysis_id = str(uuid.uuid4())

        # Get database manager
        db_manager = get_db_manager()

        # Extract imagery metadata
        imagery = result['imagery']
        latitude = imagery['coordinates'][0]
        longitude = imagery['coordinates'][1]

        # Store planting sites in database
        site_responses = []

        for site_data in result['planting_sites']:
            # Generate site ID
            site_id = str(uuid.uuid4())

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

            # Estimate area in square feet (1 pixel ≈ 1m² ≈ 10.76 sq ft)
            area_sq_ft = int(site_data['area_pixels'] * 10.76)

            # Check for nearby infrastructure from OSM data
            osm_data = result.get('osm_data', {})
            has_nearby_roads = 'roads' in osm_data and len(osm_data['roads']) > 0
            has_nearby_buildings = 'buildings' in osm_data and len(osm_data['buildings']) > 0

            # Get site location (pixel coordinates)
            location_pixels = site_data['location']

            # Create PlantingSite record
            site_record = PlantingSite(
                site_id=site_id,
                analysis_id=analysis_id,
                address=result['address'],
                latitude=latitude,
                longitude=longitude,
                location_pixels={'x': int(location_pixels[0]), 'y': int(location_pixels[1])},
                avg_ndvi=round(avg_ndvi, 3),
                avg_slope=round(avg_slope, 2),
                area_pixels=int(site_data['area_pixels']),
                suitability_score=round(site_data['suitability_score'], 3),
                osm_data={
                    'roads': has_nearby_roads,
                    'buildings': has_nearby_buildings
                },
                rgb_image_path=imagery.get('rgb_path'),
                ndvi_image_path=imagery.get('ndvi_path'),
                slope_image_path=imagery.get('slope_path')
            )

            # Save to database
            async with db_manager.get_session() as session:
                session.add(site_record)
                await session.commit()
                await session.refresh(site_record)

            # Create response
            site_response = PlantingSiteResponse(
                site_id=site_id,
                location_lat=latitude,
                location_lon=longitude,
                avg_ndvi=round(avg_ndvi, 3),
                ndvi_category=ndvi_category,
                avg_slope=round(avg_slope, 2),
                slope_category=slope_category,
                area_sq_ft=area_sq_ft,
                suitability_score=round(site_data['suitability_score'], 3),
                has_nearby_roads=has_nearby_roads,
                has_nearby_buildings=has_nearby_buildings
            )

            site_responses.append(site_response)

        logger.info(f"Stored {len(site_responses)} sites in database")

        # Build response
        response = AnalysisResponse(
            analysis_id=analysis_id,
            address=result['address'],
            latitude=latitude,
            longitude=longitude,
            planting_sites=site_responses,
            existing_trees_count=len(result.get('existing_trees', [])),
            imagery_saved=request.save_images,
            timestamp=datetime.utcnow().isoformat()
        )

        return response

    except Exception as e:
        logger.error(f"CV analysis error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error running CV analysis: {str(e)}"
        )


@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """
    Get CV analysis results by ID

    Returns all planting sites for a specific analysis
    """
    try:
        db_manager = get_db_manager()

        async with db_manager.get_session() as session:
            from sqlalchemy import select

            # Query all sites for this analysis
            stmt = select(PlantingSite).where(PlantingSite.analysis_id == analysis_id)
            result = await session.execute(stmt)
            sites = result.scalars().all()

            if not sites:
                raise HTTPException(
                    status_code=404,
                    detail=f"No analysis found with ID: {analysis_id}"
                )

            # Format response
            site_responses = []
            for site in sites:
                site_responses.append({
                    'site_id': str(site.site_id),
                    'address': site.address,
                    'latitude': site.latitude,
                    'longitude': site.longitude,
                    'avg_ndvi': round(site.avg_ndvi, 3),
                    'avg_slope': round(site.avg_slope, 2),
                    'area_sq_ft': int(site.area_pixels * 10.76),
                    'suitability_score': round(site.suitability_score, 3)
                })

            return {
                'analysis_id': analysis_id,
                'address': sites[0].address,
                'latitude': sites[0].latitude,
                'longitude': sites[0].longitude,
                'planting_sites': site_responses,
                'total_sites': len(site_responses)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving analysis: {str(e)}"
        )
