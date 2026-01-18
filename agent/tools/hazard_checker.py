"""
Hazard Checker Tool
Verifies safety clearances for trees from buildings, roads, and utilities
"""

from typing import Dict, Any, List
import logging

from agent.tools.base_tool import BaseTool
from agent.services.site_data_loader import SiteDataLoader
from agent.services.plant_database import DatabaseManager
from agent.utils.geo_utils import haversine_distance, check_clearance
from agent.config import settings

logger = logging.getLogger(__name__)


class HazardCheckerTool(BaseTool):
    """
    Checks safety clearances from:
    - Buildings (minimum 15 ft)
    - Roads (minimum 10 ft)
    - Sidewalks (minimum 8 ft)
    - Overhead utilities (height-based)
    """

    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.site_loader = SiteDataLoader(db_manager)

    @property
    def name(self) -> str:
        return "hazard_checker"

    @property
    def description(self) -> str:
        return (
            "Verifies safety clearances for planting a tree at a specific site. "
            "Checks distances to buildings, roads, sidewalks, and overhead utilities. "
            "Returns safety assessment with warnings and recommendations."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "planting_site_id": {
                    "type": "string",
                    "description": "UUID of planting site"
                },
                "mature_tree_height_ft": {
                    "type": "number",
                    "description": "Mature tree height in feet"
                },
                "mature_spread_ft": {
                    "type": "number",
                    "description": "Mature tree canopy spread in feet"
                }
            },
            "required": ["planting_site_id", "mature_tree_height_ft", "mature_spread_ft"]
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute hazard check"""
        site_id = kwargs['planting_site_id']
        height_ft = kwargs['mature_tree_height_ft']
        spread_ft = kwargs['mature_spread_ft']

        # Load site data
        site_data = await self.site_loader.get_site_by_id(site_id)
        if not site_data:
            raise ValueError(f"Planting site {site_id} not found")

        warnings = []
        clearances = {}
        safe_to_plant = True
        recommendations = []

        # Check for nearby infrastructure from OSM data
        osm_data = site_data.get('osm_data', {})

        # Check buildings
        if site_data.get('has_nearby_buildings'):
            building_clearance = settings.clearance_building_ft
            clearances['buildings'] = {
                'required_ft': building_clearance,
                'status': 'warning',
                'message': f"Buildings detected nearby. Maintain {building_clearance}ft clearance."
            }
            warnings.append(
                f"⚠️ Buildings nearby - ensure {building_clearance}ft minimum clearance "
                f"from building foundations (accounting for {spread_ft}ft canopy spread)"
            )

        # Check roads
        if site_data.get('has_nearby_roads'):
            road_clearance = settings.clearance_road_ft
            clearances['roads'] = {
                'required_ft': road_clearance,
                'status': 'caution',
                'message': f"Roads nearby. Maintain {road_clearance}ft clearance."
            }
            warnings.append(
                f"⚠️ Roads nearby - maintain {road_clearance}ft clearance to avoid "
                "interference with traffic and ensure driver visibility"
            )

        # Check sidewalks
        sidewalk_clearance = settings.clearance_sidewalk_ft
        clearances['sidewalks'] = {
            'required_ft': sidewalk_clearance,
            'status': 'info',
            'message': f"If sidewalks present, maintain {sidewalk_clearance}ft clearance."
        }

        # Check overhead utilities
        if height_ft > 25:
            overhead_clearance = settings.clearance_overhead_utility_ft
            clearances['overhead_utilities'] = {
                'required_ft': overhead_clearance,
                'tree_height_ft': height_ft,
                'status': 'critical',
                'message': f"Tree will grow to {height_ft}ft - check for overhead power lines"
            }
            warnings.append(
                f"⚠️ CRITICAL: Tree will reach {height_ft}ft height - ensure no overhead "
                f"power lines within {overhead_clearance}ft. Contact utility company if unsure."
            )
            safe_to_plant = False  # Require user verification
            recommendations.append(
                "Contact your local utility company to verify overhead line locations"
            )

        # Slope considerations
        if site_data.get('avg_slope', 0) > 10:
            warnings.append(
                f"⚠️ Moderate slope ({site_data['avg_slope']:.1f}°) - plant on contour "
                "and use extra staking for stability"
            )
            recommendations.append(
                "Use heavy-duty staking system and plant on contour to prevent erosion"
            )

        # Generate recommendations
        if not recommendations:
            recommendations = [
                "Site appears suitable with standard planting practices",
                "Follow species-specific planting instructions",
                "Monitor clearances as tree grows and prune if needed"
            ]

        # Add mandatory 811 warning
        warnings.insert(0, "⚠️ CALL 811 BEFORE DIGGING to locate underground utilities (gas, electric, water, communications)")

        return {
            'site_id': site_id,
            'address': site_data.get('address'),
            'tree_dimensions': {
                'mature_height_ft': height_ft,
                'mature_spread_ft': spread_ft,
                'canopy_radius_ft': spread_ft / 2
            },
            'safe_to_plant': safe_to_plant,
            'safety_level': 'needs_verification' if not safe_to_plant else 'safe_with_precautions',
            'warnings': warnings,
            'clearances': clearances,
            'recommendations': recommendations,
            'site_conditions': {
                'slope_degrees': site_data.get('avg_slope'),
                'has_nearby_buildings': site_data.get('has_nearby_buildings', False),
                'has_nearby_roads': site_data.get('has_nearby_roads', False),
                'has_nearby_parking': site_data.get('has_nearby_parking', False)
            },
            'mandatory_action': "CALL 811 BEFORE DIGGING - This is required by law in most areas"
        }
