"""
Unit tests for EnvironmentalCalculatorTool
"""

import pytest
from agent.tools.environmental_calculator import EnvironmentalCalculatorTool


@pytest.mark.asyncio
class TestEnvironmentalCalculatorTool:
    """Test suite for EnvironmentalCalculatorTool"""

    async def test_tool_metadata(self, db_manager, cache_service):
        """Test that tool metadata is correctly defined"""
        tool = EnvironmentalCalculatorTool(db_manager, cache_service)

        assert tool.name == "environmental_calculator"
        assert "environmental benefits" in tool.description.lower()
        assert "species_id" in tool.input_schema["properties"]
        assert "quantity" in tool.input_schema["properties"]
        assert "years_projection" in tool.input_schema["properties"]

    async def test_basic_calculation(
        self,
        db_manager,
        cache_service,
        sample_species
    ):
        """Test basic environmental benefits calculation"""
        tool = EnvironmentalCalculatorTool(db_manager, cache_service)

        result = await tool.execute(
            species_id="PLAC",
            quantity=1,
            years_projection=20
        )

        assert "annual_benefits" in result
        assert "lifetime_benefits" in result
        assert "dollar_value" in result
        assert "equivalent_metrics" in result

        # Check that CO2 sequestration was calculated
        assert result["annual_benefits"]["co2_sequestration_kg"] > 0
        assert result["lifetime_benefits"]["co2_sequestration_kg"] > 0

    async def test_multiple_trees_calculation(
        self,
        db_manager,
        cache_service,
        sample_species
    ):
        """Test calculation for multiple trees"""
        tool = EnvironmentalCalculatorTool(db_manager, cache_service)

        # Calculate for 5 trees
        result = await tool.execute(
            species_id="PLAC",
            quantity=5,
            years_projection=20
        )

        # Lifetime benefits should be 5x annual for 20 years
        annual_co2 = result["annual_benefits"]["co2_sequestration_kg"]
        lifetime_co2 = result["lifetime_benefits"]["co2_sequestration_kg"]

        # Should be approximately (annual * 20 years * 5 trees * growth factor)
        assert lifetime_co2 > annual_co2 * 50  # At least 50x (conservative)

    async def test_growth_curve_projection(
        self,
        db_manager,
        cache_service,
        sample_species
    ):
        """Test that growth curve is applied over time"""
        tool = EnvironmentalCalculatorTool(db_manager, cache_service)

        # Young tree (2 years) should have lower benefits
        result_2yr = await tool.execute(
            species_id="PLAC",
            quantity=1,
            years_projection=2
        )

        # Mature projection (20 years) should have higher benefits
        result_20yr = await tool.execute(
            species_id="PLAC",
            quantity=1,
            years_projection=20
        )

        # 20-year projection should have much higher lifetime benefits
        assert result_20yr["lifetime_benefits"]["co2_sequestration_kg"] > \
               result_2yr["lifetime_benefits"]["co2_sequestration_kg"]

    async def test_dollar_value_conversion(
        self,
        db_manager,
        cache_service,
        sample_species
    ):
        """Test that environmental benefits are converted to dollar values"""
        tool = EnvironmentalCalculatorTool(db_manager, cache_service)

        result = await tool.execute(
            species_id="PLAC",
            quantity=1,
            years_projection=20
        )

        dollar_value = result["dollar_value"]

        # Should have all major categories
        assert "co2_value_usd" in dollar_value
        assert "stormwater_value_usd" in dollar_value
        assert "energy_savings_usd" in dollar_value
        assert "total_value_usd" in dollar_value

        # All values should be positive
        assert dollar_value["co2_value_usd"] > 0
        assert dollar_value["total_value_usd"] > 0

        # Total should be sum of components
        expected_total = (
            dollar_value["co2_value_usd"] +
            dollar_value["stormwater_value_usd"] +
            dollar_value["energy_savings_usd"] +
            dollar_value.get("air_quality_value_usd", 0)
        )
        assert abs(dollar_value["total_value_usd"] - expected_total) < 0.01

    async def test_equivalent_metrics(
        self,
        db_manager,
        cache_service,
        sample_species
    ):
        """Test that equivalent metrics are generated for user understanding"""
        tool = EnvironmentalCalculatorTool(db_manager, cache_service)

        result = await tool.execute(
            species_id="PLAC",
            quantity=1,
            years_projection=20
        )

        metrics = result["equivalent_metrics"]

        # Should have relatable comparisons
        assert "car_miles_offset" in metrics or "days_car_free" in metrics
        assert isinstance(metrics, dict)

    async def test_caching(
        self,
        db_manager,
        cache_service,
        sample_species
    ):
        """Test that calculations are cached"""
        tool = EnvironmentalCalculatorTool(db_manager, cache_service)

        # First call
        result1 = await tool.execute(
            species_id="PLAC",
            quantity=1,
            years_projection=20
        )

        # Second call with same parameters
        result2 = await tool.execute(
            species_id="PLAC",
            quantity=1,
            years_projection=20
        )

        # Results should be identical (from cache)
        assert result1 == result2

    async def test_invalid_species_id(
        self,
        db_manager,
        cache_service
    ):
        """Test handling of invalid species ID"""
        tool = EnvironmentalCalculatorTool(db_manager, cache_service)

        # Should handle gracefully
        with pytest.raises(Exception) as exc_info:
            await tool.execute(
                species_id="INVALID",
                quantity=1,
                years_projection=20
            )

        # Should provide helpful error message
        assert "not found" in str(exc_info.value).lower() or \
               "invalid" in str(exc_info.value).lower()

    async def test_zero_quantity(
        self,
        db_manager,
        cache_service,
        sample_species
    ):
        """Test behavior with zero quantity"""
        tool = EnvironmentalCalculatorTool(db_manager, cache_service)

        # Should handle edge case
        result = await tool.execute(
            species_id="PLAC",
            quantity=0,
            years_projection=20
        )

        # All benefits should be zero
        assert result["annual_benefits"]["co2_sequestration_kg"] == 0
        assert result["dollar_value"]["total_value_usd"] == 0
