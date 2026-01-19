"""
SmartCanopy Agent Tools
All 7 specialized tools for tree planting recommendations
"""

from agent.tools.base_tool import BaseTool, ToolExecutionError, ToolRegistry, get_tool_registry
from agent.tools.species_recommender import SpeciesRecommenderTool
from agent.tools.pricing_calculator import PricingCalculatorTool
from agent.tools.environmental_calculator import EnvironmentalCalculatorTool
from agent.tools.hazard_checker import HazardCheckerTool
from agent.tools.photo_analyzer import PhotoAnalyzerTool
from agent.tools.maintenance_guide import MaintenanceGuideTool
from agent.tools.planting_instructions import PlantingInstructionsTool
from agent.tools.factory import (
    create_all_tools,
    create_database_tools,
    create_standalone_tools,
    TOOL_INFO
)

__all__ = [
    # Base classes
    'BaseTool',
    'ToolExecutionError',
    'ToolRegistry',
    'get_tool_registry',

    # Tool classes
    'SpeciesRecommenderTool',
    'PricingCalculatorTool',
    'EnvironmentalCalculatorTool',
    'HazardCheckerTool',
    'PhotoAnalyzerTool',
    'MaintenanceGuideTool',
    'PlantingInstructionsTool',

    # Factory functions
    'create_all_tools',
    'create_database_tools',
    'create_standalone_tools',
    'TOOL_INFO'
]
