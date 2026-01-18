"""
Maintenance Guide Tool
Provides care instructions for trees based on species, age, and season
"""

from typing import Dict, Any, Optional
from sqlalchemy import select
import logging

from agent.tools.base_tool import BaseTool
from agent.services.plant_database import DatabaseManager, PlantSpecies

logger = logging.getLogger(__name__)


class MaintenanceGuideTool(BaseTool):
    """
    Generates maintenance schedules including:
    - Watering frequency and amounts
    - Pruning schedules and techniques
    - Fertilization requirements
    - Pest and disease monitoring
    - Seasonal care adjustments
    """

    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager

    @property
    def name(self) -> str:
        return "maintenance_guide"

    @property
    def description(self) -> str:
        return (
            "Provides detailed maintenance care guide for a tree species based on age and season. "
            "Includes watering schedules, pruning guidelines, fertilization, pest monitoring, and cost estimates."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "species_id": {
                    "type": "string",
                    "description": "Species identifier"
                },
                "tree_age_years": {
                    "type": "integer",
                    "description": "Age of tree in years (default: 0 for newly planted)"
                },
                "season": {
                    "type": "string",
                    "enum": ["spring", "summer", "fall", "winter", "all"],
                    "description": "Season for care instructions (default: all)"
                }
            },
            "required": ["species_id"]
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute maintenance guide generation"""
        species_id = kwargs['species_id']
        tree_age = kwargs.get('tree_age_years', 0)
        season = kwargs.get('season', 'all')

        # Load species
        async with self.db_manager.get_session() as session:
            stmt = select(PlantSpecies).where(PlantSpecies.species_id == species_id)
            result = await session.execute(stmt)
            species = result.scalar_one_or_none()

            if not species:
                raise ValueError(f"Species {species_id} not found")

        # Categorize tree age
        age_category = self._categorize_age(tree_age)

        # Generate watering schedule
        watering = self._generate_watering_schedule(species, age_category, season)

        # Generate pruning schedule
        pruning = self._generate_pruning_schedule(species, age_category, season)

        # Generate fertilization schedule
        fertilization = self._generate_fertilization_schedule(species, age_category, season)

        # Generate pest monitoring
        pest_watch = self._generate_pest_watch(species, season)

        # Estimate annual cost
        annual_cost = self._estimate_annual_cost(species, age_category)

        # Seasonal care tips
        seasonal_tips = self._generate_seasonal_tips(species, season)

        return {
            'species': {
                'species_id': species.species_id,
                'common_name': species.common_name,
                'maintenance_level': species.maintenance_level
            },
            'tree_age_years': tree_age,
            'age_category': age_category,
            'season': season,

            'watering_schedule': watering,
            'pruning_schedule': pruning,
            'fertilization': fertilization,
            'pest_disease_watch': pest_watch,
            'seasonal_care_tips': seasonal_tips,

            'estimated_annual_cost': annual_cost,

            'notes': [
                "Adjust watering based on rainfall and soil moisture",
                "Young trees (0-2 years) require more frequent care",
                "Contact certified arborist for complex pruning or health issues"
            ]
        }

    def _categorize_age(self, age_years: int) -> str:
        """Categorize tree age"""
        if age_years < 2:
            return 'young'
        elif age_years < 5:
            return 'juvenile'
        else:
            return 'mature'

    def _generate_watering_schedule(self, species: PlantSpecies, age_category: str, season: str) -> Dict[str, Any]:
        """Generate watering schedule"""
        # Base schedule by age
        if age_category == 'young':
            frequency = '2-3 times per week'
            amount_gallons = 15
            duration_minutes = 30
        elif age_category == 'juvenile':
            frequency = 'Weekly'
            amount_gallons = 20
            duration_minutes = 40
        else:
            frequency = 'As needed (during drought)'
            amount_gallons = 25
            duration_minutes = 50

        # Adjust for drought tolerance
        if species.drought_tolerant:
            if age_category == 'mature':
                frequency = 'Rarely needed (drought periods only)'
                amount_gallons = 20

        # Seasonal adjustments
        seasonal_notes = []
        if season in ['summer', 'all']:
            seasonal_notes.append("Summer: Increase frequency during hot, dry periods")
        if season in ['winter', 'all']:
            seasonal_notes.append("Winter: Reduce or stop watering for dormant trees")
        if season in ['spring', 'all']:
            seasonal_notes.append("Spring: Resume regular watering as growth begins")

        return {
            'frequency': frequency,
            'amount_gallons_per_session': amount_gallons,
            'duration_minutes': duration_minutes,
            'method': 'Deep watering at drip line (edge of canopy)',
            'seasonal_adjustments': seasonal_notes,
            'drought_tolerant': species.drought_tolerant
        }

    def _generate_pruning_schedule(self, species: PlantSpecies, age_category: str, season: str) -> Dict[str, Any]:
        """Generate pruning schedule"""
        if age_category == 'young':
            timing = 'Late winter to early spring (dormant season)'
            focus = 'Structural pruning - establish strong framework'
            frequency = 'Annually'
        elif age_category == 'juvenile':
            timing = 'Late winter (before spring growth)'
            focus = 'Continue structural pruning, remove competing leaders'
            frequency = 'Annually'
        else:
            timing = 'Late winter or as needed'
            focus = 'Maintenance pruning - remove dead, diseased, or crossing branches'
            frequency = 'Every 2-3 years or as needed'

        # Species-specific adjustments
        if species.tree_type == 'deciduous':
            best_season = 'Late winter (dormant)'
        else:
            best_season = 'Late winter to early spring'

        techniques = [
            "Remove dead, diseased, or damaged branches first",
            "Make cuts just outside branch collar (don't leave stubs)",
            "Don't remove more than 25% of canopy in one season",
            "Sterilize pruning tools between cuts"
        ]

        return {
            'timing': timing,
            'best_season': best_season,
            'frequency': frequency,
            'focus': focus,
            'techniques': techniques,
            'professional_help': age_category != 'young' and 'Consider certified arborist for major pruning'
        }

    def _generate_fertilization_schedule(self, species: PlantSpecies, age_category: str, season: str) -> Dict[str, Any]:
        """Generate fertilization schedule"""
        if age_category == 'young':
            schedule = 'Begin in 2nd year after planting'
            timing = 'Early spring'
            frequency = 'Annually'
        elif age_category == 'juvenile':
            schedule = 'Annual fertilization recommended'
            timing = 'Early spring before new growth'
            frequency = 'Annually'
        else:
            schedule = 'As needed based on soil test'
            timing = 'Early spring or fall'
            frequency = 'Every 2-3 years or based on soil test'

        return {
            'schedule': schedule,
            'timing': timing,
            'frequency': frequency,
            'fertilizer_type': 'Balanced slow-release (10-10-10 or similar)',
            'application_method': 'Broadcast at drip line, water in thoroughly',
            'recommendation': 'Conduct soil test every 3-5 years to determine actual needs'
        }

    def _generate_pest_watch(self, species: PlantSpecies, season: str) -> Dict[str, Any]:
        """Generate pest and disease watch list"""
        # Get species-specific pests from maintenance notes
        maintenance_notes = species.maintenance_notes or {}
        species_pests = maintenance_notes.get('pests', [])

        # General pests by season
        seasonal_pests = {
            'spring': ['aphids', 'scale', 'emerging larvae'],
            'summer': ['spider mites', 'beetles', 'borers'],
            'fall': ['scale', 'bagworms'],
            'winter': ['minimal pest activity']
        }

        if season == 'all':
            watch_for = species_pests if species_pests else ['aphids', 'scale', 'beetles']
        else:
            watch_for = seasonal_pests.get(season, [])

        return {
            'common_pests': species_pests if species_pests else ['aphids', 'scale'],
            'seasonal_watch': watch_for,
            'pest_resistance': species.pest_resistance or 'medium',
            'disease_resistance': species.disease_resistance or 'medium',
            'monitoring_frequency': 'Monthly visual inspection',
            'action': 'Identify pest/disease before treating - consult extension service or arborist'
        }

    def _generate_seasonal_tips(self, species: PlantSpecies, season: str) -> list:
        """Generate seasonal care tips"""
        tips = {
            'spring': [
                "Apply fresh mulch (2-4 inches) around base, keeping away from trunk",
                "Begin regular watering as growth starts",
                "Inspect for winter damage and prune dead branches",
                "Apply fertilizer if needed (2nd year onward)"
            ],
            'summer': [
                "Monitor soil moisture and water during dry periods",
                "Watch for heat stress (wilting, leaf scorch)",
                "Check for pest activity weekly",
                "Avoid heavy pruning during active growth"
            ],
            'fall': [
                "Reduce watering as tree prepares for dormancy",
                "Rake and remove diseased leaves",
                "Protect trunk from rodents (wire mesh)",
                "Last chance for fertilization before winter"
            ],
            'winter': [
                "Water during warm, dry periods if ground not frozen",
                "Check stakes and ties, adjust if needed",
                "Protect young trees from snow/ice damage",
                "Plan pruning for late winter"
            ]
        }

        if season == 'all':
            all_tips = []
            for s in ['spring', 'summer', 'fall', 'winter']:
                all_tips.append(f"{s.title()}: " + "; ".join(tips[s][:2]))
            return all_tips
        else:
            return tips.get(season, [])

    def _estimate_annual_cost(self, species: PlantSpecies, age_category: str) -> Dict[str, Any]:
        """Estimate annual maintenance cost"""
        if age_category == 'young':
            water_cost = 40
            fertilizer_cost = 25
            mulch_cost = 30
            pruning_cost = 0  # DIY
        elif age_category == 'juvenile':
            water_cost = 30
            fertilizer_cost = 30
            mulch_cost = 40
            pruning_cost = 75  # Light professional pruning
        else:
            water_cost = 15
            fertilizer_cost = 25
            mulch_cost = 50
            pruning_cost = 100  # Professional pruning every 2-3 years (amortized)

        # Adjust for maintenance level
        if species.maintenance_level == 'high':
            pruning_cost *= 1.5
        elif species.maintenance_level == 'low':
            pruning_cost *= 0.7

        total = water_cost + fertilizer_cost + mulch_cost + pruning_cost

        return {
            'water': round(water_cost, 2),
            'fertilizer': round(fertilizer_cost, 2),
            'mulch': round(mulch_cost, 2),
            'pruning': round(pruning_cost, 2),
            'total_annual': round(total, 2),
            'note': 'Costs assume DIY watering/fertilizing, professional pruning as needed'
        }
