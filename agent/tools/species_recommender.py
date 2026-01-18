"""
Species Recommender Tool
Recommends tree species based on site conditions and user preferences
"""

from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from agent.tools.base_tool import BaseTool
from agent.services.plant_database import DatabaseManager, PlantSpecies
from agent.services.site_data_loader import SiteDataLoader
from agent.services.hardiness_zone_api import get_hardiness_api
from agent.services.cache_service import CacheService
from agent.config import settings
import json

logger = logging.getLogger(__name__)


class SpeciesRecommenderTool(BaseTool):
    """
    Recommends tree species based on:
    - Planting site characteristics (NDVI, slope, area)
    - USDA hardiness zones
    - User preferences (shade, privacy, wildlife, aesthetics, stormwater)
    - Soil conditions and sunlight
    - Native species prioritization
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        cache_service: Optional[CacheService] = None
    ):
        super().__init__()
        self.db_manager = db_manager
        self.site_loader = SiteDataLoader(db_manager)
        self.hardiness_api = get_hardiness_api(cache_service)
        self.cache_service = cache_service

    @property
    def name(self) -> str:
        return "species_recommender"

    @property
    def description(self) -> str:
        return (
            "Recommends tree species based on planting site characteristics, "
            "climate zone, space constraints, and user preferences. Returns top "
            "10 species ranked by suitability score with detailed justification."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "planting_site_id": {
                    "type": "string",
                    "description": "UUID of planting site from CV analysis"
                },
                "zip_code": {
                    "type": "string",
                    "description": "5-digit ZIP code for hardiness zone lookup"
                },
                "space_constraint": {
                    "type": "string",
                    "enum": ["small", "medium", "large", "any"],
                    "description": "Available space size (small: <25ft, medium: 25-45ft, large: >45ft)"
                },
                "purposes": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["shade", "privacy", "wildlife", "aesthetic", "stormwater", "street_tree"]
                    },
                    "description": "Desired tree purposes (can select multiple)"
                },
                "soil_type": {
                    "type": "string",
                    "enum": ["clay", "loam", "sandy", "unknown"],
                    "description": "Soil type if known"
                },
                "prioritize_native": {
                    "type": "boolean",
                    "description": "Prioritize native species"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of recommendations to return (default: 10)"
                }
            },
            "required": ["planting_site_id", "zip_code"]
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute species recommendation

        Returns:
            Dict with 'recommendations' (list of species with scores and reasoning),
            'site_summary', 'hardiness_zone', 'total_candidates'
        """
        # Extract parameters
        site_id = kwargs['planting_site_id']
        zip_code = kwargs['zip_code']
        space_constraint = kwargs.get('space_constraint', 'any')
        purposes = kwargs.get('purposes', [])
        soil_type = kwargs.get('soil_type', 'unknown')
        prioritize_native = kwargs.get('prioritize_native', False)
        max_results = kwargs.get('max_results', 10)

        logger.info(
            f"Species recommendation for site {site_id}, ZIP {zip_code}, "
            f"space: {space_constraint}, purposes: {purposes}"
        )

        # Step 1: Load site data
        site_data = await self.site_loader.get_site_by_id(site_id)
        if not site_data:
            raise ValueError(f"Planting site {site_id} not found in database")

        # Step 2: Get hardiness zone
        zone_data = await self.hardiness_api.get_zone_by_zip(zip_code)
        hardiness_zone = zone_data['zone_numeric']

        # Step 3: Calculate size constraints from site area
        size_constraints = self.site_loader.calculate_recommended_tree_size(site_data)

        # Override if user specified smaller constraint
        if space_constraint == 'small':
            size_constraints['max_height_ft'] = min(size_constraints['max_height_ft'], 25)
            size_constraints['max_spread_ft'] = min(size_constraints['max_spread_ft'], 20)
        elif space_constraint == 'medium':
            size_constraints['max_height_ft'] = min(size_constraints['max_height_ft'], 45)
            size_constraints['max_spread_ft'] = min(size_constraints['max_spread_ft'], 35)
        # 'large' or 'any' - use calculated constraints

        # Step 4: Query database for candidate species
        async with self.db_manager.get_session() as session:
            candidates = await self._query_candidates(
                session,
                hardiness_zone,
                size_constraints,
                soil_type,
                purposes,
                prioritize_native
            )

        if not candidates:
            return {
                'recommendations': [],
                'site_summary': site_data,
                'hardiness_zone': zone_data,
                'total_candidates': 0,
                'message': 'No suitable species found for the given criteria. Try relaxing constraints.'
            }

        # Step 5: Score and rank candidates
        scored_candidates = []
        for species in candidates:
            score_breakdown = self._calculate_suitability_score(
                species,
                site_data,
                purposes,
                prioritize_native
            )

            scored_candidates.append({
                'species': species,
                'score': score_breakdown['total_score'],
                'score_breakdown': score_breakdown
            })

        # Sort by score (descending)
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)

        # Step 6: Format top recommendations
        recommendations = []
        for i, candidate in enumerate(scored_candidates[:max_results]):
            species = candidate['species']
            score = candidate['score']
            breakdown = candidate['score_breakdown']

            recommendations.append({
                'rank': i + 1,
                'species_id': species.species_id,
                'common_name': species.common_name,
                'scientific_name': species.scientific_name,
                'suitability_score': round(score, 3),
                'score_breakdown': breakdown,

                # Size
                'mature_height_ft': f"{species.mature_height_ft_min}-{species.mature_height_ft_max}",
                'mature_spread_ft': f"{species.mature_spread_ft_min}-{species.mature_spread_ft_max}",
                'growth_rate': species.growth_rate,

                # Environmental benefits
                'co2_sequestration_kg_year': species.co2_sequestration_kg_year,
                'stormwater_gallons_year': species.stormwater_gallons_year,

                # Characteristics
                'tree_type': species.tree_type,
                'sunlight': species.sunlight,
                'maintenance_level': species.maintenance_level,
                'drought_tolerant': species.drought_tolerant,
                'is_native': len(species.native_regions or []) > 0,
                'native_regions': species.native_regions,

                # Pricing
                'price_sapling': species.price_sapling,
                'price_6ft': species.price_6ft,

                # Description
                'description': species.description,

                # Recommendation reasoning
                'why_recommended': self._generate_recommendation_reasoning(
                    species,
                    site_data,
                    breakdown,
                    purposes
                )
            })

        return {
            'recommendations': recommendations,
            'site_summary': {
                'site_id': site_data['site_id'],
                'address': site_data['address'],
                'avg_ndvi': site_data['avg_ndvi'],
                'ndvi_category': site_data['ndvi_category'],
                'avg_slope': site_data['avg_slope'],
                'slope_category': site_data['slope_category'],
                'area_sq_ft': site_data['area_sq_ft'],
                'max_tree_height': size_constraints['max_height_ft'],
                'max_tree_spread': size_constraints['max_spread_ft']
            },
            'hardiness_zone': zone_data,
            'search_criteria': {
                'space_constraint': space_constraint,
                'purposes': purposes,
                'soil_type': soil_type,
                'prioritize_native': prioritize_native
            },
            'total_candidates': len(candidates),
            'returned_results': len(recommendations)
        }

    async def _query_candidates(
        self,
        session: AsyncSession,
        hardiness_zone: int,
        size_constraints: Dict[str, Any],
        soil_type: str,
        purposes: List[str],
        prioritize_native: bool
    ) -> List[PlantSpecies]:
        """
        Query database for candidate species

        Args:
            session: Database session
            hardiness_zone: Numeric hardiness zone
            size_constraints: Max height/spread dict
            soil_type: Soil type
            purposes: Desired purposes
            prioritize_native: Whether to prioritize native

        Returns:
            List of PlantSpecies matching criteria
        """
        # Build query filters
        filters = [
            # Hardiness zone compatible
            PlantSpecies.hardiness_zone_min <= hardiness_zone,
            PlantSpecies.hardiness_zone_max >= hardiness_zone,

            # Size fits
            PlantSpecies.mature_height_ft_max <= size_constraints['max_height_ft'] + 10,  # 10ft tolerance
            PlantSpecies.mature_spread_ft_max <= size_constraints['max_spread_ft'] + 10
        ]

        # Soil type filter (if specified and not unknown)
        if soil_type != 'unknown':
            filters.append(
                or_(
                    PlantSpecies.soil_types.contains([soil_type]),
                    PlantSpecies.soil_types.is_(None)  # Allow species with no soil preference
                )
            )

        # Purpose filter (if specified)
        if purposes:
            # Match ANY of the specified purposes
            purpose_filters = [
                PlantSpecies.purposes.contains([purpose])
                for purpose in purposes
            ]
            filters.append(or_(*purpose_filters))

        # Execute query
        stmt = select(PlantSpecies).where(and_(*filters))
        result = await session.execute(stmt)
        candidates = result.scalars().all()

        # If prioritizing native and we have native species, filter to only native
        if prioritize_native:
            native_candidates = [
                c for c in candidates
                if c.native_regions and len(c.native_regions) > 0
            ]
            if native_candidates:
                return native_candidates

        return candidates

    def _calculate_suitability_score(
        self,
        species: PlantSpecies,
        site_data: Dict[str, Any],
        purposes: List[str],
        prioritize_native: bool
    ) -> Dict[str, Any]:
        """
        Calculate suitability score for a species

        Scoring breakdown:
        - 25%: NDVI match (soil moisture/vegetation tolerance)
        - 15%: Slope tolerance
        - 25%: Environmental benefits
        - 15%: Native species bonus
        - 20%: Purpose match

        Returns:
            Dict with total_score and component scores
        """
        # Component 1: NDVI match (25%)
        ndvi_score = self._score_ndvi_match(species, site_data['avg_ndvi'])

        # Component 2: Slope tolerance (15%)
        slope_score = self._score_slope_tolerance(species, site_data['avg_slope'])

        # Component 3: Environmental benefits (25%)
        env_score = self._score_environmental_benefits(species)

        # Component 4: Native species bonus (15%)
        native_score = 1.0 if (species.native_regions and len(species.native_regions) > 0) else 0.5
        if prioritize_native:
            native_score *= 1.2  # Boost if user wants native

        # Component 5: Purpose match (20%)
        purpose_score = self._score_purpose_match(species, purposes)

        # Calculate weighted total
        total_score = (
            ndvi_score * 0.25 +
            slope_score * 0.15 +
            env_score * 0.25 +
            native_score * 0.15 +
            purpose_score * 0.20
        )

        return {
            'total_score': total_score,
            'ndvi_match': round(ndvi_score, 2),
            'slope_tolerance': round(slope_score, 2),
            'environmental_benefits': round(env_score, 2),
            'native_bonus': round(native_score, 2),
            'purpose_match': round(purpose_score, 2)
        }

    def _score_ndvi_match(self, species: PlantSpecies, site_ndvi: float) -> float:
        """Score how well species matches site NDVI"""
        # Map moisture tolerance to ideal NDVI range
        moisture_ndvi_map = {
            'dry': (0.1, 0.3),
            'medium': (0.25, 0.5),
            'wet': (0.4, 0.7)
        }

        if not species.moisture_tolerance:
            return 0.7  # Neutral score

        ideal_range = moisture_ndvi_map.get(species.moisture_tolerance, (0.2, 0.5))
        ideal_min, ideal_max = ideal_range

        if ideal_min <= site_ndvi <= ideal_max:
            return 1.0  # Perfect match
        elif site_ndvi < ideal_min:
            # Site is drier than ideal
            diff = ideal_min - site_ndvi
            return max(0.3, 1.0 - diff * 2)  # Penalty for being too dry
        else:
            # Site is wetter than ideal
            diff = site_ndvi - ideal_max
            return max(0.3, 1.0 - diff * 1.5)  # Smaller penalty for being too wet

    def _score_slope_tolerance(self, species: PlantSpecies, site_slope: float) -> float:
        """Score slope tolerance"""
        # Most trees handle up to 15° slope
        # Penalize based on site slope and tree characteristics
        if site_slope < 5:
            return 1.0  # Flat site, all trees ok

        if site_slope < 10:
            # Gentle slope - most trees fine, slight preference for drought-tolerant
            return 1.0 if species.drought_tolerant else 0.9

        if site_slope < 15:
            # Moderate slope - prefer drought-tolerant and deep-rooted
            return 0.9 if species.drought_tolerant else 0.7

        # Steep slope (shouldn't happen often since CV model filters at 15°)
        return 0.6 if species.drought_tolerant else 0.4

    def _score_environmental_benefits(self, species: PlantSpecies) -> float:
        """Score environmental benefits"""
        # Normalize CO2 sequestration (typical range: 20-200 kg/year)
        co2 = species.co2_sequestration_kg_year or 50
        co2_score = min(co2 / 200, 1.0)

        # Normalize stormwater (typical range: 200-2000 gallons/year)
        stormwater = species.stormwater_gallons_year or 500
        stormwater_score = min(stormwater / 2000, 1.0)

        # Combined environmental score
        return (co2_score + stormwater_score) / 2

    def _score_purpose_match(self, species: PlantSpecies, purposes: List[str]) -> float:
        """Score how well species matches desired purposes"""
        if not purposes:
            return 0.8  # Neutral score if no preferences

        if not species.purposes:
            return 0.5  # Species has no tagged purposes

        # Count matching purposes
        matches = sum(1 for p in purposes if p in species.purposes)
        match_ratio = matches / len(purposes)

        return match_ratio

    def _generate_recommendation_reasoning(
        self,
        species: PlantSpecies,
        site_data: Dict[str, Any],
        score_breakdown: Dict[str, Any],
        purposes: List[str]
    ) -> str:
        """Generate human-readable reasoning for recommendation"""
        reasons = []

        # NDVI match
        if score_breakdown['ndvi_match'] > 0.8:
            reasons.append(f"excellent match for site vegetation (NDVI: {site_data['avg_ndvi']:.2f})")
        elif score_breakdown['ndvi_match'] > 0.6:
            reasons.append(f"good match for site conditions")

        # Slope
        if site_data['avg_slope'] > 10 and score_breakdown['slope_tolerance'] > 0.8:
            reasons.append(f"well-suited for {site_data['avg_slope']:.1f}° slope")

        # Environmental benefits
        if species.co2_sequestration_kg_year > 150:
            reasons.append(f"high CO2 sequestration ({species.co2_sequestration_kg_year} kg/year)")
        if species.stormwater_gallons_year > 1000:
            reasons.append("excellent stormwater management")

        # Native
        if species.native_regions and len(species.native_regions) > 0:
            regions = ', '.join(species.native_regions[:2])  # First 2 regions
            reasons.append(f"native to {regions}")

        # Purpose match
        matching_purposes = [p for p in purposes if p in (species.purposes or [])]
        if matching_purposes:
            reasons.append(f"ideal for {', '.join(matching_purposes)}")

        # Maintenance
        if species.maintenance_level == 'low':
            reasons.append("low maintenance requirements")

        # Growth rate
        if species.growth_rate == 'fast':
            reasons.append("fast-growing for quicker benefits")

        return "; ".join(reasons).capitalize() if reasons else "Meets site requirements"
