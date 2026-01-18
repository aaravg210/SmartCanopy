"""
Unit tests for PricingCalculatorTool
"""

import pytest
from agent.tools.pricing_calculator import PricingCalculatorTool


@pytest.mark.asyncio
class TestPricingCalculatorTool:
    """Test suite for PricingCalculatorTool"""

    async def test_basic_pricing(self, db_manager, sample_species):
        """Test basic price calculation"""
        tool = PricingCalculatorTool(db_manager)

        result = await tool.execute(
            species_id="PLAC",
            quantity=1,
            tree_size="6ft",
            include_planting=False,
            zip_code="95123"
        )

        assert "breakdown" in result
        assert "cost_per_tree" in result
        assert "total_cost" in result
        assert result["total_cost"] > 0

    async def test_bulk_discount(self, db_manager, sample_species):
        """Test that bulk discounts are applied"""
        tool = PricingCalculatorTool(db_manager)

        # Single tree
        result_1 = await tool.execute(
            species_id="PLAC",
            quantity=1,
            tree_size="6ft",
            include_planting=False,
            zip_code="95123"
        )

        # 10 trees (should get 10% discount)
        result_10 = await tool.execute(
            species_id="PLAC",
            quantity=10,
            tree_size="6ft",
            include_planting=False,
            zip_code="95123"
        )

        # Cost per tree should be lower with bulk order
        assert result_10["cost_per_tree"] < result_1["cost_per_tree"]

    async def test_planting_labor_cost(self, db_manager, sample_species):
        """Test that planting labor is added when requested"""
        tool = PricingCalculatorTool(db_manager)

        result_no_planting = await tool.execute(
            species_id="PLAC",
            quantity=1,
            tree_size="6ft",
            include_planting=False,
            zip_code="95123"
        )

        result_with_planting = await tool.execute(
            species_id="PLAC",
            quantity=1,
            tree_size="6ft",
            include_planting=True,
            zip_code="95123"
        )

        # With planting should be more expensive
        assert result_with_planting["total_cost"] > result_no_planting["total_cost"]

    async def test_regional_pricing(self, db_manager, sample_species):
        """Test that regional multipliers are applied"""
        tool = PricingCalculatorTool(db_manager)

        # California (higher cost)
        result_ca = await tool.execute(
            species_id="PLAC",
            quantity=1,
            tree_size="6ft",
            include_planting=False,
            zip_code="95123"  # CA
        )

        # Texas (lower cost)
        result_tx = await tool.execute(
            species_id="PLAC",
            quantity=1,
            tree_size="6ft",
            include_planting=False,
            zip_code="78701"  # TX
        )

        # CA should be more expensive (1.3x multiplier vs 0.9x)
        assert result_ca["total_cost"] > result_tx["total_cost"]

    async def test_tree_size_pricing(self, db_manager, sample_species):
        """Test that larger trees cost more"""
        tool = PricingCalculatorTool(db_manager)

        sizes = ["sapling", "6ft", "8ft", "10ft"]
        costs = []

        for size in sizes:
            result = await tool.execute(
                species_id="PLAC",
                quantity=1,
                tree_size=size,
                include_planting=False,
                zip_code="95123"
            )
            costs.append(result["total_cost"])

        # Costs should increase with size
        assert costs == sorted(costs)
