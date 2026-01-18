#!/usr/bin/env python3
"""
Quick test of direct agent
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from agent.agent import SmartCanopyAgent

async def main():
    print("Testing SmartCanopy Agent...\n")

    # Create agent without tools
    agent = SmartCanopyAgent()

    # Test basic chat
    print("Sending message: 'Hello'\n")
    response = await agent.chat(
        message="Hello",
        conversation_history=[]
    )

    print(f"Response: {response['response'][:200]}...\n")
    print(f"Rounds: {response['rounds']}")
    print(f"Tools used: {len(response['tool_calls'])}")

    print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(main())
