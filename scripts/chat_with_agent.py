#!/usr/bin/env python3
"""
Interactive chat with SmartCanopy AI Agent
Talk to the agent in real-time!
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent import SmartCanopyAgent
from agent.services.plant_database import DatabaseManager
from agent.services.cache_service import CacheService
from agent.tools import create_all_tools, create_standalone_tools
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

    agent = None
    tools = []

    # Try to connect to database and create full agent
    try:
        db_manager = DatabaseManager(settings.database_url)
        cache_service = CacheService(settings.redis_url)

        # Create all 7 tools using the factory
        tools = create_all_tools(
            db_manager=db_manager,
            cache_service=cache_service,
            include_photo_analyzer=True
        )

        # Create agent with tools
        agent = SmartCanopyAgent(tools=tools)

        print(f"✅ Agent initialized with {len(tools)} tools!")
        print("\nAvailable tools:")
        for tool in tools:
            print(f"  • {tool.name}: {tool.description[:60]}...")

    except Exception as e:
        print(f"⚠️  Database not available ({e})")

        # Try to create agent with standalone tools only (PhotoAnalyzer)
        try:
            standalone_tools = create_standalone_tools()
            if standalone_tools:
                agent = SmartCanopyAgent(tools=standalone_tools)
                tools = standalone_tools
                print(f"✅ Agent initialized with {len(tools)} standalone tools!")
                print("\nAvailable tools:")
                for tool in tools:
                    print(f"  • {tool.name}")
            else:
                agent = SmartCanopyAgent(tools=[])
                print("   Starting agent WITHOUT tools (conversation only)")

        except Exception as e2:
            print(f"   Could not create standalone tools: {e2}")
            agent = SmartCanopyAgent(tools=[])
            print("   Starting agent WITHOUT tools (conversation only)")

    print("\n" + "="*80)
    print("Ready to chat! Type 'quit' or 'exit' to end the conversation.")
    print("\nTips:")
    print("  • Ask about trees, environmental benefits, or request recommendations!")
    print("  • Upload site photos for analysis (if photo_analyzer tool is available)")
    print("  • Get pricing estimates, planting instructions, and maintenance guides")
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

            # Check for special commands
            if user_message.lower() == '/tools':
                print("\n📦 Available tools:")
                if tools:
                    for tool in tools:
                        print(f"  • {tool.name}: {tool.description[:70]}...")
                else:
                    print("  No tools available (database not connected)")
                print()
                continue

            if user_message.lower() == '/stats':
                stats = agent.get_stats()
                print("\n📊 Agent Statistics:")
                print(f"  Model: {stats['model']}")
                print(f"  Tools registered: {stats['tools_registered']}")
                if stats['tool_stats']:
                    print("  Tool usage:")
                    for name, tool_stat in stats['tool_stats'].items():
                        if tool_stat['execution_count'] > 0:
                            print(f"    • {name}: {tool_stat['execution_count']} calls, "
                                  f"avg {tool_stat['avg_time_ms']:.0f}ms")
                print()
                continue

            if user_message.lower() == '/help':
                print("\n📖 Commands:")
                print("  /tools - List available tools")
                print("  /stats - Show agent statistics")
                print("  /help  - Show this help")
                print("  quit   - Exit the chat")
                print()
                continue

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
                tool_names = [t['tool'] for t in response['tool_calls']]
                print(f"[Used {len(response['tool_calls'])} tools: {', '.join(tool_names)}]\n")

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
    print("\nFor full functionality (all 7 tools):")
    print("  1. Open Docker Desktop")
    print("  2. Run: docker compose up -d postgres redis")
    print("  3. Run: python scripts/seed_plants.py")
    print("="*80)

    input("\nPress ENTER to start chatting...")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nGoodbye! 🌳\n")
