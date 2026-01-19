# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SmartCanopy is an AI-powered urban tree planting system that:
1. Identifies optimal planting locations using satellite imagery (NAIP from Google Earth Engine)
2. Detects existing trees using DeepForest (pre-trained object detection)
3. Analyzes vegetation health (NDVI) and terrain (slope)
4. Filters infrastructure (roads, buildings) using OpenStreetMap
5. Provides tree species recommendations via a Claude-powered AI agent

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

## Common Commands

### Run Components
```bash
# CV Pipeline
python test_gee.py                # Test GEE connection
python planting_site_detector.py  # Full analysis pipeline

# API Server
uvicorn api.main:app --reload     # Start FastAPI at :8000
python scripts/run_api.py         # Alternative

# Interactive Testing
python scripts/chat_with_agent.py # Chat with AI agent
python scripts/test_agent.py      # Test agent tools
```

### Run Tests
```bash
pytest                            # Run all tests
pytest -m unit                    # Unit tests only
pytest -m integration             # Integration tests
pytest -m "not requires_api_key"  # Skip tests needing API keys
pytest tests/tools/               # Test specific tools
pytest --cov=agent --cov=api      # With coverage
```

### Database
```bash
python scripts/seed_plants.py     # Seed plant species data
python scripts/query_database.py  # Query utilities
docker-compose --profile tools up pgadmin  # DB admin UI at :5050
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
        PostgreSQL → [agent/] → Claude API → FastAPI → Client
```

### Key Components

**CV Pipeline** (root level):
- `data_pipeline.py` - `TreeDataPipeline`: GEE integration, NDVI calculation
- `download_imagery.py` - `ImageryDownloader`: Local image downloads
- `test_deepforest.py` - `DeepForestDetector`: Tree detection with bounding boxes
- `osm_filter.py` - `OSMFilter`: Infrastructure exclusion masks
- `planting_site_detector.py` - `PlantingSiteDetector`: Orchestrates full pipeline

**AI Agent** (`agent/`):
- `agent.py` - `SmartCanopyAgent`: Claude API integration, tool orchestration
- `config.py` - Pydantic settings from environment
- `tools/` - 7 specialized tools inheriting from `BaseTool`:
  - `species_recommender.py` - Tree recommendations by climate/space/soil
  - `pricing_calculator.py` - Cost estimates with regional multipliers
  - `environmental_calculator.py` - CO2, stormwater, air quality benefits
  - `hazard_checker.py` - Safety clearances (utilities, buildings)
  - `photo_analyzer.py` - Site photo analysis via Claude Vision
  - `maintenance_guide.py` - Watering/pruning schedules
  - `planting_instructions.py` - Step-by-step guides
- `services/` - Data layer:
  - `plant_database.py` - SQLAlchemy models (PlantSpecies, PlantingSite, etc.)
  - `cache_service.py` - Redis caching with TTL
  - `hardiness_zone_api.py` - USDA zone lookups

**API** (`api/`):
- `main.py` - FastAPI app with async context managers
- `routes/` - Endpoints for agent, species, sites, CV operations

### Database Schema
Core tables in `database/schema.sql`:
- `plant_species` - Species with environmental benefits, pricing, hardiness zones
- `planting_sites` - CV analysis results with suitability scores
- `analyses` - Analysis runs with imagery paths
- `conversations` - Agent chat history

## Key Parameters

| Parameter | Default | Location |
|-----------|---------|----------|
| NDVI range | 0.15-0.65 | `planting_site_detector.py:find_planting_sites()` |
| Slope max | 15° | `planting_site_detector.py:find_planting_sites()` |
| DeepForest confidence | 0.3 | `test_deepforest.py:predict_trees()` |
| Infrastructure buffer | 3m | `osm_filter.py` |
| Analysis buffer | 100m | `buffer_m` parameter |
| Image size | 512x512 | `get_image_url()` |

## Testing

Tests in `tests/` use pytest with markers defined in `pytest.ini`:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - API integration
- `@pytest.mark.e2e` - End-to-end scenarios
- `@pytest.mark.requires_api_key` - Needs ANTHROPIC_API_KEY
- `@pytest.mark.requires_gee` - Needs GEE auth
- `@pytest.mark.requires_redis` - Needs Redis

Fixtures in `tests/conftest.py` provide:
- `db_manager` - In-memory SQLite for tests
- `cache_service` - Isolated Redis DB 15
- `sample_species`, `sample_planting_site` - Test data
- `mock_anthropic_response` - Mock Claude API

## Important Notes

- **Coordinate Systems**: WGS84 (EPSG:4326) for I/O, Web Mercator (EPSG:3857) for OSM buffering
- **GEE Rate Limits**: `cache/` directory stores API responses to avoid repeated requests
- **DeepForest**: Downloads weights on first run via `model.use_release()`
- **All GEE scripts** call `ee.Initialize(project='urban-tree-ai')` - auth required first
