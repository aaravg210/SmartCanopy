#!/usr/bin/env python3
"""
Simple chat test - mimics what chat_with_agent.py does
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from agent.agent import SmartCanopyAgent
from agent.services.plant_database import DatabaseManager
from agent.services.cache_service import CacheService
from agent.tools import (
    SpeciesRecommenderTool,
    PricingCalculatorTool,
    EnvironmentalCalculatorTool,
    HazardCheckerTool,
    MaintenanceGuideTool,
    PlantingInstructionsTool
)
from agent.config import settings

async def main():
    """Test chat like the interactive script"""

    print("\n" + "="*80)
    print("🌳 Testing SmartCanopy Agent")
    print("="*80)

    # Try to initialize with tools
    try:
        db_manager = DatabaseManager(settings.database_url)
        cache_service = CacheService(settings.redis_url)

        tools = [
            SpeciesRecommenderTool(db_manager, cache_service),
            PricingCalculatorTool(db_manager),
            EnvironmentalCalculatorTool(db_manager, cache_service),
            HazardCheckerTool(db_manager),
            MaintenanceGuideTool(db_manager),
            PlantingInstructionsTool(db_manager)
        ]

        print(f"\n✅ Agent initialized with {len(tools)} tools!")
    except Exception as e:
        print(f"\n⚠️  Database not available ({e})")
        print("   Starting agent WITHOUT tools (conversation only)")
        tools = []

    # Create agent
    agent = SmartCanopyAgent(tools=tools)

    # Test conversation
    conversation_history = []

    # Message 1
    print("\n" + "-"*80)
    print("👤 You: Tell me about environmental benefits of trees")
    print("-"*80)

    response = await agent.chat(
        message="Tell me about environmental benefits of trees",
        conversation_history=conversation_history
    )

    conversation_history = response['conversation_history']

    print(f"\n🤖 SmartCanopy:\n{response['response'][:500]}...")
    print(f"\nRounds: {response['rounds']}")
    print(f"Tools used: {len(response['tool_calls'])}")

    # Message 2 (should trigger tool)
    print("\n" + "-"*80)
    print("👤 You: Calculate benefits of 1 American Sycamore for 20 years")
    print("-"*80)

    response = await agent.chat(
        message="Calculate environmental benefits of 1 American Sycamore for 20 years",
        conversation_history=conversation_history
    )

    conversation_history = response['conversation_history']

    print(f"\n🤖 SmartCanopy:\n{response['response'][:500]}...")
    print(f"\nRounds: {response['rounds']}")
    print(f"Tools used: {len(response['tool_calls'])}")

    if response['tool_calls']:
        for tool_call in response['tool_calls']:
            print(f"\n  Tool: {tool_call['tool']}")

    print("\n" + "="*80)
    print("✅ Test complete!")
    print("="*80)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
