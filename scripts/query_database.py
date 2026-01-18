"""
Simple database query script
Usage: python scripts/query_database.py
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.services.plant_database import DatabaseManager, PlantSpecies, PlantingSite
from agent.config import settings
from sqlalchemy import select, func
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def query_examples():
    """Run example database queries"""

    db_manager = DatabaseManager(settings.database_url)

    async with db_manager.get_session() as session:

        # Example 1: Count all species
        print("\n" + "="*60)
        print("EXAMPLE 1: Count all plant species")
        print("="*60)
        stmt = select(func.count(PlantSpecies.species_id))
        result = await session.execute(stmt)
        count = result.scalar()
        print(f"Total species in database: {count}")

        # Example 2: List all species
        print("\n" + "="*60)
        print("EXAMPLE 2: List all species")
        print("="*60)
        stmt = select(PlantSpecies).order_by(PlantSpecies.common_name)
        result = await session.execute(stmt)
        species_list = result.scalars().all()

        for species in species_list:
            print(f"\n{species.common_name} ({species.scientific_name})")
            print(f"  ID: {species.species_id}")
            print(f"  Height: {species.mature_height_ft_min}-{species.mature_height_ft_max} ft")
            print(f"  Hardiness: Zones {species.hardiness_zone_min}-{species.hardiness_zone_max}")
            print(f"  CO2 Sequestration: {species.co2_sequestration_kg_year} kg/year")
            print(f"  Price (sapling): ${species.price_sapling}")

        # Example 3: Filter by hardiness zone
        print("\n" + "="*60)
        print("EXAMPLE 3: Find species for hardiness zone 7")
        print("="*60)
        stmt = select(PlantSpecies).where(
            PlantSpecies.hardiness_zone_min <= 7,
            PlantSpecies.hardiness_zone_max >= 7
        )
        result = await session.execute(stmt)
        zone7_species = result.scalars().all()

        print(f"Found {len(zone7_species)} species suitable for zone 7:")
        for species in zone7_species:
            print(f"  - {species.common_name}")

        # Example 4: Find native species
        print("\n" + "="*60)
        print("EXAMPLE 4: Find native species")
        print("="*60)
        stmt = select(PlantSpecies).where(
            func.jsonb_array_length(PlantSpecies.native_regions) > 0
        )
        result = await session.execute(stmt)
        native_species = result.scalars().all()

        print(f"Found {len(native_species)} native species:")
        for species in native_species:
            regions = species.native_regions or []
            print(f"  - {species.common_name}: {', '.join(regions)}")

        # Example 5: Top CO2 sequestration
        print("\n" + "="*60)
        print("EXAMPLE 5: Top 3 trees for CO2 sequestration")
        print("="*60)
        stmt = select(PlantSpecies).order_by(
            PlantSpecies.co2_sequestration_kg_year.desc()
        ).limit(3)
        result = await session.execute(stmt)
        top_co2 = result.scalars().all()

        for i, species in enumerate(top_co2, 1):
            print(f"{i}. {species.common_name}: {species.co2_sequestration_kg_year} kg/year")

        # Example 6: Count planting sites
        print("\n" + "="*60)
        print("EXAMPLE 6: Count planting sites")
        print("="*60)
        stmt = select(func.count(PlantingSite.site_id))
        result = await session.execute(stmt)
        site_count = result.scalar()
        print(f"Total planting sites analyzed: {site_count}")


async def custom_query(query: str):
    """Run a custom SQL query"""
    db_manager = DatabaseManager(settings.database_url)

    async with db_manager.get_session() as session:
        result = await session.execute(query)
        rows = result.fetchall()

        print(f"\nQuery Results ({len(rows)} rows):")
        for row in rows:
            print(row)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SMARTCANOPY DATABASE QUERY EXAMPLES")
    print("="*60)

    try:
        asyncio.run(query_examples())
        print("\n" + "="*60)
        print("Query examples completed successfully!")
        print("="*60 + "\n")
    except Exception as e:
        logger.error(f"Error running queries: {e}")
        print("\nMake sure:")
        print("1. Database is running (docker-compose up -d postgres)")
        print("2. Database has been seeded (python scripts/seed_plants.py)")
        print("3. .env file is configured with correct DATABASE_URL")
