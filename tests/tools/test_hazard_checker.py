"""
Unit tests for HazardCheckerTool
"""

import pytest
from agent.tools.hazard_checker import HazardCheckerTool


@pytest.mark.asyncio
class TestHazardCheckerTool:
    """Test suite for HazardCheckerTool"""

    async def test_safe_planting_site(self, db_manager, sample_planting_site):
        """Test a site with no hazards"""
        tool = HazardCheckerTool(db_manager)

        # Site has no roads/buildings nearby
        result = await tool.execute(
            planting_site_id=sample_planting_site["site_id"],
            mature_tree_height_ft=50,
            mature_spread_ft=30
        )

        assert "safe_to_plant" in result
        assert "warnings" in result
        assert "clearances" in result
        assert "recommendations" in result

        # Should be safe to plant
        assert result["safe_to_plant"] is True

    async def test_utility_line_warning(self, db_manager):
        """Test warning for trees that might interfere with utilities"""
        from agent.services.plant_database import PlantingSite
        import uuid

        # Create site near utilities
        site_data = {
            "site_id": str(uuid.uuid4()),
            "analysis_id": str(uuid.uuid4()),
            "address": "456 Oak St, San Jose, CA 95123",
            "latitude": 37.3,
            "longitude": -121.87,
            "location_pixels": {"x": 200, "y": 200},
            "avg_ndvi": 0.4,
            "ndvi_category": "moderate_vegetation",
            "avg_slope": 2.0,
            "slope_category": "flat",
            "area_pixels": 200,
            "suitability_score": 0.7,
            "osm_data": {
                "power_lines": True,  # Has overhead utilities
                "roads": False,
                "buildings": False
            }
        }

        async with db_manager.get_session() as session:
            site = PlantingSite(**site_data)
            session.add(site)
            await session.commit()

        tool = HazardCheckerTool(db_manager)

        # Tall tree near power lines
        result = await tool.execute(
            planting_site_id=site_data["site_id"],
            mature_tree_height_ft=60,  # Tall tree
            mature_spread_ft=40
        )

        # Should have warnings about utilities
        assert len(result["warnings"]) > 0
        warnings_text = " ".join(result["warnings"]).lower()
        assert "util" in warnings_text or "power" in warnings_text or "overhead" in warnings_text

    async def test_call_811_reminder(self, db_manager, sample_planting_site):
        """Test that 811 reminder is always included"""
        tool = HazardCheckerTool(db_manager)

        result = await tool.execute(
            planting_site_id=sample_planting_site["site_id"],
            mature_tree_height_ft=50,
            mature_spread_ft=30
        )

        # Should always remind to call 811
        recommendations_text = " ".join(result["recommendations"]).lower()
        assert "811" in recommendations_text

    async def test_clearance_calculations(self, db_manager, sample_planting_site):
        """Test that clearance distances are calculated"""
        tool = HazardCheckerTool(db_manager)

        result = await tool.execute(
            planting_site_id=sample_planting_site["site_id"],
            mature_tree_height_ft=50,
            mature_spread_ft=30
        )

        clearances = result["clearances"]

        # Should have clearance measurements
        assert isinstance(clearances, dict)
        # May include: buildings, roads, sidewalks, utilities
