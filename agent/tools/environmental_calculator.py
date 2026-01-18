"""
Environmental Benefits Calculator Tool
Calculates CO2 sequestration, stormwater, air quality, and energy savings
"""

from typing import Dict, Any, Optional
from sqlalchemy import select
import logging

from agent.tools.base_tool import BaseTool
from agent.services.plant_database import DatabaseManager, PlantSpecies
from agent.services.itree_integration import get_itree_api
from agent.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class EnvironmentalCalculatorTool(BaseTool):
    """
    Calculates environmental benefits over time including:
    - CO2 sequestration (kg/year)
    - Air pollution removal (kg/year)
    - Stormwater interception (gallons/year)
    - Energy savings (kWh/year)
    - Dollar value conversions
    - Relatable equivalent metrics
    """

    def __init__(self, db_manager: DatabaseManager, cache_service: Optional[CacheService] = None):
        super().__init__()
        self.db_manager = db_manager
        self.itree_api = get_itree_api(cache_service)

    @property
    def name(self) -> str:
        return "environmental_calculator"

    @property
    def description(self) -> str:
        return (
            "Calculates environmental benefits of trees over time including CO2 sequestration, "
            "stormwater management, air quality improvement, and energy savings. Returns "
            "lifetime projections and dollar value equivalents."
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
                "quantity": {
                    "type": "integer",
                    "description": "Number of trees"
                },
                "years_projection": {
                    "type": "integer",
                    "description": "Number of years to project (default: 20)"
                },
                "tree_age_years": {
                    "type": "integer",
                    "description": "Current age of trees (default: 0 for new planting)"
                }
            },
            "required": ["species_id", "quantity"]
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute environmental benefits calculation"""
        species_id = kwargs['species_id']
        quantity = kwargs['quantity']
        years_projection = kwargs.get('years_projection', 20)
        tree_age_years = kwargs.get('tree_age_years', 0)

        # Load species from database
        async with self.db_manager.get_session() as session:
            stmt = select(PlantSpecies).where(PlantSpecies.species_id == species_id)
            result = await session.execute(stmt)
            species = result.scalar_one_or_none()

            if not species:
                raise ValueError(f"Species {species_id} not found")

        # Get mature benefits from database
        mature_benefits = {
            'co2_sequestration_kg_year': species.co2_sequestration_kg_year or 0,
            'air_pollution_removal_kg_year': species.air_pollution_removal_kg_year or 0,
            'stormwater_gallons_year': species.stormwater_gallons_year or 0,
            'energy_savings_kwh_year': species.energy_savings_kwh_year or 0
        }

        # Calculate year-by-year benefits with growth curve
        yearly_benefits = self._calculate_yearly_benefits(
            mature_benefits,
            tree_age_years,
            years_projection,
            species.mature_height_ft_max or 40
        )

        # Calculate cumulative totals
        cumulative_benefits = {
            'co2_kg': sum(y['co2_kg'] for y in yearly_benefits),
            'air_pollution_kg': sum(y['air_pollution_kg'] for y in yearly_benefits),
            'stormwater_gallons': sum(y['stormwater_gallons'] for y in yearly_benefits),
            'energy_kwh': sum(y['energy_kwh'] for y in yearly_benefits)
        }

        # Multiply by quantity
        total_benefits = {k: v * quantity for k, v in cumulative_benefits.items()}

        # Calculate dollar values
        dollar_values = self.itree_api.calculate_dollar_value(
            {
                'co2_sequestration_kg_year': cumulative_benefits['co2_kg'],
                'air_pollution_removal_kg_year': cumulative_benefits['air_pollution_kg'],
                'stormwater_gallons_year': cumulative_benefits['stormwater_gallons'],
                'energy_savings_kwh_year': cumulative_benefits['energy_kwh']
            },
            years=1  # Already cumulative
        )

        # Generate equivalent metrics
        equivalents = self.itree_api.generate_equivalent_metrics(
            {
                'co2_sequestration_kg_year': total_benefits['co2_kg'],
                'stormwater_gallons_year': total_benefits['stormwater_gallons']
            },
            years=1
        )

        return {
            'species': {
                'species_id': species.species_id,
                'common_name': species.common_name,
                'scientific_name': species.scientific_name
            },
            'quantity': quantity,
            'projection_years': years_projection,
            'starting_age': tree_age_years,

            'annual_benefits_per_tree': {
                'co2_kg': round(mature_benefits['co2_sequestration_kg_year'], 2),
                'air_pollution_kg': round(mature_benefits['air_pollution_removal_kg_year'], 2),
                'stormwater_gallons': round(mature_benefits['stormwater_gallons_year'], 2),
                'energy_kwh': round(mature_benefits['energy_savings_kwh_year'], 2)
            },

            'cumulative_benefits': {
                'co2_kg': round(total_benefits['co2_kg'], 1),
                'air_pollution_kg': round(total_benefits['air_pollution_kg'], 1),
                'stormwater_gallons': round(total_benefits['stormwater_gallons'], 1),
                'energy_kwh': round(total_benefits['energy_kwh'], 1)
            },

            'dollar_value': dollar_values['annual'],
            'equivalent_metrics': equivalents,

            'notes': [
                f"Based on i-Tree scientific data for {species.common_name}",
                "Benefits assume healthy tree growth and proper maintenance",
                f"Projections include growth curve from age {tree_age_years} to {tree_age_years + years_projection}"
            ]
        }

    def _calculate_yearly_benefits(
        self,
        mature_benefits: Dict[str, float],
        start_age: int,
        years: int,
        mature_height_ft: float
    ) -> list:
        """Calculate benefits for each year with growth curve"""
        yearly = []

        for year in range(years):
            age = start_age + year

            # Apply growth curve scaling
            scale_factor = self._growth_curve_factor(age, mature_height_ft)

            yearly.append({
                'year': year + 1,
                'tree_age': age,
                'scale_factor': round(scale_factor, 2),
                'co2_kg': mature_benefits['co2_sequestration_kg_year'] * scale_factor,
                'air_pollution_kg': mature_benefits['air_pollution_removal_kg_year'] * scale_factor,
                'stormwater_gallons': mature_benefits['stormwater_gallons_year'] * scale_factor,
                'energy_kwh': mature_benefits['energy_savings_kwh_year'] * scale_factor
            })

        return yearly

    def _growth_curve_factor(self, age: int, mature_height_ft: float) -> float:
        """Calculate growth curve scaling factor based on age"""
        # Estimate years to maturity based on height (taller trees take longer)
        years_to_maturity = mature_height_ft / 3  # Rough approximation

        if age < 2:
            return 0.10  # Young trees: 10% of mature benefits
        elif age < years_to_maturity * 0.5:
            # Juvenile: linear ramp from 10% to 80%
            progress = age / (years_to_maturity * 0.5)
            return 0.10 + progress * 0.70
        else:
            # Mature: linear ramp from 80% to 100%
            progress = (age - years_to_maturity * 0.5) / (years_to_maturity * 0.5)
            return 0.80 + min(progress * 0.20, 0.20)
