"""
Plant Species Database Routes
Provides species search and details
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from sqlalchemy import select, or_, and_
from agent.services.plant_database import DatabaseManager, PlantSpecies
from agent.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class SpeciesSearchParams(BaseModel):
    """Species search parameters"""
    query: Optional[str] = Field(None, description="Search by name")
    hardiness_zone: Optional[int] = Field(None, ge=1, le=13, description="USDA hardiness zone")
    tree_type: Optional[str] = Field(None, description="Tree type: deciduous, evergreen, conifer")
    purpose: Optional[str] = Field(None, description="Purpose: shade, privacy, wildlife, aesthetic, stormwater")
    native_only: bool = Field(False, description="Native species only")
    drought_tolerant: Optional[bool] = Field(None, description="Drought tolerant species")
    max_height_ft: Optional[int] = Field(None, description="Maximum mature height in feet")
    limit: int = Field(20, ge=1, le=100, description="Maximum results")


class SpeciesResponse(BaseModel):
    """Species information response"""
    species_id: str
    common_name: str
    scientific_name: str
    tree_type: str
    mature_height_ft: int
    mature_spread_ft: int
    hardiness_zone_min: int
    hardiness_zone_max: int
    drought_tolerant: bool
    native_regions: Optional[List[str]]
    co2_sequestration_kg_year: float
    stormwater_interception_gal_year: float
    air_pollution_removal_kg_year: float
    price_6ft: Optional[float]


class SpeciesDetailResponse(SpeciesResponse):
    """Detailed species information"""
    growth_rate: str
    sunlight_requirements: str
    moisture_tolerance: str
    soil_types: List[str]
    maintenance_level: str
    maintenance_notes: Optional[Dict[str, Any]]
    created_at: str


# Initialize database
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """Get database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(settings.database_url)
    return _db_manager


@router.get("/search", response_model=List[SpeciesResponse])
async def search_species(
    query: Optional[str] = Query(None, description="Search by name"),
    hardiness_zone: Optional[int] = Query(None, ge=1, le=13),
    tree_type: Optional[str] = Query(None),
    purpose: Optional[str] = Query(None),
    native_only: bool = Query(False),
    drought_tolerant: Optional[bool] = Query(None),
    max_height_ft: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Search plant species database

    **Query Parameters:**
    - `query`: Search by common or scientific name
    - `hardiness_zone`: Filter by USDA hardiness zone (1-13)
    - `tree_type`: Filter by type (deciduous, evergreen, conifer)
    - `purpose`: Filter by purpose (shade, privacy, wildlife, aesthetic, stormwater)
    - `native_only`: Only native species
    - `drought_tolerant`: Filter drought-tolerant species
    - `max_height_ft`: Maximum mature height
    - `limit`: Maximum results (default: 20, max: 100)

    **Returns:** List of matching species
    """
    try:
        db_manager = get_db_manager()

        async with db_manager.get_session() as session:
            # Build query
            stmt = select(PlantSpecies)

            # Apply filters
            filters = []

            # Name search
            if query:
                filters.append(
                    or_(
                        PlantSpecies.common_name.ilike(f'%{query}%'),
                        PlantSpecies.scientific_name.ilike(f'%{query}%')
                    )
                )

            # Hardiness zone
            if hardiness_zone is not None:
                filters.append(
                    and_(
                        PlantSpecies.hardiness_zone_min <= hardiness_zone,
                        PlantSpecies.hardiness_zone_max >= hardiness_zone
                    )
                )

            # Tree type
            if tree_type:
                filters.append(PlantSpecies.tree_type == tree_type)

            # Drought tolerant
            if drought_tolerant is not None:
                filters.append(PlantSpecies.drought_tolerant == drought_tolerant)

            # Max height
            if max_height_ft:
                filters.append(PlantSpecies.mature_height_ft <= max_height_ft)

            # Native only
            if native_only:
                filters.append(PlantSpecies.native_regions.isnot(None))

            # Apply all filters
            if filters:
                stmt = stmt.where(and_(*filters))

            # Limit results
            stmt = stmt.limit(limit)

            # Execute query
            result = await session.execute(stmt)
            species_list = result.scalars().all()

            # Format response
            return [
                SpeciesResponse(
                    species_id=species.species_id,
                    common_name=species.common_name,
                    scientific_name=species.scientific_name,
                    tree_type=species.tree_type,
                    mature_height_ft=species.mature_height_ft,
                    mature_spread_ft=species.mature_spread_ft,
                    hardiness_zone_min=species.hardiness_zone_min,
                    hardiness_zone_max=species.hardiness_zone_max,
                    drought_tolerant=species.drought_tolerant,
                    native_regions=species.native_regions,
                    co2_sequestration_kg_year=species.co2_sequestration_kg_year,
                    stormwater_interception_gal_year=species.stormwater_interception_gal_year,
                    air_pollution_removal_kg_year=species.air_pollution_removal_kg_year,
                    price_6ft=species.price_6ft
                )
                for species in species_list
            ]

    except Exception as e:
        logger.error(f"Species search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error searching species: {str(e)}"
        )


@router.get("/{species_id}", response_model=SpeciesDetailResponse)
async def get_species(species_id: str):
    """
    Get detailed species information by ID

    **Path Parameters:**
    - `species_id`: Species identifier (e.g., "PLOC" for American Sycamore)

    **Returns:** Detailed species information
    """
    try:
        db_manager = get_db_manager()

        async with db_manager.get_session() as session:
            stmt = select(PlantSpecies).where(PlantSpecies.species_id == species_id)
            result = await session.execute(stmt)
            species = result.scalar_one_or_none()

            if not species:
                raise HTTPException(
                    status_code=404,
                    detail=f"Species not found: {species_id}"
                )

            return SpeciesDetailResponse(
                species_id=species.species_id,
                common_name=species.common_name,
                scientific_name=species.scientific_name,
                tree_type=species.tree_type,
                mature_height_ft=species.mature_height_ft,
                mature_spread_ft=species.mature_spread_ft,
                hardiness_zone_min=species.hardiness_zone_min,
                hardiness_zone_max=species.hardiness_zone_max,
                drought_tolerant=species.drought_tolerant,
                native_regions=species.native_regions,
                co2_sequestration_kg_year=species.co2_sequestration_kg_year,
                stormwater_interception_gal_year=species.stormwater_interception_gal_year,
                air_pollution_removal_kg_year=species.air_pollution_removal_kg_year,
                price_6ft=species.price_6ft,
                growth_rate=species.growth_rate,
                sunlight_requirements=species.sunlight_requirements,
                moisture_tolerance=species.moisture_tolerance,
                soil_types=species.soil_types,
                maintenance_level=species.maintenance_level,
                maintenance_notes=species.maintenance_notes,
                created_at=species.created_at.isoformat()
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving species: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving species: {str(e)}"
        )


@router.get("/")
async def list_all_species(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """
    List all species with pagination

    **Query Parameters:**
    - `limit`: Results per page (default: 50, max: 200)
    - `offset`: Number of results to skip (default: 0)

    **Returns:** Paginated species list
    """
    try:
        db_manager = get_db_manager()

        async with db_manager.get_session() as session:
            # Get total count
            from sqlalchemy import func
            count_stmt = select(func.count()).select_from(PlantSpecies)
            total_result = await session.execute(count_stmt)
            total_count = total_result.scalar()

            # Get paginated results
            stmt = select(PlantSpecies).offset(offset).limit(limit)
            result = await session.execute(stmt)
            species_list = result.scalars().all()

            return {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'species': [
                    {
                        'species_id': s.species_id,
                        'common_name': s.common_name,
                        'scientific_name': s.scientific_name,
                        'tree_type': s.tree_type
                    }
                    for s in species_list
                ]
            }

    except Exception as e:
        logger.error(f"Error listing species: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing species: {str(e)}"
        )
