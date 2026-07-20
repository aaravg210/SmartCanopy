# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SmartCanopy is an AI-powered urban tree planting system that:
1. Identifies optimal planting locations using satellite imagery (NAIP from Google Earth Engine)
2. Detects existing trees using DeepForest (pre-trained object detection)
3. Analyzes vegetation health (NDVI) and terrain (slope)
4. Filters infrastructure (roads, buildings) using OpenStreetMap
5. Provides tree species recommendations via a Claude-powered AI agent
6. Serves results through a Next.js frontend with Mapbox GL

## Environment Setup

### Quick Start
```bash
source venv/bin/activate   # Python 3.13 venv
earthengine authenticate    # Required for GEE (project ID: urban-tree-ai)
docker-compose up -d postgres redis  # Start databases
cp .env.example .env        # Configure API keys
```

### Required Environment Variables
- `ANTHROPIC_API_KEY` - Required for AI agent
- `DATABASE_URL` - PostgreSQL (default: `postgresql+asyncpg://smartcanopy:password@localhost:5432/smartcanopy`)
- `REDIS_URL` - Redis cache (default: `redis://localhost:6379/0`)
- `CLAUDE_MODEL` - Claude model ID (default: `claude-opus-4-5-20251101`)

### Optional Management UIs
```bash
docker-compose --profile tools up -d  # pgAdmin at :5050, Redis Commander at :8081
```

## Common Commands

### Backend
```bash
# CV Pipeline
python test_gee.py                # Test GEE connection
python planting_site_detector.py  # Full analysis pipeline

# API Server
uvicorn api.main:app --reload     # Start FastAPI at :8000

# Interactive Testing
python scripts/chat_with_agent.py # Chat with AI agent
python scripts/test_agent.py      # Test agent tools

# Database
python scripts/seed_plants.py     # Seed plant species data
```

### Frontend (Next.js + Tailwind + Mapbox GL)
```bash
cd frontend
npm run dev                       # Start dev server
npm run build                     # Production build
npm run lint                      # ESLint
```

### Tests
```bash
pytest                            # Run all tests
pytest -m unit                    # Unit tests only
pytest -m integration             # Integration tests
pytest -m "not requires_api_key"  # Skip tests needing API keys
pytest tests/tools/               # Test specific tool directory
pytest tests/test_agent.py::TestClassName::test_name  # Single test
pytest --cov=agent --cov=api      # With coverage
```

### Linting / Formatting
```bash
black .                           # Format Python code
flake8                            # Lint Python code
mypy agent/ api/                  # Type checking
```

## Architecture

```
Address → [data_pipeline.py] → GEE (NAIP/NDVI/Slope)
                ↓
        [download_imagery.py] → Local images
                ↓
        [test_deepforest.py] → Tree detection
                ↓
        [osm_filter.py] → Infrastructure mask
                ↓
        [planting_site_detector.py] → Suitability scores
                ↓
        PostgreSQL → [agent/] → Claude API → FastAPI → Next.js frontend
```

### CV Pipeline (root level)
- `data_pipeline.py` - `TreeDataPipeline`: GEE integration, NDVI calculation
- `download_imagery.py` - `ImageryDownloader`: Local image downloads
- `test_deepforest.py` - `DeepForestDetector`: Tree detection with bounding boxes
- `osm_filter.py` - `OSMFilter`: Infrastructure exclusion masks
- `planting_site_detector.py` - `PlantingSiteDetector`: Orchestrates full pipeline

### AI Agent (`agent/`)
- `agent.py` - `SmartCanopyAgent`: Claude API integration, tool orchestration
- `config.py` - Pydantic settings from environment
- `tools/` - 7 tools inheriting from `BaseTool`: `species_recommender`, `pricing_calculator`, `environmental_calculator`, `hazard_checker`, `photo_analyzer`, `maintenance_guide`, `planting_instructions`
- `tools/factory.py` - `create_all_tools()`, `create_database_tools()`, `create_standalone_tools()` for tool instantiation
- `tools/base_tool.py` - `BaseTool` base class, `ToolRegistry` for registration
- `utils/geo_utils.py` - Shared geographic utility functions
- `services/plant_database.py` - SQLAlchemy models (`PlantSpecies`, `PlantingSite`, etc.); uses cross-database-compatible `GUID`/`JSONType` wrappers so tests run on SQLite while production uses PostgreSQL JSONB/UUID
- `services/cache_service.py` - Redis caching with TTL
- `services/hardiness_zone_api.py` - USDA hardiness zone lookups
- `services/itree_integration.py` - iTree Tools API integration for species data
- `services/site_data_loader.py` - Loads site data for agent context

### API (`api/`)
- `main.py` - FastAPI app with async context managers
- `routes/` - Endpoints for agent, species, sites, CV operations
- `schemas/` - Pydantic request/response schemas

### Frontend (`frontend/`)
- Next.js 14 app with TypeScript, Tailwind CSS, Mapbox GL
- State management via Zustand (`src/stores/`)
- Components in `src/components/`, hooks in `src/hooks/`

### Database Schema
Core tables in `database/schema.sql`: `plant_species`, `planting_sites`, `analyses`, `conversations`

## Testing

Tests in `tests/` use pytest with markers defined in `pytest.ini`:
- `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e`
- `@pytest.mark.requires_api_key`, `@pytest.mark.requires_gee`, `@pytest.mark.requires_redis`

Fixtures in `tests/conftest.py` provide:
- `db_manager` - In-memory SQLite for tests
- `cache_service` - Isolated Redis DB 15
- `sample_species`, `sample_planting_site` - Test data
- `mock_anthropic_response` - Mock Claude API

Async mode: `asyncio_mode = auto` (no need for `@pytest.mark.asyncio`)

## Key Parameters

| Parameter | Default | Location |
|-----------|---------|----------|
| NDVI range | 0.15-0.65 | `planting_site_detector.py:find_planting_sites()` |
| Slope max | 15° | `planting_site_detector.py:find_planting_sites()` |
| DeepForest confidence | 0.3 | `test_deepforest.py:predict_trees()` |
| Infrastructure buffer | 3m | `osm_filter.py` |
| Analysis buffer | 100m | `buffer_m` parameter |
| Image size | 512x512 | `get_image_url()` |

## Important Notes

- **Coordinate Systems**: WGS84 (EPSG:4326) for I/O, Web Mercator (EPSG:3857) for OSM buffering
- **GEE Rate Limits**: `cache/` directory stores API responses to avoid repeated requests
- **DeepForest**: Downloads weights on first run via `model.use_release()`
- **All GEE scripts** call `ee.Initialize(project='urban-tree-ai')` - auth required first
- **Tool pattern**: All agent tools inherit from `BaseTool` and register via `ToolRegistry`; use factory functions in `tools/factory.py` to instantiate
