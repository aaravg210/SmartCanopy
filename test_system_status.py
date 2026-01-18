#!/usr/bin/env python3
"""
Quick System Status Check
Tests what's working in the SmartCanopy AI system
"""

import sys
from pathlib import Path
import asyncio

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def test_imports():
    """Test if all required modules can be imported"""
    print(f"\n{BOLD}Testing Module Imports...{RESET}")

    tests = [
        ("Core Python", ["pathlib", "asyncio", "typing"]),
        ("Data Science", ["numpy", "pandas", "geopandas"]),
        ("ML/CV", ["torch", "torchvision", "deepforest"]),
        ("GEE", ["ee"]),
        ("API", ["fastapi", "uvicorn", "pydantic"]),
        ("Agent", ["anthropic"]),
        ("Database", ["sqlalchemy", "asyncpg", "psycopg2"]),
        ("Testing", ["pytest", "pytest_asyncio"])
    ]

    for category, modules in tests:
        failed = []
        for module in modules:
            try:
                __import__(module.replace("-", "_"))
            except ImportError:
                failed.append(module)

        if not failed:
            print(f"  {GREEN}✓{RESET} {category}: All modules available")
        else:
            print(f"  {YELLOW}⚠{RESET} {category}: Missing {', '.join(failed)}")


def test_project_structure():
    """Test if project structure is correct"""
    print(f"\n{BOLD}Testing Project Structure...{RESET}")

    required_dirs = [
        "agent",
        "agent/tools",
        "agent/services",
        "agent/prompts",
        "api",
        "api/routes",
        "database",
        "tests",
        "scripts"
    ]

    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            # Count Python files in directory
            py_files = list(path.glob("*.py"))
            print(f"  {GREEN}✓{RESET} {dir_path}/ ({len(py_files)} Python files)")
        else:
            print(f"  {RED}✗{RESET} {dir_path}/ (missing)")


def test_configuration():
    """Test if configuration files exist and are valid"""
    print(f"\n{BOLD}Testing Configuration...{RESET}")

    # Check .env file
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path) as f:
            env_content = f.read()

        # Check for required keys (not values, just keys)
        required_keys = ["ANTHROPIC_API_KEY", "DATABASE_URL"]
        for key in required_keys:
            if key in env_content and not f"{key}=your-" in env_content and not f"{key}=sk-ant-your-" in env_content:
                print(f"  {GREEN}✓{RESET} {key} is configured")
            else:
                print(f"  {YELLOW}⚠{RESET} {key} needs to be set in .env")
    else:
        print(f"  {RED}✗{RESET} .env file missing (copy from .env.example)")

    # Check system prompt
    prompt_path = Path("agent/prompts/system_prompt.txt")
    if prompt_path.exists():
        size = prompt_path.stat().st_size
        print(f"  {GREEN}✓{RESET} System prompt exists ({size} bytes)")
    else:
        print(f"  {RED}✗{RESET} System prompt missing")


async def test_agent_creation():
    """Test if agent can be created"""
    print(f"\n{BOLD}Testing Agent Initialization...{RESET}")

    try:
        from agent.agent import SmartCanopyAgent

        # Try creating agent without tools (minimal setup)
        try:
            agent = SmartCanopyAgent(tools=[])
            print(f"  {GREEN}✓{RESET} Agent created successfully")
            print(f"  {BLUE}ℹ{RESET} Model: {agent.model}")
            print(f"  {BLUE}ℹ{RESET} Tools registered: {len(agent.tools)}")
            return True
        except ValueError as e:
            if "API key" in str(e):
                print(f"  {YELLOW}⚠{RESET} Agent requires ANTHROPIC_API_KEY in .env")
                return False
            raise
        except Exception as e:
            print(f"  {RED}✗{RESET} Agent creation failed: {e}")
            return False

    except ImportError as e:
        print(f"  {RED}✗{RESET} Cannot import agent: {e}")
        return False


async def test_tools_available():
    """Test if all tools can be imported"""
    print(f"\n{BOLD}Testing Tool Availability...{RESET}")

    tools = [
        ("species_recommender", "SpeciesRecommenderTool"),
        ("environmental_calculator", "EnvironmentalCalculatorTool"),
        ("pricing_calculator", "PricingCalculatorTool"),
        ("hazard_checker", "HazardCheckerTool"),
        ("photo_analyzer", "PhotoAnalyzerTool"),
        ("maintenance_guide", "MaintenanceGuideTool"),
        ("planting_instructions", "PlantingInstructionsTool")
    ]

    available_count = 0
    for module_name, class_name in tools:
        try:
            module = __import__(f"agent.tools.{module_name}", fromlist=[class_name])
            tool_class = getattr(module, class_name)
            print(f"  {GREEN}✓{RESET} {class_name}")
            available_count += 1
        except Exception as e:
            print(f"  {RED}✗{RESET} {class_name}: {e}")

    print(f"\n  {BLUE}ℹ{RESET} {available_count}/7 tools available")


def test_cv_model():
    """Test if CV model components are available"""
    print(f"\n{BOLD}Testing CV Model Components...{RESET}")

    cv_files = [
        ("data_pipeline.py", "TreeDataPipeline"),
        ("osm_filter.py", "OSMFilter"),
        ("test_deepforest.py", "DeepForestDetector"),
        ("planting_site_detector.py", "PlantingSiteDetector")
    ]

    for filename, class_name in cv_files:
        path = Path(filename)
        if path.exists():
            print(f"  {GREEN}✓{RESET} {filename}")
        else:
            print(f"  {RED}✗{RESET} {filename} (missing)")


async def test_database_schema():
    """Test if database schema is defined"""
    print(f"\n{BOLD}Testing Database Schema...{RESET}")

    try:
        from agent.services.plant_database import PlantSpecies, PlantingSite
        print(f"  {GREEN}✓{RESET} PlantSpecies model defined")
        print(f"  {GREEN}✓{RESET} PlantingSite model defined")

        # Try to show fields
        print(f"  {BLUE}ℹ{RESET} PlantSpecies fields: {len(PlantSpecies.__table__.columns)} columns")

    except ImportError as e:
        print(f"  {RED}✗{RESET} Database models not available: {e}")


def test_api_routes():
    """Test if API routes are defined"""
    print(f"\n{BOLD}Testing API Routes...{RESET}")

    try:
        from api.main import app

        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        print(f"  {GREEN}✓{RESET} API application created")
        print(f"  {BLUE}ℹ{RESET} Routes defined: {len(routes)}")

        # Show important routes
        important_routes = [r for r in routes if r.startswith('/api/')]
        for route in sorted(important_routes)[:10]:
            print(f"    • {route}")

        if len(important_routes) > 10:
            print(f"    ... and {len(important_routes) - 10} more")

    except Exception as e:
        print(f"  {RED}✗{RESET} API routes error: {e}")


async def main():
    """Run all tests"""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}  SmartCanopy AI - System Status Check{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}")

    test_imports()
    test_project_structure()
    test_configuration()
    await test_agent_creation()
    await test_tools_available()
    test_cv_model()
    await test_database_schema()
    test_api_routes()

    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"\n{BOLD}Summary:{RESET}")
    print(f"  {GREEN}✓{RESET} = Working")
    print(f"  {YELLOW}⚠{RESET} = Needs configuration")
    print(f"  {RED}✗{RESET} = Missing or broken")
    print(f"\n{BOLD}Next Steps:{RESET}")
    print(f"  1. Review output above")
    print(f"  2. Fix any {RED}✗{RESET} (missing) items")
    print(f"  3. Configure any {YELLOW}⚠{RESET} (warning) items")
    print(f"  4. See {BLUE}QUICK_TEST_GUIDE.md{RESET} for detailed testing")
    print()


if __name__ == "__main__":
    asyncio.run(main())
