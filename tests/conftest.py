"""
Pytest configuration and shared fixtures
"""

import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from agent.services.plant_database import DatabaseManager, Base
from agent.services.cache_service import CacheService
from agent.config import settings
import os

# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_REDIS_URL = "redis://localhost:6379/15"  # Use DB 15 for tests


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_manager() -> AsyncGenerator[DatabaseManager, None]:
    """
    Fixture that provides a clean database for each test.
    Uses in-memory SQLite for speed.
    """
    # Create test database manager
    test_db = DatabaseManager(TEST_DATABASE_URL)

    # Create all tables
    async with test_db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield test_db

    # Cleanup
    async with test_db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_db.engine.dispose()


@pytest.fixture(scope="function")
async def cache_service() -> AsyncGenerator[CacheService, None]:
    """
    Fixture that provides a clean Redis cache for each test.
    Uses separate DB to avoid conflicts.
    """
    cache = CacheService(TEST_REDIS_URL)

    # Clear the test database
    await cache.redis.flushdb()

    yield cache

    # Cleanup
    await cache.redis.flushdb()
    await cache.redis.close()


@pytest.fixture
async def sample_species(db_manager: DatabaseManager) -> Dict[str, Any]:
    """
    Create sample plant species for testing.
    Returns a dict with species data.
    """
    from agent.services.plant_database import PlantSpecies

    # Use field names that match the actual PlantSpecies model
    species_data = {
        "species_id": "PLAC",
        "common_name": "American Sycamore",
        "scientific_name": "Platanus occidentalis",
        "tree_type": "deciduous",
        "hardiness_zone_min": 4,
        "hardiness_zone_max": 9,
        "mature_height_ft_min": 70,
        "mature_height_ft_max": 100,
        "mature_spread_ft_min": 40,
        "mature_spread_ft_max": 70,
        "growth_rate": "fast",
        "drought_tolerant": False,
        "native_regions": ["Eastern US", "Midwest"],
        "co2_sequestration_kg_year": 95.2,
        "air_pollution_removal_kg_year": 12.4,
        "stormwater_gallons_year": 775.62,
        "energy_savings_kwh_year": 124.8,
        "price_sapling": 25.0,
        "price_6ft": 125.0,
        "price_8ft": 185.0,
        "price_10ft": 275.0,
        "maintenance_notes": {
            "watering": "Regular watering for first 2 years",
            "pruning": "Prune in late winter",
            "pests": ["Sycamore anthracnose", "Scale insects"]
        },
        "planting_instructions": "Plant in moist, well-drained soil. Full sun. Space 40ft apart."
    }

    async with db_manager.get_session() as session:
        species = PlantSpecies(**species_data)
        session.add(species)
        await session.commit()

    return species_data


@pytest.fixture
async def sample_planting_site(db_manager: DatabaseManager) -> Dict[str, Any]:
    """
    Create a sample planting site for testing.
    Returns a dict with site data.
    """
    from agent.services.plant_database import PlantingSite
    import uuid

    # Use field names that match the actual PlantingSite model
    site_data = {
        "site_id": str(uuid.uuid4()),
        "analysis_id": str(uuid.uuid4()),
        "address": "123 Main St, San Jose, CA 95123",
        "latitude": 37.2948,
        "longitude": -121.8700,
        "zip_code": "95123",
        "location_pixels": {"x": 256, "y": 256},
        "avg_ndvi": 0.45,
        "avg_slope": 3.2,
        "area_pixels": 250,
        "suitability_score": 0.78,
        "osm_data": {
            "roads": False,
            "buildings": False,
            "parking": False
        }
    }

    async with db_manager.get_session() as session:
        site = PlantingSite(**site_data)
        session.add(site)
        await session.commit()

    return site_data


@pytest.fixture
def mock_anthropic_response():
    """
    Mock response from Anthropic Claude API.
    """
    class MockMessage:
        def __init__(self, content, stop_reason="end_turn"):
            self.content = content
            self.stop_reason = stop_reason
            self.model = "claude-opus-4-5-20251101"
            self.usage = type('obj', (object,), {
                'input_tokens': 100,
                'output_tokens': 50
            })()

    class MockTextBlock:
        def __init__(self, text):
            self.type = "text"
            self.text = text

    return {
        "MockMessage": MockMessage,
        "MockTextBlock": MockTextBlock
    }


@pytest.fixture
def mock_hardiness_zone_api(monkeypatch):
    """
    Mock the hardiness zone API to avoid external calls during tests.
    """
    async def mock_get_zone(zip_code: str) -> str:
        # Simple mapping for common test cases
        zones = {
            "95123": "9b",
            "10001": "7b",
            "60601": "6a",
            "90210": "10a"
        }
        return zones.get(zip_code, "8a")  # Default to 8a

    from agent.services import hardiness_zone_api
    monkeypatch.setattr(hardiness_zone_api, "get_hardiness_zone", mock_get_zone)

    return mock_get_zone
