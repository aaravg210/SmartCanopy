"""
Unit tests for SpeciesRecommenderTool
"""

import pytest
from agent.tools.species_recommender import SpeciesRecommenderTool
from agent.services.plant_database import PlantSpecies


@pytest.mark.asyncio
class TestSpeciesRecommenderTool:
    """Test suite for SpeciesRecommenderTool"""

    async def test_tool_metadata(self):
        """Test that tool metadata is correctly defined"""
        from agent.services.plant_database import DatabaseManager
        from agent.services.cache_service import CacheService

        db_manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
        cache_service = CacheService("redis://localhost:6379/15")

        tool = SpeciesRecommenderTool(db_manager, cache_service)

        assert tool.name == "species_recommender"
        assert "recommend tree species" in tool.description.lower()
        assert tool.input_schema["type"] == "object"
        assert "planting_site_id" in tool.input_schema["properties"]
        assert "zip_code" in tool.input_schema["properties"]

    async def test_hardiness_zone_filtering(
        self,
        db_manager,
        cache_service,
        sample_species,
        sample_planting_site,
        mock_hardiness_zone_api
    ):
        """Test that species are filtered by hardiness zone"""
        tool = SpeciesRecommenderTool(db_manager, cache_service)

        # Create additional species with different zones
        async with db_manager.get_session() as session:
            # Species that won't match zone 9b (too cold)
            cold_species = PlantSpecies(
                species_id="COLD",
                common_name="Cold Climate Tree",
                scientific_name="Coldus treeicus",
                tree_type="deciduous",
                hardiness_zone_min=2,
                hardiness_zone_max=5,  # Won't survive in 9b
                mature_height_ft=50,
                mature_spread_ft=30,
                growth_rate="medium",
                drought_tolerant=False,
                native_regions=["Northern US"],
                environmental_benefits={},
                pricing={},
                maintenance_notes={},
                planting_instructions={}
            )
            session.add(cold_species)
            await session.commit()

        # Run recommendation for ZIP 95123 (zone 9b)
        result = await tool.execute(
            planting_site_id=sample_planting_site["site_id"],
            zip_code="95123"
        )

        assert "recommendations" in result
        # Should only recommend American Sycamore (zone 4-9), not cold species (zone 2-5)
        species_names = [s["common_name"] for s in result["recommendations"]]
        assert "American Sycamore" in species_names
        assert "Cold Climate Tree" not in species_names

    async def test_space_constraint_filtering(
        self,
        db_manager,
        cache_service,
        sample_species,
        sample_planting_site
    ):
        """Test that species are filtered by available space"""
        tool = SpeciesRecommenderTool(db_manager, cache_service)

        # Create a large tree that won't fit
        async with db_manager.get_session() as session:
            large_tree = PlantSpecies(
                species_id="HUGE",
                common_name="Gigantic Oak",
                scientific_name="Quercus giganticus",
                tree_type="deciduous",
                hardiness_zone_min=4,
                hardiness_zone_max=9,
                mature_height_ft=150,  # Very tall
                mature_spread_ft=120,  # Very wide
                growth_rate="slow",
                drought_tolerant=False,
                native_regions=["Eastern US"],
                environmental_benefits={},
                pricing={},
                maintenance_notes={},
                planting_instructions={}
            )
            session.add(large_tree)
            await session.commit()

        # Test with small space constraint
        result = await tool.execute(
            planting_site_id=sample_planting_site["site_id"],
            zip_code="95123",
            space_constraint="small"
        )

        species_names = [s["common_name"] for s in result["recommendations"]]
        assert "Gigantic Oak" not in species_names

    async def test_purpose_matching(
        self,
        db_manager,
        cache_service,
        sample_species,
        sample_planting_site
    ):
        """Test that species are ranked by user preferences"""
        tool = SpeciesRecommenderTool(db_manager, cache_service)

        # American Sycamore has good shade and stormwater benefits
        result = await tool.execute(
            planting_site_id=sample_planting_site["site_id"],
            zip_code="95123",
            purpose=["shade", "stormwater"]
        )

        assert "recommendations" in result
        assert len(result["recommendations"]) > 0

        # Top recommendation should have shade/stormwater benefits
        top_rec = result["recommendations"][0]
        assert top_rec["common_name"] == "American Sycamore"

    async def test_ndvi_tolerance_matching(
        self,
        db_manager,
        cache_service,
        sample_species,
        sample_planting_site
    ):
        """Test that species match site NDVI conditions"""
        tool = SpeciesRecommenderTool(db_manager, cache_service)

        # Site has NDVI of 0.45 (moderate vegetation)
        result = await tool.execute(
            planting_site_id=sample_planting_site["site_id"],
            zip_code="95123"
        )

        assert "site_characteristics" in result
        assert result["site_characteristics"]["ndvi_category"] == "moderate_vegetation"

    async def test_drought_tolerance_filtering(
        self,
        db_manager,
        cache_service,
        sample_planting_site
    ):
        """Test filtering by drought tolerance"""
        tool = SpeciesRecommenderTool(db_manager, cache_service)

        # Create drought-tolerant species
        async with db_manager.get_session() as session:
            drought_species = PlantSpecies(
                species_id="DROUGHT",
                common_name="Desert Willow",
                scientific_name="Chilopsis linearis",
                tree_type="deciduous",
                hardiness_zone_min=7,
                hardiness_zone_max=9,
                mature_height_ft=25,
                mature_spread_ft=20,
                growth_rate="fast",
                drought_tolerant=True,  # Drought tolerant
                native_regions=["Southwestern US"],
                environmental_benefits={},
                pricing={},
                maintenance_notes={},
                planting_instructions={}
            )
            session.add(drought_species)
            await session.commit()

        # Request only drought-tolerant species
        result = await tool.execute(
            planting_site_id=sample_planting_site["site_id"],
            zip_code="95123",
            drought_tolerant_only=True
        )

        # All recommendations should be drought tolerant
        for species in result["recommendations"]:
            assert species.get("drought_tolerant") is True

    async def test_caching_behavior(
        self,
        db_manager,
        cache_service,
        sample_species,
        sample_planting_site,
        mock_hardiness_zone_api
    ):
        """Test that results are cached for performance"""
        tool = SpeciesRecommenderTool(db_manager, cache_service)

        # First call - should fetch from database
        result1 = await tool.execute(
            planting_site_id=sample_planting_site["site_id"],
            zip_code="95123"
        )

        # Second call with same parameters - should use cache
        result2 = await tool.execute(
            planting_site_id=sample_planting_site["site_id"],
            zip_code="95123"
        )

        # Results should be identical
        assert result1 == result2
        assert len(result1["recommendations"]) == len(result2["recommendations"])

    async def test_no_matching_species(
        self,
        db_manager,
        cache_service,
        sample_planting_site
    ):
        """Test behavior when no species match criteria"""
        tool = SpeciesRecommenderTool(db_manager, cache_service)

        # Request species for extreme hardiness zone with no matches
        result = await tool.execute(
            planting_site_id=sample_planting_site["site_id"],
            zip_code="10001",  # Zone 7b, but no species in DB for this zone
            min_height_ft=200  # Unrealistic requirement
        )

        assert "recommendations" in result
        # Should return empty list or error message, not crash
        assert isinstance(result["recommendations"], list)

    async def test_suitability_score_calculation(
        self,
        db_manager,
        cache_service,
        sample_species,
        sample_planting_site,
        mock_hardiness_zone_api
    ):
        """Test that suitability scores are calculated correctly"""
        tool = SpeciesRecommenderTool(db_manager, cache_service)

        result = await tool.execute(
            planting_site_id=sample_planting_site["site_id"],
            zip_code="95123"
        )

        # All recommendations should have suitability scores
        for species in result["recommendations"]:
            assert "suitability_score" in species
            assert 0 <= species["suitability_score"] <= 1

        # Recommendations should be sorted by score (descending)
        scores = [s["suitability_score"] for s in result["recommendations"]]
        assert scores == sorted(scores, reverse=True)
