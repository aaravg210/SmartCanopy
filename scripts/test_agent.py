#!/usr/bin/env python3
"""
Test script for SmartCanopy AI Agent
Demonstrates the agent with currently implemented tools
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.agent import SmartCanopyAgent
from agent.config import settings
from agent.services.plant_database import DatabaseManager
from agent.services.cache_service import CacheService
from agent.tools.species_recommender import SpeciesRecommenderTool
from agent.tools.pricing_calculator import PricingCalculatorTool
from agent.tools.environmental_calculator import EnvironmentalCalculatorTool
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_agent_basic():
    """Test basic agent interaction without tools"""
    print("\n" + "="*80)
    print("TEST 1: Basic Agent Interaction (No Tools)")
    print("="*80 + "\n")

    try:
        agent = SmartCanopyAgent()

        response = await agent.chat(
            message="Hello! What can you help me with?",
            conversation_history=[]
        )

        print("User: Hello! What can you help me with?")
        print(f"\nAgent: {response['response']}")
        print(f"\nMetadata: {response['rounds']} rounds, {len(response['tool_calls'])} tools called")

    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure ANTHROPIC_API_KEY is set in .env file!")


async def test_agent_with_tools():
    """Test agent with all available tools"""
    print("\n" + "="*80)
    print("TEST 2: Agent with Tools (Species Recommendation)")
    print("="*80 + "\n")

    try:
        # Initialize services
        db_manager = DatabaseManager(settings.database_url)
        cache_service = CacheService(settings.redis_url)

        # Initialize tools
        tools = [
            SpeciesRecommenderTool(db_manager, cache_service),
            PricingCalculatorTool(db_manager),
            EnvironmentalCalculatorTool(db_manager, cache_service)
        ]

        # Create agent with tools
        agent = SmartCanopyAgent(tools=tools)

        print(f"Agent initialized with {len(agent.tools)} tools:")
        for tool_name in agent.tools.keys():
            print(f"  - {tool_name}")

        # Note: This requires a planting site to exist in database
        # For now, we'll just show the agent recognizes the tools

        response = await agent.chat(
            message="What tools do you have available?",
            conversation_history=[]
        )

        print("\nUser: What tools do you have available?")
        print(f"\nAgent: {response['response']}")

    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Detailed error:")


async def test_tool_directly():
    """Test a tool directly (without agent)"""
    print("\n" + "="*80)
    print("TEST 3: Direct Tool Testing (Environmental Calculator)")
    print("="*80 + "\n")

    try:
        # Initialize services
        db_manager = DatabaseManager(settings.database_url)
        cache_service = CacheService(settings.redis_url)

        # Create environmental calculator
        env_calc = EnvironmentalCalculatorTool(db_manager, cache_service)

        print("Testing Environmental Calculator with American Sycamore (PLOC)...")
        print("Calculating 20-year environmental benefits for 1 tree\n")

        result = await env_calc.run(
            species_id='PLOC',
            quantity=1,
            years_projection=20,
            tree_age_years=0
        )

        print(f"Species: {result['species']['common_name']}")
        print(f"Projection: {result['projection_years']} years")
        print(f"\nAnnual Benefits (at maturity):")
        print(f"  CO2 Sequestration: {result['annual_benefits_per_tree']['co2_kg']} kg/year")
        print(f"  Stormwater: {result['annual_benefits_per_tree']['stormwater_gallons']} gallons/year")
        print(f"  Air Pollution Removal: {result['annual_benefits_per_tree']['air_pollution_kg']} kg/year")

        print(f"\n20-Year Cumulative Benefits:")
        print(f"  Total CO2 Captured: {result['cumulative_benefits']['co2_kg']:,.1f} kg")
        print(f"  Total Stormwater: {result['cumulative_benefits']['stormwater_gallons']:,.1f} gallons")
        print(f"  Total Air Pollution: {result['cumulative_benefits']['air_pollution_kg']:,.1f} kg")

        print(f"\nDollar Value (20 years):")
        print(f"  CO2 Value: ${result['dollar_value']['co2_value_usd']:,.2f}")
        print(f"  Stormwater Value: ${result['dollar_value']['stormwater_value_usd']:,.2f}")
        print(f"  Air Quality Value: ${result['dollar_value']['air_quality_value_usd']:,.2f}")
        print(f"  Total Value: ${result['dollar_value']['total_usd']:,.2f}")

        print(f"\nEquivalent Metrics:")
        for key, value in result['equivalent_metrics'].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")

    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Detailed error:")


async def test_pricing_tool():
    """Test pricing calculator directly"""
    print("\n" + "="*80)
    print("TEST 4: Direct Tool Testing (Pricing Calculator)")
    print("="*80 + "\n")

    try:
        db_manager = DatabaseManager(settings.database_url)
        pricing_calc = PricingCalculatorTool(db_manager)

        print("Testing Pricing Calculator for 3 Valley Oaks (QULO), 6ft size")
        print("Including professional planting, ZIP 94102 (San Francisco)\n")

        result = await pricing_calc.run(
            species_id='QULO',
            quantity=3,
            tree_size='6ft',
            include_planting=True,
            zip_code='94102'
        )

        print(f"Species: {result['species']['common_name']}")
        print(f"Quantity: {result['quantity']} trees")
        print(f"Size: {result['tree_size']}")
        print(f"\nPrice Breakdown (per tree):")
        print(f"  Base Tree Price: ${result['breakdown']['base_price']}")
        print(f"  Regional Multiplier: {result['breakdown']['regional_multiplier']}x (CA)")
        print(f"  Adjusted Tree Price: ${result['breakdown']['tree_price_per_unit']}")
        print(f"  Labor ({result['breakdown']['labor_hours']}hrs @ $50/hr): ${result['breakdown']['labor_per_tree']}")
        print(f"  Materials: ${result['breakdown']['materials_per_tree']}")
        print(f"  Cost Per Tree: ${result['breakdown']['cost_per_tree']}")

        print(f"\nTotal Pricing:")
        print(f"  Subtotal: ${result['breakdown']['subtotal']}")
        if result['breakdown']['discount_rate'] > 0:
            print(f"  Bulk Discount ({result['breakdown']['discount_rate']*100}%): -${result['breakdown']['discount_amount']}")
        print(f"  TOTAL COST: ${result['total_cost']}")
        print(f"\nEstimated Delivery: {result['estimated_delivery_days']} days")

    except Exception as e:
        print(f"Error: {e}")
        logger.exception("Detailed error:")


async def test_all():
    """Run all tests"""
    print("\n" + "="*80)
    print("SMARTCANOPY AI AGENT - TEST SUITE")
    print("="*80)

    # Test 1: Basic agent
    await test_agent_basic()

    # Test 2: Agent with tools
    await test_agent_with_tools()

    # Test 3: Environmental calculator
    await test_tool_directly()

    # Test 4: Pricing calculator
    await test_pricing_tool()

    print("\n" + "="*80)
    print("ALL TESTS COMPLETE!")
    print("="*80 + "\n")


if __name__ == "__main__":
    print("\nSmartCanopy AI Agent Test Script")
    print("=" * 80)
    print("This script tests the AI agent and its tools.")
    print("\nPrerequisites:")
    print("  1. Database running (docker compose up -d postgres redis)")
    print("  2. Database seeded (python scripts/seed_plants.py)")
    print("  3. ANTHROPIC_API_KEY set in .env file")
    print("=" * 80)

    # Run tests
    try:
        asyncio.run(test_all())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        logger.exception("Detailed error:")
        print("\n\nTo debug, check:")
        print("  1. Is Docker running? (docker compose ps)")
        print("  2. Is database seeded? (python scripts/query_database.py)")
        print("  3. Is ANTHROPIC_API_KEY valid in .env?")
