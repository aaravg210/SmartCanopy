"""
Tool Factory
Creates all agent tools with proper dependency injection
"""

from typing import List, Optional
import logging

from agent.tools.base_tool import BaseTool
from agent.tools.species_recommender import SpeciesRecommenderTool
from agent.tools.pricing_calculator import PricingCalculatorTool
from agent.tools.environmental_calculator import EnvironmentalCalculatorTool
from agent.tools.hazard_checker import HazardCheckerTool
from agent.tools.maintenance_guide import MaintenanceGuideTool
from agent.tools.planting_instructions import PlantingInstructionsTool
from agent.tools.photo_analyzer import PhotoAnalyzerTool
from agent.services.plant_database import DatabaseManager
from agent.services.cache_service import CacheService

logger = logging.getLogger(__name__)


def create_all_tools(
    db_manager: DatabaseManager,
    cache_service: Optional[CacheService] = None,
    include_photo_analyzer: bool = True
) -> List[BaseTool]:
    """
    Create all SmartCanopy agent tools with dependencies.

    Args:
        db_manager: Database manager for data access
        cache_service: Optional cache service for performance
        include_photo_analyzer: Whether to include photo analyzer (requires API key)

    Returns:
        List of initialized tool instances

    Example:
        >>> from agent.services.plant_database import DatabaseManager
        >>> from agent.services.cache_service import CacheService
        >>> from agent.config import settings
        >>>
        >>> db_manager = DatabaseManager(settings.database_url)
        >>> cache_service = CacheService(settings.redis_url)
        >>> tools = create_all_tools(db_manager, cache_service)
    """
    tools: List[BaseTool] = []

    # 1. Species Recommender - recommends trees based on site/climate/preferences
    tools.append(SpeciesRecommenderTool(db_manager, cache_service))
    logger.debug("Created SpeciesRecommenderTool")

    # 2. Pricing Calculator - calculates costs for trees and installation
    tools.append(PricingCalculatorTool(db_manager))
    logger.debug("Created PricingCalculatorTool")

    # 3. Environmental Calculator - calculates CO2, stormwater, etc. benefits
    tools.append(EnvironmentalCalculatorTool(db_manager, cache_service))
    logger.debug("Created EnvironmentalCalculatorTool")

    # 4. Hazard Checker - verifies safety clearances from utilities/buildings
    tools.append(HazardCheckerTool(db_manager))
    logger.debug("Created HazardCheckerTool")

    # 5. Maintenance Guide - provides care instructions by species/age/season
    tools.append(MaintenanceGuideTool(db_manager))
    logger.debug("Created MaintenanceGuideTool")

    # 6. Planting Instructions - generates step-by-step planting guides
    tools.append(PlantingInstructionsTool(db_manager))
    logger.debug("Created PlantingInstructionsTool")

    # 7. Photo Analyzer - analyzes site photos using Claude Vision
    if include_photo_analyzer:
        try:
            tools.append(PhotoAnalyzerTool())
            logger.debug("Created PhotoAnalyzerTool")
        except Exception as e:
            logger.warning(f"Could not create PhotoAnalyzerTool: {e}")

    logger.info(f"Created {len(tools)} tools")
    return tools


def create_database_tools(
    db_manager: DatabaseManager,
    cache_service: Optional[CacheService] = None
) -> List[BaseTool]:
    """
    Create only tools that require database access.
    Excludes PhotoAnalyzerTool which only needs the API key.

    Args:
        db_manager: Database manager for data access
        cache_service: Optional cache service for performance

    Returns:
        List of database-dependent tool instances
    """
    return create_all_tools(
        db_manager=db_manager,
        cache_service=cache_service,
        include_photo_analyzer=False
    )


def create_standalone_tools() -> List[BaseTool]:
    """
    Create tools that don't require database access.
    Currently only PhotoAnalyzerTool.

    Returns:
        List of standalone tool instances
    """
    tools: List[BaseTool] = []

    try:
        tools.append(PhotoAnalyzerTool())
        logger.debug("Created PhotoAnalyzerTool")
    except Exception as e:
        logger.warning(f"Could not create PhotoAnalyzerTool: {e}")

    return tools


# Tool metadata for documentation/introspection
TOOL_INFO = {
    'species_recommender': {
        'class': SpeciesRecommenderTool,
        'requires_db': True,
        'requires_cache': True,
        'description': 'Recommends tree species based on site conditions and preferences'
    },
    'pricing_calculator': {
        'class': PricingCalculatorTool,
        'requires_db': True,
        'requires_cache': False,
        'description': 'Calculates costs for tree purchase and installation'
    },
    'environmental_calculator': {
        'class': EnvironmentalCalculatorTool,
        'requires_db': True,
        'requires_cache': True,
        'description': 'Calculates environmental benefits (CO2, stormwater, etc.)'
    },
    'hazard_checker': {
        'class': HazardCheckerTool,
        'requires_db': True,
        'requires_cache': False,
        'description': 'Verifies safety clearances from utilities and buildings'
    },
    'maintenance_guide': {
        'class': MaintenanceGuideTool,
        'requires_db': True,
        'requires_cache': False,
        'description': 'Provides tree care instructions by species, age, and season'
    },
    'planting_instructions': {
        'class': PlantingInstructionsTool,
        'requires_db': True,
        'requires_cache': False,
        'description': 'Generates step-by-step planting guides'
    },
    'photo_analyzer': {
        'class': PhotoAnalyzerTool,
        'requires_db': False,
        'requires_cache': False,
        'description': 'Analyzes site photos using Claude Vision'
    }
}
