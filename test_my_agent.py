#!/usr/bin/env python3
"""
Quick Agent Integration Test
Tests the SmartCanopy Agent through FastAPI backend
"""

import httpx
import asyncio
import json

async def test_agent():
    async with httpx.AsyncClient() as client:
        # Test 1: Basic conversation
        print("\n" + "="*80)
        print("TEST 1: Basic Conversation")
        print("="*80)

        response = await client.post(
            "http://localhost:8000/api/agent/chat",
            json={"message": "What can you help me with?"},
            timeout=30.0
        )

        data = response.json()
        print(f"\n🤖 Agent: {data['response'][:300]}...")
        print(f"\nRounds: {data['rounds']}")
        print(f"Tools used: {len(data['tool_calls'])}")

        # Save conversation ID for continuity
        conversation_id = data['conversation_id']
        conversation_history = data['conversation_history']


        # Test 2: Environmental benefits (triggers tool)
        print("\n" + "="*80)
        print("TEST 2: Environmental Calculator Tool")
        print("="*80)

        response = await client.post(
            "http://localhost:8000/api/agent/chat",
            json={
                "message": "Calculate environmental benefits of 1 American Sycamore for 20 years",
                "conversation_id": conversation_id,
                "conversation_history": conversation_history
            },
            timeout=30.0
        )

        data = response.json()
        print(f"\n🤖 Agent: {data['response'][:500]}...")
        print(f"\nRounds: {data['rounds']}")
        print(f"Tools used: {len(data['tool_calls'])}")

        if data['tool_calls']:
            for tool_call in data['tool_calls']:
                print(f"\n📊 Tool: {tool_call['tool']}")
                print(f"Input: {json.dumps(tool_call['input'], indent=2)}")
                if 'cumulative_benefits' in tool_call['result']:
                    benefits = tool_call['result']['cumulative_benefits']
                    print(f"\nResults:")
                    print(f"  CO2: {benefits['co2_kg']:,.1f} kg")
                    print(f"  Stormwater: {benefits['stormwater_gallons']:,.1f} gallons")

                if 'equivalent_metrics' in tool_call['result']:
                    print(f"\nEquivalents:")
                    for metric, value in tool_call['result']['equivalent_metrics'].items():
                        print(f"  • {value}")


        # Test 3: Pricing (triggers another tool)
        print("\n" + "="*80)
        print("TEST 3: Pricing Calculator Tool")
        print("="*80)

        conversation_history = data['conversation_history']

        response = await client.post(
            "http://localhost:8000/api/agent/chat",
            json={
                "message": "How much would this cost with professional planting in ZIP 94102?",
                "conversation_id": conversation_id,
                "conversation_history": conversation_history
            },
            timeout=30.0
        )

        data = response.json()
        print(f"\n🤖 Agent: {data['response'][:500]}...")
        print(f"\nRounds: {data['rounds']}")
        print(f"Tools used: {len(data['tool_calls'])}")

        if data['tool_calls']:
            for tool_call in data['tool_calls']:
                print(f"\n💰 Tool: {tool_call['tool']}")
                if 'total_cost' in tool_call['result']:
                    print(f"Total Cost: ${tool_call['result']['total_cost']}")
                    print(f"Regional Multiplier: {tool_call['result']['breakdown'].get('regional_multiplier', 1.0)}x")


        print("\n" + "="*80)
        print("✅ All Tests Complete!")
        print("="*80)

if __name__ == "__main__":
    print("\n🧪 SmartCanopy Agent Integration Test")
    print("Testing agent through FastAPI backend")
    print("\nMake sure the API server is running:")
    print("  python3 scripts/run_api.py")
    print()

    input("Press ENTER to start tests...")

    try:
        asyncio.run(test_agent())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. API server is running (python3 scripts/run_api.py)")
        print("  2. Database is running (docker compose up -d)")
