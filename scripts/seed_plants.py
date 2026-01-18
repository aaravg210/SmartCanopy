"""
Seed plant species database with initial data
Fetches data from USDA PLANTS and i-Tree APIs
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.services.plant_database import DatabaseManager, PlantSpecies
from agent.config import settings
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Sample tree species data (curated list of common urban trees)
SAMPLE_SPECIES = [
    {
        'species_id': 'ACPL',
        'scientific_name': 'Acer platanoides',
        'common_name': 'Norway Maple',
        'family': 'Sapindaceae',
        'mature_height_ft_min': 40,
        'mature_height_ft_max': 50,
        'mature_spread_ft_min': 30,
        'mature_spread_ft_max': 40,
        'growth_rate': 'medium',
        'hardiness_zone_min': 4,
        'hardiness_zone_max': 7,
        'sunlight': 'full_sun',
        'soil_types': ['clay', 'loam', 'sandy'],
        'moisture_tolerance': 'medium',
        'drought_tolerant': False,
        'co2_sequestration_kg_year': 115.0,
        'air_pollution_removal_kg_year': 2.8,
        'stormwater_gallons_year': 920,
        'energy_savings_kwh_year': 42,
        'native_regions': [],
        'tree_type': 'deciduous',
        'purposes': ['shade', 'street_tree'],
        'maintenance_level': 'medium',
        'pest_resistance': 'medium',
        'disease_resistance': 'medium',
        'price_sapling': 25.0,
        'price_6ft': 85.0,
        'price_8ft': 145.0,
        'price_10ft': 225.0,
        'description': 'Widely planted street tree with dense, rounded crown. Tolerates urban conditions well.',
        'planting_instructions': 'Plant in fall or early spring. Dig hole 2-3x wider than root ball.',
        'maintenance_notes': {
            'watering': {'frequency': '2-3x weekly for first 2 years', 'amount_gallons': 15},
            'pruning': 'Prune in late winter to maintain structure',
            'pests': ['aphids', 'scale']
        }
    },
    {
        'species_id': 'PLOC',
        'scientific_name': 'Platanus occidentalis',
        'common_name': 'American Sycamore',
        'family': 'Platanaceae',
        'mature_height_ft_min': 75,
        'mature_height_ft_max': 100,
        'mature_spread_ft_min': 50,
        'mature_spread_ft_max': 70,
        'growth_rate': 'fast',
        'hardiness_zone_min': 4,
        'hardiness_zone_max': 9,
        'sunlight': 'full_sun',
        'soil_types': ['clay', 'loam'],
        'moisture_tolerance': 'wet',
        'drought_tolerant': False,
        'co2_sequestration_kg_year': 195.0,
        'air_pollution_removal_kg_year': 4.5,
        'stormwater_gallons_year': 1580,
        'energy_savings_kwh_year': 68,
        'native_regions': ['southeast', 'midwest'],
        'tree_type': 'deciduous',
        'purposes': ['shade', 'wildlife'],
        'maintenance_level': 'low',
        'pest_resistance': 'high',
        'disease_resistance': 'medium',
        'price_sapling': 30.0,
        'price_6ft': 95.0,
        'price_8ft': 165.0,
        'price_10ft': 250.0,
        'description': 'Large native tree with distinctive white bark. Excellent for large spaces.',
        'planting_instructions': 'Requires ample space. Plant away from buildings and power lines.',
        'maintenance_notes': {
            'watering': {'frequency': 'weekly for first year', 'amount_gallons': 20},
            'pruning': 'Minimal pruning needed',
            'pests': ['anthracnose']
        }
    },
    {
        'species_id': 'QULO',
        'scientific_name': 'Quercus lobata',
        'common_name': 'Valley Oak',
        'family': 'Fagaceae',
        'mature_height_ft_min': 40,
        'mature_height_ft_max': 70,
        'mature_spread_ft_min': 60,
        'mature_spread_ft_max': 100,
        'growth_rate': 'slow',
        'hardiness_zone_min': 7,
        'hardiness_zone_max': 10,
        'sunlight': 'full_sun',
        'soil_types': ['loam', 'sandy'],
        'moisture_tolerance': 'medium',
        'drought_tolerant': True,
        'co2_sequestration_kg_year': 145.0,
        'air_pollution_removal_kg_year': 3.2,
        'stormwater_gallons_year': 1240,
        'energy_savings_kwh_year': 55,
        'native_regions': ['california'],
        'tree_type': 'deciduous',
        'purposes': ['shade', 'wildlife', 'aesthetic'],
        'maintenance_level': 'low',
        'pest_resistance': 'high',
        'disease_resistance': 'high',
        'price_sapling': 35.0,
        'price_6ft': 110.0,
        'price_8ft': 185.0,
        'price_10ft': 275.0,
        'description': 'California native oak with massive spreading canopy. Iconic landscape tree.',
        'planting_instructions': 'Plant in fall. Do not irrigate near trunk once established.',
        'maintenance_notes': {
            'watering': {'frequency': 'deep watering monthly in summer', 'amount_gallons': 25},
            'pruning': 'Prune only when necessary',
            'pests': ['oak moth']
        }
    },
    {
        'species_id': 'COJA',
        'scientific_name': 'Cornus florida',
        'common_name': 'Flowering Dogwood',
        'family': 'Cornaceae',
        'mature_height_ft_min': 15,
        'mature_height_ft_max': 30,
        'mature_spread_ft_min': 15,
        'mature_spread_ft_max': 30,
        'growth_rate': 'medium',
        'hardiness_zone_min': 5,
        'hardiness_zone_max': 9,
        'sunlight': 'partial_shade',
        'soil_types': ['loam'],
        'moisture_tolerance': 'medium',
        'drought_tolerant': False,
        'co2_sequestration_kg_year': 42.0,
        'air_pollution_removal_kg_year': 1.1,
        'stormwater_gallons_year': 380,
        'energy_savings_kwh_year': 18,
        'native_regions': ['southeast', 'midwest'],
        'tree_type': 'deciduous',
        'purposes': ['ornamental', 'wildlife', 'aesthetic'],
        'maintenance_level': 'medium',
        'pest_resistance': 'medium',
        'disease_resistance': 'medium',
        'price_sapling': 40.0,
        'price_6ft': 125.0,
        'price_8ft': 195.0,
        'price_10ft': 285.0,
        'description': 'Small ornamental tree with beautiful spring flowers. Excellent for understory planting.',
        'planting_instructions': 'Plant in partial shade with acidic, well-drained soil.',
        'maintenance_notes': {
            'watering': {'frequency': '2x weekly', 'amount_gallons': 10},
            'pruning': 'Prune after flowering',
            'pests': ['dogwood borer', 'anthracnose']
        }
    },
    {
        'species_id': 'PIST',
        'scientific_name': 'Pinus strobus',
        'common_name': 'Eastern White Pine',
        'family': 'Pinaceae',
        'mature_height_ft_min': 50,
        'mature_height_ft_max': 80,
        'mature_spread_ft_min': 20,
        'mature_spread_ft_max': 40,
        'growth_rate': 'fast',
        'hardiness_zone_min': 3,
        'hardiness_zone_max': 8,
        'sunlight': 'full_sun',
        'soil_types': ['loam', 'sandy'],
        'moisture_tolerance': 'medium',
        'drought_tolerant': False,
        'co2_sequestration_kg_year': 165.0,
        'air_pollution_removal_kg_year': 3.8,
        'stormwater_gallons_year': 1420,
        'energy_savings_kwh_year': 62,
        'native_regions': ['northeast', 'midwest'],
        'tree_type': 'conifer',
        'purposes': ['privacy', 'windbreak', 'wildlife'],
        'maintenance_level': 'low',
        'pest_resistance': 'medium',
        'disease_resistance': 'medium',
        'price_sapling': 28.0,
        'price_6ft': 90.0,
        'price_8ft': 155.0,
        'price_10ft': 235.0,
        'description': 'Fast-growing evergreen with soft needles. Excellent for privacy screens.',
        'planting_instructions': 'Plant in spring. Provide wind protection when young.',
        'maintenance_notes': {
            'watering': {'frequency': 'weekly for first 2 years', 'amount_gallons': 15},
            'pruning': 'Shape in early spring if needed',
            'pests': ['white pine weevil']
        }
    }
]


async def seed_database():
    """Seed database with sample plant species"""
    logger.info("Starting database seeding...")

    # Initialize database manager
    db_manager = DatabaseManager(settings.database_url)

    # Create tables if they don't exist
    try:
        await db_manager.create_tables()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return

    # Insert species
    async with db_manager.get_session() as session:
        try:
            for species_data in SAMPLE_SPECIES:
                # Check if species already exists
                from sqlalchemy import select
                stmt = select(PlantSpecies).where(
                    PlantSpecies.species_id == species_data['species_id']
                )
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    logger.info(f"Species {species_data['species_id']} already exists, skipping")
                    continue

                # Create new species
                species = PlantSpecies(**species_data)
                session.add(species)
                logger.info(f"Added species: {species_data['common_name']}")

            await session.commit()
            logger.info(f"Successfully seeded {len(SAMPLE_SPECIES)} species")

        except Exception as e:
            logger.error(f"Error seeding database: {e}")
            await session.rollback()
            raise

    logger.info("Database seeding complete!")


async def fetch_from_itree(species_id: str):
    """
    Fetch environmental benefits from i-Tree API

    Args:
        species_id: USDA plant symbol

    Returns:
        Environmental benefits data or None
    """
    try:
        url = f"{settings.itree_species_api_url}/{species_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"i-Tree API returned {response.status_code} for {species_id}")
                return None
    except Exception as e:
        logger.warning(f"Error fetching from i-Tree for {species_id}: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(seed_database())
