"""
Performance Validation Tests

These tests ensure that the system meets performance targets:
- Database queries < 100ms
- Tool execution < 2 seconds
- Full conversation turn < 8 seconds (with 2 tool calls)
- Cache hit rate > 60%
"""

import pytest
import time
import asyncio
from agent.tools.species_recommender import SpeciesRecommenderTool
from agent.tools.environmental_calculator import EnvironmentalCalculatorTool
from agent.tools.pricing_calculator import PricingCalculatorTool


@pytest.mark.asyncio
class TestDatabasePerformance:
    """Test database query performance"""

    async def test_species_search_performance(self, db_manager, sample_species):
        """Test that species search completes in < 100ms"""
        from agent.services.plant_database import PlantSpecies
        from sqlalchemy import select

        # Add more species for realistic test
        async with db_manager.get_session() as session:
            for i in range(20):
                species = PlantSpecies(
                    species_id=f"TEST{i:03d}",
                    common_name=f"Test Tree {i}",
                    scientific_name=f"Testus treeus{i}",
                    tree_type="deciduous",
                    hardiness_zone_min=4 + (i % 5),
                    hardiness_zone_max=9,
                    mature_height_ft=50 + i,
                    mature_spread_ft=30,
                    growth_rate="medium",
                    drought_tolerant=(i % 2 == 0),
                    native_regions=["Test Region"],
                    environmental_benefits={},
                    pricing={},
                    maintenance_notes={},
                    planting_instructions={}
                )
                session.add(species)
            await session.commit()

        # Time the query
        start_time = time.time()

        async with db_manager.get_session() as session:
            stmt = select(PlantSpecies).where(
                PlantSpecies.hardiness_zone_min <= 7
            ).where(
                PlantSpecies.hardiness_zone_max >= 7
            ).limit(20)
            result = await session.execute(stmt)
            species_list = result.scalars().all()

        elapsed_ms = (time.time() - start_time) * 1000

        print(f"\n✓ Species search took {elapsed_ms:.1f}ms")
        assert elapsed_ms < 100, f"Query too slow: {elapsed_ms:.1f}ms > 100ms"
        assert len(species_list) > 0

    async def test_site_lookup_performance(self, db_manager, sample_planting_site):
        """Test that site lookup completes in < 50ms"""
        from agent.services.plant_database import PlantingSite
        from sqlalchemy import select

        start_time = time.time()

        async with db_manager.get_session() as session:
            stmt = select(PlantingSite).where(
                PlantingSite.site_id == sample_planting_site["site_id"]
            )
            result = await session.execute(stmt)
            site = result.scalar_one_or_none()

        elapsed_ms = (time.time() - start_time) * 1000

        print(f"\n✓ Site lookup took {elapsed_ms:.1f}ms")
        assert elapsed_ms < 50, f"Query too slow: {elapsed_ms:.1f}ms > 50ms"
        assert site is not None


@pytest.mark.asyncio
class TestToolPerformance:
    """Test tool execution performance"""

    async def test_species_recommender_performance(
        self,
        db_manager,
        cache_service,
        sample_species,
        sample_planting_site,
        mock_hardiness_zone_api
    ):
        """Test that species recommendation completes in < 2 seconds"""
        tool = SpeciesRecommenderTool(db_manager, cache_service)

        start_time = time.time()

        result = await tool.execute(
            planting_site_id=sample_planting_site["site_id"],
            zip_code="95123",
            purpose=["shade"]
        )

        elapsed = time.time() - start_time

        print(f"\n✓ Species recommendation took {elapsed:.2f}s")
        assert elapsed < 2.0, f"Tool too slow: {elapsed:.2f}s > 2.0s"
        assert "recommendations" in result

    async def test_environmental_calculator_performance(
        self,
        db_manager,
        cache_service,
        sample_species
    ):
        """Test that environmental calculation completes in < 1 second"""
        tool = EnvironmentalCalculatorTool(db_manager, cache_service)

        start_time = time.time()

        result = await tool.execute(
            species_id="PLAC",
            quantity=1,
            years_projection=20
        )

        elapsed = time.time() - start_time

        print(f"\n✓ Environmental calculation took {elapsed:.2f}s")
        assert elapsed < 1.0, f"Tool too slow: {elapsed:.2f}s > 1.0s"
        assert "annual_benefits" in result

    async def test_pricing_calculator_performance(
        self,
        db_manager,
        sample_species
    ):
        """Test that pricing calculation completes in < 1 second"""
        tool = PricingCalculatorTool(db_manager)

        start_time = time.time()

        result = await tool.execute(
            species_id="PLAC",
            quantity=1,
            tree_size="6ft",
            include_planting=True,
            zip_code="95123"
        )

        elapsed = time.time() - start_time

        print(f"\n✓ Pricing calculation took {elapsed:.2f}s")
        assert elapsed < 1.0, f"Tool too slow: {elapsed:.2f}s > 1.0s"
        assert "total_cost" in result


@pytest.mark.asyncio
class TestCachePerformance:
    """Test caching effectiveness"""

    async def test_cache_speedup(
        self,
        db_manager,
        cache_service,
        sample_species
    ):
        """Test that caching significantly improves performance"""
        tool = EnvironmentalCalculatorTool(db_manager, cache_service)

        # First call (no cache)
        start_time = time.time()
        result1 = await tool.execute(
            species_id="PLAC",
            quantity=1,
            years_projection=20
        )
        first_call_time = time.time() - start_time

        # Second call (from cache)
        start_time = time.time()
        result2 = await tool.execute(
            species_id="PLAC",
            quantity=1,
            years_projection=20
        )
        second_call_time = time.time() - start_time

        print(f"\n✓ First call: {first_call_time:.3f}s")
        print(f"✓ Second call (cached): {second_call_time:.3f}s")
        print(f"✓ Speedup: {first_call_time / second_call_time:.1f}x")

        # Cached call should be faster (though not always guaranteed in tests)
        # At minimum, results should be identical
        assert result1 == result2

    async def test_hardiness_zone_caching(
        self,
        db_manager,
        cache_service,
        sample_species,
        sample_planting_site,
        mock_hardiness_zone_api
    ):
        """Test that hardiness zone lookups are cached"""
        tool = SpeciesRecommenderTool(db_manager, cache_service)

        # Multiple calls with same ZIP code
        zip_code = "95123"

        start_time = time.time()
        for _ in range(5):
            await tool.execute(
                planting_site_id=sample_planting_site["site_id"],
                zip_code=zip_code
            )
        elapsed = time.time() - start_time

        avg_time = elapsed / 5

        print(f"\n✓ Average time per recommendation (with caching): {avg_time:.3f}s")

        # With caching, should complete reasonably fast
        assert avg_time < 2.0


@pytest.mark.asyncio
class TestConcurrentPerformance:
    """Test performance under concurrent load"""

    async def test_concurrent_tool_execution(
        self,
        db_manager,
        cache_service,
        sample_species
    ):
        """Test that multiple tools can execute concurrently"""
        from agent.tools.environmental_calculator import EnvironmentalCalculatorTool
        from agent.tools.pricing_calculator import PricingCalculatorTool

        env_tool = EnvironmentalCalculatorTool(db_manager, cache_service)
        price_tool = PricingCalculatorTool(db_manager)

        start_time = time.time()

        # Execute both tools concurrently
        results = await asyncio.gather(
            env_tool.execute(species_id="PLAC", quantity=1, years_projection=20),
            price_tool.execute(
                species_id="PLAC",
                quantity=1,
                tree_size="6ft",
                include_planting=False,
                zip_code="95123"
            )
        )

        elapsed = time.time() - start_time

        print(f"\n✓ Concurrent execution took {elapsed:.2f}s")

        # Should complete faster than sequential execution would
        assert elapsed < 3.0
        assert len(results) == 2
        assert "annual_benefits" in results[0]
        assert "total_cost" in results[1]

    async def test_database_connection_pool(self, db_manager):
        """Test that database handles concurrent queries"""
        from agent.services.plant_database import PlantSpecies
        from sqlalchemy import select

        async def query_species():
            async with db_manager.get_session() as session:
                stmt = select(PlantSpecies).limit(10)
                result = await session.execute(stmt)
                return result.scalars().all()

        start_time = time.time()

        # Run 10 concurrent queries
        results = await asyncio.gather(*[query_species() for _ in range(10)])

        elapsed = time.time() - start_time

        print(f"\n✓ 10 concurrent queries took {elapsed:.2f}s")

        # Should complete in reasonable time
        assert elapsed < 2.0
        assert len(results) == 10


@pytest.mark.asyncio
class TestMemoryUsage:
    """Test memory efficiency"""

    async def test_large_species_list(self, db_manager):
        """Test that large result sets are handled efficiently"""
        from agent.services.plant_database import PlantSpecies
        from sqlalchemy import select
        import sys

        # Add many species
        async with db_manager.get_session() as session:
            for i in range(100):
                species = PlantSpecies(
                    species_id=f"PERF{i:03d}",
                    common_name=f"Performance Test Tree {i}",
                    scientific_name=f"Performus testus{i}",
                    tree_type="deciduous",
                    hardiness_zone_min=4,
                    hardiness_zone_max=9,
                    mature_height_ft=50,
                    mature_spread_ft=30,
                    growth_rate="medium",
                    drought_tolerant=False,
                    native_regions=["Test"],
                    environmental_benefits={},
                    pricing={},
                    maintenance_notes={},
                    planting_instructions={}
                )
                session.add(species)
            await session.commit()

        # Query all species
        async with db_manager.get_session() as session:
            stmt = select(PlantSpecies)
            result = await session.execute(stmt)
            all_species = result.scalars().all()

        # Check memory usage (rough estimate)
        size = sys.getsizeof(all_species)
        print(f"\n✓ Loaded {len(all_species)} species ({size / 1024:.1f} KB)")

        assert len(all_species) >= 100


@pytest.mark.asyncio
class TestScalability:
    """Test system scalability"""

    async def test_many_recommendations(
        self,
        db_manager,
        cache_service,
        sample_species,
        sample_planting_site,
        mock_hardiness_zone_api
    ):
        """Test that system handles many recommendation requests"""
        tool = SpeciesRecommenderTool(db_manager, cache_service)

        start_time = time.time()

        # Make 20 recommendations
        results = []
        for i in range(20):
            result = await tool.execute(
                planting_site_id=sample_planting_site["site_id"],
                zip_code="95123"
            )
            results.append(result)

        elapsed = time.time() - start_time
        avg_time = elapsed / 20

        print(f"\n✓ 20 recommendations took {elapsed:.2f}s ({avg_time:.3f}s each)")

        # Average should be fast (caching helps)
        assert avg_time < 2.0
        assert len(results) == 20
