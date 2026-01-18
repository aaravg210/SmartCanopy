#!/usr/bin/env python3
"""
Simple conversation demo with SmartCanopy AI Agent
No database required - just shows the agent's personality
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.agent import SmartCanopyAgent


async def demo_conversation():
    """Demo conversation without tools"""
    print("\n" + "="*80)
    print("SMARTCANOPY AI - CONVERSATION DEMO")
    print("="*80 + "\n")

    # Create agent (no tools)
    agent = SmartCanopyAgent()

    # Conversation 1
    print("👤 User: What can you help me with?\n")
    response = await agent.chat(
        message="What can you help me with?",
        conversation_history=[]
    )
    print(f"🤖 SmartCanopy: {response['response']}\n")
    print("-" * 80 + "\n")

    # Conversation 2 - Continue from history
    print("👤 User: I live in San Francisco and want to plant a tree for shade in my backyard.\n")
    response = await agent.chat(
        message="I live in San Francisco and want to plant a tree for shade in my backyard.",
        conversation_history=response['conversation_history']
    )
    print(f"🤖 SmartCanopy: {response['response']}\n")
    print("-" * 80 + "\n")

    # Conversation 3
    print("👤 User: How do trees help the environment?\n")
    response = await agent.chat(
        message="How do trees help the environment?",
        conversation_history=response['conversation_history']
    )
    print(f"🤖 SmartCanopy: {response['response']}\n")

    print("="*80)
    print(f"Conversation complete! Used {response['rounds']} total rounds.")
    print("="*80 + "\n")


if __name__ == "__main__":
    print("\n🌳 SmartCanopy AI Conversation Demo")
    print("Testing the agent's personality and knowledge\n")

    try:
        asyncio.run(demo_conversation())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
    except Exception as e:
        print(f"\n\nError: {e}")
        print("\nMake sure ANTHROPIC_API_KEY is set in .env file!")
