"""
Pricing Calculator Tool
Calculates costs for trees, installation, and materials
"""

from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from agent.tools.base_tool import BaseTool
from agent.services.plant_database import DatabaseManager, PlantSpecies
from agent.config import settings

logger = logging.getLogger(__name__)


class PricingCalculatorTool(BaseTool):
    """
    Calculates pricing for tree purchases and installation

    Includes:
    - Tree cost by size (sapling, 6ft, 8ft, 10ft)
    - Regional pricing adjustments
    - Professional planting labor
    - Materials (soil, mulch, stakes)
    - Bulk discounts
    """

    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager

    @property
    def name(self) -> str:
        return "pricing_calculator"

    @property
    def description(self) -> str:
        return (
            "Calculates total cost for tree purchase and installation including "
            "regional pricing adjustments, labor, materials, and bulk discounts."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "species_id": {
                    "type": "string",
                    "description": "Species identifier (e.g., 'PLOC')"
                },
                "quantity": {
                    "type": "integer",
                    "description": "Number of trees"
                },
                "tree_size": {
                    "type": "string",
                    "enum": ["sapling", "6ft", "8ft", "10ft"],
                    "description": "Tree size to purchase"
                },
                "include_planting": {
                    "type": "boolean",
                    "description": "Include professional planting labor"
                },
                "zip_code": {
                    "type": "string",
                    "description": "ZIP code for regional pricing (optional)"
                }
            },
            "required": ["species_id", "quantity", "tree_size", "include_planting"]
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute pricing calculation"""
        species_id = kwargs['species_id']
        quantity = kwargs['quantity']
        tree_size = kwargs['tree_size']
        include_planting = kwargs['include_planting']
        zip_code = kwargs.get('zip_code')

        # Load species from database
        async with self.db_manager.get_session() as session:
            stmt = select(PlantSpecies).where(PlantSpecies.species_id == species_id)
            result = await session.execute(stmt)
            species = result.scalar_one_or_none()

            if not species:
                raise ValueError(f"Species {species_id} not found")

        # Get base tree price
        price_map = {
            'sapling': species.price_sapling,
            '6ft': species.price_6ft,
            '8ft': species.price_8ft,
            '10ft': species.price_10ft
        }
        base_price_per_tree = price_map.get(tree_size)
        if not base_price_per_tree:
            raise ValueError(f"Price not available for {tree_size} size")

        # Regional multiplier
        regional_multiplier = 1.0
        if zip_code:
            state_code = self._zip_to_state(zip_code)
            regional_multiplier = settings.get_price_multiplier(state_code)

        tree_price_per_unit = base_price_per_tree * regional_multiplier

        # Labor cost (if include_planting)
        labor_hours_map = {'sapling': 2, '6ft': 2.5, '8ft': 3, '10ft': 4}
        labor_hours = labor_hours_map.get(tree_size, 2.5)
        labor_rate_per_hour = 50.0
        labor_per_tree = labor_hours * labor_rate_per_hour if include_planting else 0

        # Materials cost (if include_planting)
        materials_per_tree = 50.0 if include_planting else 0  # Soil, mulch, stakes

        # Calculate per-tree cost
        cost_per_tree = tree_price_per_unit + labor_per_tree + materials_per_tree

        # Subtotal before discounts
        subtotal = cost_per_tree * quantity

        # Bulk discount
        discount_rate = 0
        if quantity >= 25:
            discount_rate = 0.15
        elif quantity >= 10:
            discount_rate = 0.10

        discount_amount = subtotal * discount_rate
        total = subtotal - discount_amount

        # Breakdown
        return {
            'species': {
                'species_id': species.species_id,
                'common_name': species.common_name,
                'scientific_name': species.scientific_name
            },
            'quantity': quantity,
            'tree_size': tree_size,
            'breakdown': {
                'tree_price_per_unit': round(tree_price_per_unit, 2),
                'base_price': round(base_price_per_tree, 2),
                'regional_multiplier': regional_multiplier,
                'labor_per_tree': round(labor_per_tree, 2) if include_planting else 0,
                'labor_hours': labor_hours if include_planting else 0,
                'materials_per_tree': round(materials_per_tree, 2) if include_planting else 0,
                'cost_per_tree': round(cost_per_tree, 2),
                'subtotal': round(subtotal, 2),
                'discount_rate': discount_rate,
                'discount_amount': round(discount_amount, 2)
            },
            'total_cost': round(total, 2),
            'estimated_delivery_days': 7 if tree_size == 'sapling' else 14,
            'planting_included': include_planting
        }

    def _zip_to_state(self, zip_code: str) -> str:
        """Map ZIP code to state (first digit approximation)"""
        state_map = {
            '9': 'CA', '0': 'MA', '1': 'NY', '2': 'VA',
            '7': 'TX', '6': 'IL'
        }
        return state_map.get(zip_code[0], 'default')
