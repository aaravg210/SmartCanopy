#!/usr/bin/env python3
"""
Interactive chat with SmartCanopy AI Agent
Talk to the agent in real-time!
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
import logging

# Setup logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise


async def main():
    """Interactive chat with SmartCanopy AI"""

    print("\n" + "="*80)
    print("🌳 SMARTCANOPY AI - INTERACTIVE CHAT")
    print("="*80)
    print("\nInitializing agent...")

    # Check if database is available
    try:
        db_manager = DatabaseManager(settings.database_url)
        cache_service = CacheService(settings.redis_url)

        # Initialize all 7 tools
        tools = [
            SpeciesRecommenderTool(db_manager, cache_service),
            PricingCalculatorTool(db_manager),
            EnvironmentalCalculatorTool(db_manager, cache_service),
            HazardCheckerTool(db_manager),
            MaintenanceGuideTool(db_manager),
            PlantingInstructionsTool(db_manager)
            # PhotoAnalyzerTool not included (requires image upload)
        ]

        print(f"✅ Agent initialized with {len(tools)} tools!")
        print("\nAvailable tools:")
        for tool in tools:
            print(f"  • {tool.name}")

    except Exception as e:
        print(f"⚠️  Database not available ({e})")
        print("   Starting agent WITHOUT tools (conversation only)")
        tools = []

    # Create agent
    agent = SmartCanopyAgent(tools=tools)

    print("\n" + "="*80)
    print("Ready to chat! Type 'quit' or 'exit' to end the conversation.")
    print("Tip: Ask about trees, environmental benefits, or request recommendations!")
    print("="*80 + "\n")

    # Conversation history
    conversation_history = []

    # Chat loop
    while True:
        try:
            # Get user input
            user_message = input("👤 You: ").strip()

            if not user_message:
                continue

            # Check for exit
            if user_message.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print("\n🌳 Thanks for chatting! Happy tree planting! 🌱\n")
                break

            # Show thinking indicator
            print("\n🤖 SmartCanopy is thinking...\n")

            # Get agent response
            response = await agent.chat(
                message=user_message,
                conversation_history=conversation_history,
                max_tool_rounds=5
            )

            # Update conversation history
            conversation_history = response['conversation_history']

            # Display response
            print(f"🤖 SmartCanopy:\n{response['response']}\n")

            # Show tool usage if any
            if response['tool_calls']:
                print(f"[Used {len(response['tool_calls'])} tools: {', '.join(t['tool'] for t in response['tool_calls'])}]\n")

            print("-" * 80 + "\n")

        except KeyboardInterrupt:
            print("\n\n🌳 Chat interrupted. Goodbye! 🌱\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            print("Try asking something else, or type 'quit' to exit.\n")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("SMARTCANOPY AI AGENT - INTERACTIVE CHAT")
    print("="*80)
    print("\nPrerequisites:")
    print("  ✅ ANTHROPIC_API_KEY is set in .env")
    print("  ⚠️  Database is optional (agent works without it)")
    print("\nIf you want to use tools (recommendations, pricing, etc.):")
    print("  1. Open Docker Desktop")
    print("  2. Run: docker compose up -d postgres redis")
    print("  3. Wait ~30 seconds for containers to start")
    print("="*80)

    input("\nPress ENTER to start chatting...")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nGoodbye! 🌳\n")
