"""
Planting Instructions Tool
Generates step-by-step planting instructions customized to species and site
"""

from typing import Dict, Any, List, Optional
from sqlalchemy import select
import logging

from agent.tools.base_tool import BaseTool
from agent.services.plant_database import DatabaseManager, PlantSpecies
from agent.services.site_data_loader import SiteDataLoader

logger = logging.getLogger(__name__)


class PlantingInstructionsTool(BaseTool):
    """
    Generates customized step-by-step planting instructions based on:
    - Species-specific requirements
    - Site conditions (NDVI, slope, area)
    - Tree size being planted
    - Soil type
    """

    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db_manager = db_manager
        self.site_loader = SiteDataLoader(db_manager)

    @property
    def name(self) -> str:
        return "planting_instructions"

    @property
    def description(self) -> str:
        return (
            "Generates detailed step-by-step planting instructions customized for the specific "
            "tree species and site conditions. Includes tools needed, preparation steps, and timing."
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
                "planting_site_id": {
                    "type": "string",
                    "description": "UUID of planting site (optional for site-specific notes)"
                },
                "tree_size": {
                    "type": "string",
                    "enum": ["sapling", "6ft", "8ft", "10ft"],
                    "description": "Size of tree being planted"
                },
                "soil_type": {
                    "type": "string",
                    "enum": ["clay", "loam", "sandy", "unknown"],
                    "description": "Soil type if known"
                }
            },
            "required": ["species_id", "tree_size"]
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute planting instructions generation"""
        species_id = kwargs['species_id']
        site_id = kwargs.get('planting_site_id')
        tree_size = kwargs['tree_size']
        soil_type = kwargs.get('soil_type', 'unknown')

        # Load species
        async with self.db_manager.get_session() as session:
            stmt = select(PlantSpecies).where(PlantSpecies.species_id == species_id)
            result = await session.execute(stmt)
            species = result.scalar_one_or_none()

            if not species:
                raise ValueError(f"Species {species_id} not found")

        # Load site data if provided
        site_data = None
        if site_id:
            site_data = await self.site_loader.get_site_by_id(site_id)

        # Generate tools needed list
        tools_needed = self._generate_tools_list(tree_size)

        # Generate step-by-step instructions
        steps = self._generate_planting_steps(species, tree_size, soil_type, site_data)

        # Calculate total time
        total_time = sum(step['time_estimate_min'] for step in steps)

        # Determine best planting time
        best_time = self._determine_best_planting_time(species)

        # Generate site-specific notes
        site_notes = self._generate_site_notes(site_data, species) if site_data else []

        return {
            'species': {
                'species_id': species.species_id,
                'common_name': species.common_name,
                'scientific_name': species.scientific_name
            },
            'tree_size': tree_size,
            'tools_needed': tools_needed,
            'steps': steps,
            'total_time_estimate_min': total_time,
            'best_planting_time': best_time,
            'site_specific_notes': site_notes,
            'success_tips': [
                "Water thoroughly immediately after planting",
                "Avoid fertilizing newly planted trees (wait until 2nd year)",
                "Keep mulch 2-3 inches away from trunk to prevent rot",
                "Check and adjust stakes/ties every 2-3 months",
                "Don't prune after planting unless removing broken branches"
            ]
        }

    def _generate_tools_list(self, tree_size: str) -> List[str]:
        """Generate list of tools needed"""
        base_tools = [
            "Round-point shovel",
            "Garden spade",
            "Rake",
            "Wheelbarrow or tarp",
            "Garden hose with spray nozzle",
            "Measuring tape",
            "Mulch (2-4 cubic feet)"
        ]

        # Add size-specific tools
        if tree_size in ['8ft', '10ft']:
            base_tools.extend([
                "Wood stakes (2-3, 6-8 ft tall)",
                "Tree straps or soft ties",
                "Mallet or post driver"
            ])

        base_tools.extend([
            "Soil amendments (compost, if needed)",
            "Gloves",
            "Utility knife",
            "Bucket for water"
        ])

        return base_tools

    def _generate_planting_steps(
        self,
        species: PlantSpecies,
        tree_size: str,
        soil_type: str,
        site_data: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate step-by-step planting instructions"""
        steps = []

        # Step 1: Site Preparation
        site_prep_instructions = [
            "Mark planting area - clear circle 3-4 ft diameter",
            "Remove grass, weeds, and debris",
            "Check soil drainage - dig test hole and fill with water",
            "If water doesn't drain in 4-6 hours, improve drainage"
        ]

        if site_data and site_data.get('avg_slope', 0) > 5:
            site_prep_instructions.append(
                f"Create level terrace on {site_data['avg_slope']:.1f}° slope to prevent runoff"
            )

        steps.append({
            'step_number': 1,
            'title': 'Site Preparation',
            'instructions': site_prep_instructions,
            'time_estimate_min': 20
        })

        # Step 2: Dig Hole
        hole_size_map = {
            'sapling': '18 inches wide x 12 inches deep',
            '6ft': '2-3 feet wide x 18 inches deep',
            '8ft': '3-4 feet wide x 24 inches deep',
            '10ft': '4-5 feet wide x 30 inches deep'
        }

        steps.append({
            'step_number': 2,
            'title': 'Dig Planting Hole',
            'instructions': [
                f"Dig hole {hole_size_map.get(tree_size)}",
                "Make hole 2-3x wider than root ball, same depth",
                "Sides should be sloped, not vertical",
                "Roughen sides to help roots penetrate",
                "Save topsoil separately from subsoil"
            ],
            'time_estimate_min': 30 if tree_size in ['sapling', '6ft'] else 45
        })

        # Step 3: Prepare Tree
        steps.append({
            'step_number': 3,
            'title': 'Prepare Tree',
            'instructions': [
                "Water tree thoroughly in container before removal",
                "Carefully remove from container (cut if needed)",
                "Gently loosen circling roots",
                "Remove broken or damaged roots",
                "Keep root ball moist and intact"
            ],
            'time_estimate_min': 10
        })

        # Step 4: Soil Amendment (if needed)
        soil_amendment_instructions = []
        if soil_type == 'clay':
            soil_amendment_instructions = [
                "Mix removed soil with compost (1:3 ratio)",
                "Add coarse sand to improve drainage",
                "Clay soil needs extra drainage improvement"
            ]
        elif soil_type == 'sandy':
            soil_amendment_instructions = [
                "Mix removed soil with compost (1:2 ratio)",
                "Add organic matter to improve water retention",
                "Sandy soil needs moisture-holding amendments"
            ]
        else:
            soil_amendment_instructions = [
                "Mix removed topsoil with compost (1:4 ratio)",
                "Use native soil for most of backfill",
                "Avoid excessive amendments"
            ]

        steps.append({
            'step_number': 4,
            'title': 'Prepare Soil Mix',
            'instructions': soil_amendment_instructions,
            'time_estimate_min': 10
        })

        # Step 5: Place Tree
        steps.append({
            'step_number': 5,
            'title': 'Position Tree',
            'instructions': [
                "Place tree in center of hole",
                "Ensure root flare is at or slightly above ground level",
                "Check depth - adjust if needed",
                "Rotate tree to best side faces viewing direction",
                "Keep tree vertical and straight"
            ],
            'time_estimate_min': 10
        })

        # Step 6: Backfill
        steps.append({
            'step_number': 6,
            'title': 'Backfill Hole',
            'instructions': [
                "Fill hole halfway with soil mix",
                "Gently tamp to remove air pockets (don't compact heavily)",
                "Water thoroughly to settle soil",
                "Fill remainder of hole",
                "Create shallow basin around tree to hold water"
            ],
            'time_estimate_min': 15
        })

        # Step 7: Stake (if large tree)
        if tree_size in ['8ft', '10ft']:
            steps.append({
                'step_number': 7,
                'title': 'Install Stakes',
                'instructions': [
                    "Drive 2-3 stakes outside root ball (2-3 ft away)",
                    "Position stakes perpendicular to prevailing wind",
                    "Attach tree with soft, wide straps",
                    "Allow some trunk movement (don't tie too tight)",
                    "Plan to remove stakes after 1 year"
                ],
                'time_estimate_min': 15
            })

        # Step 8: Mulch
        steps.append({
            'step_number': 7 if tree_size in ['sapling', '6ft'] else 8,
            'title': 'Apply Mulch',
            'instructions': [
                "Spread 2-4 inches of organic mulch",
                "Cover area 3-4 ft diameter around tree",
                "Keep mulch 2-3 inches away from trunk (no 'mulch volcanoes')",
                "Extend to drip line if possible",
                "Use wood chips, bark, or compost"
            ],
            'time_estimate_min': 10
        })

        # Step 9: Initial Watering
        watering_amount = {
            'sapling': '5-10',
            '6ft': '15-20',
            '8ft': '20-25',
            '10ft': '25-30'
        }

        steps.append({
            'step_number': 8 if tree_size in ['sapling', '6ft'] else 9,
            'title': 'Water Thoroughly',
            'instructions': [
                f"Water with {watering_amount.get(tree_size)} gallons",
                "Water slowly to allow soil absorption",
                "Fill basin and let soak in, repeat 2-3 times",
                "Ensure entire root ball is saturated",
                "Water daily for first week, then adjust based on conditions"
            ],
            'time_estimate_min': 15
        })

        return steps

    def _determine_best_planting_time(self, species: PlantSpecies) -> Dict[str, Any]:
        """Determine best planting time for species"""
        if species.tree_type == 'deciduous':
            return {
                'primary_season': 'Fall',
                'alternative_season': 'Early spring',
                'timing': 'September-November (fall) or March-April (spring)',
                'reason': 'Deciduous trees establish best when planted dormant',
                'avoid': 'Summer (heat stress) and late spring (active growth)'
            }
        elif species.tree_type == 'evergreen':
            return {
                'primary_season': 'Early fall',
                'alternative_season': 'Late spring',
                'timing': 'September-October (fall) or April-May (spring)',
                'reason': 'Evergreens need time to establish before winter',
                'avoid': 'Mid-summer and mid-winter'
            }
        else:  # conifer
            return {
                'primary_season': 'Spring',
                'alternative_season': 'Early fall',
                'timing': 'March-May (spring) or September-October (fall)',
                'reason': 'Plant when soil is workable and temperatures moderate',
                'avoid': 'Extreme heat or cold periods'
            }

    def _generate_site_notes(self, site_data: Dict[str, Any], species: PlantSpecies) -> List[str]:
        """Generate site-specific planting notes"""
        notes = []

        # NDVI-based notes
        ndvi = site_data.get('avg_ndvi', 0)
        if ndvi < 0.2:
            notes.append(
                f"⚠️ Low vegetation (NDVI: {ndvi:.2f}) - soil may be compacted or poor quality. "
                "Add 3-4 inches of compost to improve soil structure."
            )
        elif ndvi > 0.6:
            notes.append(
                f"Dense vegetation (NDVI: {ndvi:.2f}) - clear competing plants in 4-foot radius "
                "to reduce competition for water and nutrients."
            )

        # Slope-based notes
        slope = site_data.get('avg_slope', 0)
        if slope > 5:
            notes.append(
                f"Moderate slope ({slope:.1f}°) - plant on contour to prevent erosion. "
                "Consider building small berm downslope to catch water."
            )

        # Infrastructure notes
        if site_data.get('has_nearby_roads'):
            notes.append(
                "Roads nearby - consider installing root barrier to prevent future sidewalk/road damage."
            )

        return notes
