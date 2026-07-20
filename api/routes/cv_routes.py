"""
Computer Vision Model Integration Routes
Bridges the existing CV model with the database and API
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import uuid
import json
import asyncio
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from planting_site_detector import PlantingSiteDetector
from agent.services.plant_database import DatabaseManager, PlantingSite
from agent.services.cache_service import CacheService
from agent.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

_db_manager: Optional[DatabaseManager] = None
_cache_service: Optional[CacheService] = None

JOB_TTL_SECONDS = 3600


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class AnalysisRequest(BaseModel):
    address: str = Field(..., min_length=3, description="Street address to analyze")
    latitude: Optional[float] = Field(None, description="Pre-geocoded latitude from Mapbox. Skips Nominatim when provided.")
    longitude: Optional[float] = Field(None, description="Pre-geocoded longitude from Mapbox. Skips Nominatim when provided.")
    buffer_m: int = Field(100, ge=50, le=500, description="Analysis radius in meters")
    save_images: bool = Field(True)


class JobSubmitResponse(BaseModel):
    job_id: str
    status: str = "pending"
    message: str = "Analysis queued. Poll /cv/jobs/{job_id} for results."


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # pending | running | complete | error
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class PlantingSiteResponse(BaseModel):
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


class ExistingTreeResponse(BaseModel):
    lat: float
    lon: float
    confidence: float
    bbox_width: int
    bbox_height: int


class AnalysisResponse(BaseModel):
    analysis_id: str
    address: str
    latitude: float
    longitude: float
    planting_sites: List[PlantingSiteResponse]
    existing_trees: List[ExistingTreeResponse]
    existing_trees_count: int
    imagery_saved: bool
    timestamp: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(settings.database_url)
    return _db_manager


async def get_cache() -> Optional[CacheService]:
    global _cache_service
    if _cache_service is None:
        try:
            svc = CacheService(settings.redis_url)
            await svc.connect()
            _cache_service = svc
        except Exception:
            logger.warning("Redis unavailable — job status stored in memory only")
    return _cache_service


# In-memory fallback for job status when Redis is unavailable
_memory_jobs: Dict[str, dict] = {}


async def _set_job(job_id: str, payload: dict):
    cache = await get_cache()
    if cache:
        await cache.set(f"job:{job_id}", json.dumps(payload), ttl=JOB_TTL_SECONDS)
    else:
        _memory_jobs[job_id] = payload


async def _get_job(job_id: str) -> Optional[dict]:
    cache = await get_cache()
    if cache:
        raw = await cache.get(f"job:{job_id}")
        return json.loads(raw) if raw else None
    return _memory_jobs.get(job_id)


def _ndvi_category(v: float) -> str:
    if v < 0.1:
        return "bare_soil_or_pavement"
    if v < 0.3:
        return "sparse_vegetation"
    if v < 0.6:
        return "moderate_vegetation"
    return "dense_vegetation"


def _slope_category(v: float) -> str:
    if v < 5:
        return "flat"
    if v < 10:
        return "gentle"
    if v < 15:
        return "moderate"
    return "steep"


# ---------------------------------------------------------------------------
# Background job
# ---------------------------------------------------------------------------

async def _run_analysis_job(job_id: str, request: AnalysisRequest):
    """Run the full CV pipeline as a background task and persist results."""
    await _set_job(job_id, {"status": "running", "message": "Downloading satellite imagery and running analysis…"})

    try:
        detector = PlantingSiteDetector()

        coords = None
        if request.latitude is not None and request.longitude is not None:
            coords = (request.latitude, request.longitude)

        # Run the blocking CV pipeline in a thread so we don't block the event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: detector.analyze_address(
                address=request.address,
                buffer_m=request.buffer_m,
                coords=coords,
            )
        )

        if result is None:
            await _set_job(job_id, {
                "status": "error",
                "message": "Analysis failed — could not geocode the address or download imagery.",
            })
            return

        analysis_id = str(uuid.uuid4())
        imagery = result["imagery"]
        center_lat = imagery["coordinates"][0]
        center_lon = imagery["coordinates"][1]

        sq_feet_per_pixel = ((2 * request.buffer_m / 512) ** 2) * 10.76

        db_manager = get_db_manager()
        site_responses = []
        osm_data = result.get("osm_data", {})
        has_nearby_roads = bool(osm_data.get("roads") and len(osm_data["roads"]) > 0)
        has_nearby_buildings = bool(osm_data.get("buildings") and len(osm_data["buildings"]) > 0)

        for site_data in result["planting_sites"]:
            site_id = str(uuid.uuid4())
            avg_ndvi = site_data["avg_ndvi"]
            avg_slope = site_data["avg_slope"]
            area_sq_ft = int(site_data["area_pixels"] * sq_feet_per_pixel)
            location_pixels = site_data["location"]

            site_record = PlantingSite(
                site_id=site_id,
                analysis_id=analysis_id,
                address=result["address"],
                latitude=center_lat,
                longitude=center_lon,
                location_pixels={"x": int(location_pixels[0]), "y": int(location_pixels[1])},
                avg_ndvi=round(avg_ndvi, 3),
                avg_slope=round(avg_slope, 2),
                area_pixels=int(site_data["area_pixels"]),
                suitability_score=round(site_data["suitability_score"], 3),
                osm_data={"roads": has_nearby_roads, "buildings": has_nearby_buildings},
                rgb_image_path=imagery.get("rgb_path"),
                ndvi_image_path=imagery.get("ndvi_path"),
                slope_image_path=imagery.get("slope_path"),
            )

            async with db_manager.get_session() as session:
                session.add(site_record)
                await session.commit()

            site_responses.append({
                "site_id": site_id,
                "location_lat": site_data.get("location_lat", center_lat),
                "location_lon": site_data.get("location_lon", center_lon),
                "avg_ndvi": round(avg_ndvi, 3),
                "ndvi_category": _ndvi_category(avg_ndvi),
                "avg_slope": round(avg_slope, 2),
                "slope_category": _slope_category(avg_slope),
                "area_sq_ft": area_sq_ft,
                "suitability_score": round(site_data["suitability_score"], 3),
                "has_nearby_roads": has_nearby_roads,
                "has_nearby_buildings": has_nearby_buildings,
            })

        trees = [
            {
                "lat": t["lat"], "lon": t["lon"],
                "confidence": t["confidence"],
                "bbox_width": t.get("bbox_width", 0),
                "bbox_height": t.get("bbox_height", 0),
            }
            for t in result.get("existing_trees", [])
        ]

        final = {
            "analysis_id": analysis_id,
            "address": result["address"],
            "latitude": center_lat,
            "longitude": center_lon,
            "planting_sites": site_responses,
            "existing_trees": trees,
            "existing_trees_count": result.get("existing_trees_count", len(trees)),
            "imagery_saved": request.save_images,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await _set_job(job_id, {"status": "complete", "message": f"Found {len(site_responses)} planting sites.", "result": final})
        logger.info(f"[job {job_id}] complete — {len(site_responses)} sites stored")

    except Exception as e:
        logger.error(f"[job {job_id}] failed: {e}", exc_info=True)
        await _set_job(job_id, {"status": "error", "message": str(e)})


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/analyze", response_model=JobSubmitResponse)
async def analyze_address(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Start a CV analysis for an address (async).

    Returns a `job_id` immediately. Poll `GET /cv/jobs/{job_id}` every 3 seconds
    until `status` is `complete` or `error`.

    Pass `latitude`/`longitude` from a Mapbox geocoding call to get accurate
    results — this bypasses the Nominatim fallback geocoder.
    """
    job_id = str(uuid.uuid4())
    await _set_job(job_id, {"status": "pending", "message": "Queued"})
    background_tasks.add_task(_run_analysis_job, job_id, request)
    return JobSubmitResponse(job_id=job_id)


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Poll the status of an async CV analysis job.

    `status` values:
    - `pending` — queued, not yet started
    - `running` — analysis in progress (typically 60–120 s)
    - `complete` — finished; `result` contains the full analysis
    - `error` — failed; `message` explains why
    """
    payload = await _get_job(job_id)
    if payload is None:
        raise HTTPException(status_code=404, detail=f"No job found with ID: {job_id}")
    return JobStatusResponse(job_id=job_id, **payload)


@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get stored CV analysis results by analysis ID."""
    try:
        db_manager = get_db_manager()

        async with db_manager.get_session() as session:
            from sqlalchemy import select
            stmt = select(PlantingSite).where(PlantingSite.analysis_id == analysis_id)
            result = await session.execute(stmt)
            sites = result.scalars().all()

            if not sites:
                raise HTTPException(status_code=404, detail=f"No analysis found with ID: {analysis_id}")

            sq_feet_per_pixel = ((2 * 100 / 512) ** 2) * 10.76  # assumes default 100m buffer

            return {
                "analysis_id": analysis_id,
                "address": sites[0].address,
                "latitude": sites[0].latitude,
                "longitude": sites[0].longitude,
                "planting_sites": [
                    {
                        "site_id": str(s.site_id),
                        "address": s.address,
                        "latitude": s.latitude,
                        "longitude": s.longitude,
                        "avg_ndvi": round(s.avg_ndvi, 3),
                        "avg_slope": round(s.avg_slope, 2),
                        "area_sq_ft": int(s.area_pixels * sq_feet_per_pixel),
                        "suitability_score": round(s.suitability_score, 3),
                    }
                    for s in sites
                ],
                "total_sites": len(sites),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving analysis: {str(e)}")
