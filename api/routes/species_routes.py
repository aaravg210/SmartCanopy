"""
Plant Species Database Routes
Provides species search and details
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from sqlalchemy import select, or_, and_, cast, String
from agent.services.plant_database import DatabaseManager, PlantSpecies
from agent.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class SpeciesResponse(BaseModel):
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
    growth_rate: Optional[str]
    sunlight_requirements: Optional[str]
    moisture_tolerance: Optional[str]
    soil_types: Optional[List[str]]
    maintenance_level: Optional[str]
    maintenance_notes: Optional[Dict[str, Any]]
    vta_approved: Optional[bool]
    csj_street_tree: Optional[bool]
    fall_color: Optional[bool]
    flowers: Optional[bool]
    ocf_notes: Optional[str]
    created_at: str


_db_manager = None


def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(settings.database_url)
    return _db_manager


def _map_species(species: PlantSpecies) -> SpeciesResponse:
    """Map ORM row to SpeciesResponse, computing single-value height/spread."""
    h_min = species.mature_height_ft_min or 0
    h_max = species.mature_height_ft_max or 0
    sp_min = species.mature_spread_ft_min or 0
    sp_max = species.mature_spread_ft_max or 0
    return SpeciesResponse(
        species_id=species.species_id,
        common_name=species.common_name,
        scientific_name=species.scientific_name,
        tree_type=species.tree_type or 'deciduous',
        mature_height_ft=h_max or h_min,
        mature_spread_ft=sp_max or sp_min,
        hardiness_zone_min=species.hardiness_zone_min or 7,
        hardiness_zone_max=species.hardiness_zone_max or 10,
        drought_tolerant=bool(species.drought_tolerant),
        native_regions=species.native_regions,
        co2_sequestration_kg_year=species.co2_sequestration_kg_year or 0.0,
        stormwater_interception_gal_year=species.stormwater_gallons_year or 0.0,
        air_pollution_removal_kg_year=species.air_pollution_removal_kg_year or 0.0,
        price_6ft=species.price_6ft,
    )


@router.get("/search", response_model=List[SpeciesResponse])
async def search_species(
    query: Optional[str] = Query(None, description="Search by name"),
    hardiness_zone: Optional[int] = Query(None, ge=1, le=13),
    tree_type: Optional[str] = Query(None),
    native_only: bool = Query(False),
    drought_tolerant: Optional[bool] = Query(None),
    vta_approved: Optional[bool] = Query(None),
    max_height_ft: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Search plant species database.

    Filters: query, hardiness_zone, tree_type, native_only,
             drought_tolerant, vta_approved, max_height_ft
    """
    try:
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            stmt = select(PlantSpecies)
            filters = []

            if query:
                filters.append(or_(
                    PlantSpecies.common_name.ilike(f'%{query}%'),
                    PlantSpecies.scientific_name.ilike(f'%{query}%'),
                ))

            if hardiness_zone is not None:
                filters.append(and_(
                    PlantSpecies.hardiness_zone_min <= hardiness_zone,
                    PlantSpecies.hardiness_zone_max >= hardiness_zone,
                ))

            if tree_type:
                filters.append(PlantSpecies.tree_type == tree_type)

            if drought_tolerant is not None:
                filters.append(PlantSpecies.drought_tolerant == drought_tolerant)

            if max_height_ft:
                # Use max height column for filtering
                filters.append(PlantSpecies.mature_height_ft_max <= max_height_ft)

            if native_only:
                # Cast JSONB/JSON to string and search for "california"
                filters.append(
                    cast(PlantSpecies.native_regions, String).ilike('%california%')
                )

            if vta_approved is not None:
                filters.append(PlantSpecies.vta_approved == vta_approved)

            if filters:
                stmt = stmt.where(and_(*filters))

            # Sort by CO2 benefit descending so best trees appear first
            stmt = stmt.order_by(PlantSpecies.co2_sequestration_kg_year.desc().nullslast())
            stmt = stmt.limit(limit)

            result = await session.execute(stmt)
            return [_map_species(s) for s in result.scalars().all()]

    except Exception as e:
        logger.error(f"Species search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error searching species: {str(e)}")


@router.get("/{species_id}", response_model=SpeciesDetailResponse)
async def get_species(species_id: str):
    """Get detailed species information by ID."""
    try:
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            stmt = select(PlantSpecies).where(PlantSpecies.species_id == species_id)
            result = await session.execute(stmt)
            species = result.scalar_one_or_none()

            if not species:
                raise HTTPException(status_code=404, detail=f"Species not found: {species_id}")

            base = _map_species(species)
            return SpeciesDetailResponse(
                **base.model_dump(),
                growth_rate=species.growth_rate,
                sunlight_requirements=species.sunlight,
                moisture_tolerance=species.moisture_tolerance,
                soil_types=species.soil_types or [],
                maintenance_level=species.maintenance_level,
                maintenance_notes=species.maintenance_notes,
                vta_approved=getattr(species, 'vta_approved', None),
                csj_street_tree=getattr(species, 'csj_street_tree', None),
                fall_color=getattr(species, 'fall_color', None),
                flowers=getattr(species, 'flowers', None),
                ocf_notes=getattr(species, 'ocf_notes', None),
                created_at=species.created_at.isoformat() if species.created_at else '',
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving species: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving species: {str(e)}")


@router.get("/")
async def list_all_species(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List all species with pagination."""
    try:
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            from sqlalchemy import func
            total = (await session.execute(select(func.count()).select_from(PlantSpecies))).scalar()

            stmt = select(PlantSpecies).offset(offset).limit(limit)
            result = await session.execute(stmt)
            species_list = result.scalars().all()

            return {
                'total': total,
                'limit': limit,
                'offset': offset,
                'species': [
                    {'species_id': s.species_id, 'common_name': s.common_name,
                     'scientific_name': s.scientific_name, 'tree_type': s.tree_type}
                    for s in species_list
                ],
            }

    except Exception as e:
        logger.error(f"Error listing species: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing species: {str(e)}")
