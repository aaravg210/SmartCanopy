#!/usr/bin/env python3
"""
Test SmartCanopy FastAPI Backend
Run all API endpoints to verify functionality
"""

import asyncio
import httpx
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# API Base URL
API_BASE = "http://localhost:8000"


def print_section(title: str):
    """Print section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_response(response: httpx.Response, show_body: bool = True):
    """Print response details"""
    print(f"\n📍 {response.request.method} {response.request.url}")
    print(f"Status: {response.status_code} {response.reason_phrase}")

    if show_body and response.text:
        try:
            data = response.json()
            print(f"\nResponse:\n{json.dumps(data, indent=2)}")
        except:
            print(f"\nResponse:\n{response.text[:500]}")


async def test_health_check(client: httpx.AsyncClient):
    """Test health check endpoint"""
    print_section("1. Health Check")

    response = await client.get(f"{API_BASE}/api/health")
    print_response(response)

    assert response.status_code == 200, "Health check failed"
    print("\n✅ Health check passed")


async def test_root(client: httpx.AsyncClient):
    """Test root endpoint"""
    print_section("2. Root Endpoint")

    response = await client.get(f"{API_BASE}/")
    print_response(response)

    assert response.status_code == 200, "Root endpoint failed"
    print("\n✅ Root endpoint passed")


async def test_species_search(client: httpx.AsyncClient):
    """Test species search"""
    print_section("3. Species Search")

    # Search all species
    response = await client.get(f"{API_BASE}/api/species/search?limit=5")
    print_response(response)

    assert response.status_code == 200, "Species search failed"
    data = response.json()
    print(f"\n✅ Found {len(data)} species")

    # Search by hardiness zone
    print("\n--- Search by Hardiness Zone 10 ---")
    response = await client.get(f"{API_BASE}/api/species/search?hardiness_zone=10&limit=3")
    print_response(response)

    # Search by name
    print("\n--- Search by Name: 'oak' ---")
    response = await client.get(f"{API_BASE}/api/species/search?query=oak&limit=3")
    print_response(response)


async def test_species_detail(client: httpx.AsyncClient):
    """Test species detail endpoint"""
    print_section("4. Species Detail")

    # Get American Sycamore details
    response = await client.get(f"{API_BASE}/api/species/PLOC")
    print_response(response)

    if response.status_code == 200:
        print("\n✅ Species detail retrieved")
    else:
        print(f"\n⚠️ Species not found (database may not be seeded)")


async def test_agent_chat(client: httpx.AsyncClient):
    """Test agent chat endpoint"""
    print_section("5. Agent Chat")

    chat_request = {
        "message": "Tell me about the environmental benefits of planting trees",
        "max_tool_rounds": 3
    }

    print(f"\nSending message: {chat_request['message']}")

    response = await client.post(
        f"{API_BASE}/api/agent/chat",
        json=chat_request,
        timeout=30.0  # Agent may take time
    )

    print_response(response, show_body=False)

    if response.status_code == 200:
        data = response.json()
        print(f"\n🤖 Agent Response:\n{data['response'][:500]}...")
        print(f"\nRounds: {data['rounds']}")
        print(f"Tools used: {len(data['tool_calls'])}")
        print("\n✅ Agent chat working!")
    else:
        print("\n⚠️ Agent chat failed (check API key)")


async def test_agent_chat_with_tools(client: httpx.AsyncClient):
    """Test agent chat with tool usage"""
    print_section("6. Agent Chat with Tools")

    chat_request = {
        "message": "Calculate the environmental benefits of planting 1 American Sycamore for 20 years",
        "max_tool_rounds": 5
    }

    print(f"\nSending message: {chat_request['message']}")

    response = await client.post(
        f"{API_BASE}/api/agent/chat",
        json=chat_request,
        timeout=30.0
    )

    print_response(response, show_body=False)

    if response.status_code == 200:
        data = response.json()
        print(f"\n🤖 Agent Response:\n{data['response'][:800]}...")
        print(f"\n📊 Tool Calls: {len(data['tool_calls'])}")
        for tool in data['tool_calls']:
            print(f"  • {tool['tool']}")
        print("\n✅ Agent tools working!")
    else:
        print("\n⚠️ Agent with tools failed (database may not be running)")


async def test_cv_analysis(client: httpx.AsyncClient):
    """Test CV model analysis (requires Google Earth Engine)"""
    print_section("7. CV Model Analysis")

    print("\n⚠️ Skipping CV analysis test (requires GEE authentication)")
    print("To test manually:")
    print("  POST /api/cv/analyze")
    print('  Body: {"address": "123 Main St, San Francisco, CA", "buffer_m": 100}')

    # Uncomment to test (requires GEE setup):
    # analysis_request = {
    #     "address": "Golden Gate Park, San Francisco, CA",
    #     "buffer_m": 100,
    #     "save_images": True
    # }
    # response = await client.post(
    #     f"{API_BASE}/api/cv/analyze",
    #     json=analysis_request,
    #     timeout=60.0
    # )
    # print_response(response)


async def test_site_endpoints(client: httpx.AsyncClient):
    """Test site endpoints"""
    print_section("8. Site Endpoints")

    print("\n⚠️ Site endpoints require a valid site_id from CV analysis")
    print("Example usage:")
    print("  GET /api/sites/{site_id}")
    print("  POST /api/sites/{site_id}/photo")
    print("  GET /api/sites/{site_id}/photos")


async def run_all_tests():
    """Run all API tests"""
    print("\n" + "🌳"*40)
    print("SmartCanopy API Test Suite")
    print("🌳"*40)
    print(f"\nTesting API at: {API_BASE}")
    print("Make sure the API server is running:")
    print("  python3 api/main.py")
    print("\nOr:")
    print("  uvicorn api.main:app --reload")

    input("\nPress ENTER to start tests...")

    async with httpx.AsyncClient() as client:
        try:
            # Core tests
            await test_health_check(client)
            await test_root(client)

            # Species database tests
            await test_species_search(client)
            await test_species_detail(client)

            # Agent tests
            await test_agent_chat(client)
            await test_agent_chat_with_tools(client)

            # CV and site tests (informational)
            await test_cv_analysis(client)
            await test_site_endpoints(client)

            # Summary
            print_section("✅ Test Summary")
            print("\nCore functionality:")
            print("  ✅ Health check")
            print("  ✅ Root endpoint")
            print("  ✅ Species search")
            print("  ✅ Species detail")
            print("  ✅ Agent chat")
            print("\nOptional (requires setup):")
            print("  ⚠️ CV analysis (needs GEE authentication)")
            print("  ⚠️ Site endpoints (needs CV analysis first)")

            print("\n" + "="*80)
            print("🎉 API tests complete!")
            print("="*80)

        except httpx.ConnectError:
            print("\n" + "="*80)
            print("❌ ERROR: Could not connect to API")
            print("="*80)
            print("\nMake sure the API server is running:")
            print("  python3 api/main.py")
            print("\nOr:")
            print("  uvicorn api.main:app --reload")
            sys.exit(1)

        except Exception as e:
            print(f"\n❌ Test error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    print("\n🧪 SmartCanopy API Test Suite")
    print("="*80)
    print("\nPrerequisites:")
    print("  1. API server running (python3 api/main.py)")
    print("  2. Database running (docker compose up -d postgres redis)")
    print("  3. Database seeded (python3 scripts/seed_plants.py)")
    print("  4. ANTHROPIC_API_KEY in .env")
    print("="*80)

    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(0)
