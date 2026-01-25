# SmartCanopy - AI-Powered Urban Tree Planting System

An intelligent system that identifies optimal locations for planting trees in urban environments and recommends suitable plant species based on environmental and geographic factors.

## Overview

SmartCanopy combines:
- **Computer Vision**: DeepForest tree detection + satellite imagery analysis (NAIP, NDVI, slope)
- **Geospatial Analysis**: OpenStreetMap integration for infrastructure filtering
- **AI Agent**: Claude-powered conversational assistant for tree recommendations

## Features

### CV Model
- Fetch satellite imagery from Google Earth Engine
- Detect existing trees using DeepForest
- Calculate NDVI (vegetation health) and slope (terrain)
- Filter out unsuitable areas (roads, buildings, parking)
- Generate planting site recommendations with suitability scores

### AI Agent
1. **Tree Species Recommendations** - Based on climate, space, soil, and user preferences
2. **Pricing Estimates** - Cost calculator for trees and planting
3. **Environmental Benefits** - CO2 sequestration, stormwater, air quality calculations
4. **Hazard Checking** - Safety clearances for utilities, buildings, roads
5. **Photo Analysis** - Analyze user-uploaded site photos with Claude Vision
6. **Maintenance Guidance** - Watering schedules, pruning instructions
7. **Planting Instructions** - Step-by-step guides customized to species and site

## Architecture

```
CV Model → PostgreSQL Database → AI Agent → FastAPI Backend → Web UI
                                     ↓
                            Claude API + Tool System
```

## Getting Started

### Prerequisites

- Python 3.13
- PostgreSQL 16
- Redis 7
- Google Earth Engine account (authenticated)
- Anthropic API key (for Claude)

### 1. Environment Setup

```bash
# Clone repository
cd urban-tree-ai

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Google Earth Engine Authentication

**CRITICAL**: Must complete before running CV model

```bash
earthengine authenticate
```

This will open a browser for authentication. The project uses GEE project ID: `urban-tree-ai`

### 3. Database Setup

#### Option A: Using Docker (Recommended)

```bash
# Copy environment template
cp .env.example .env

# Edit .env and set your passwords and API keys
nano .env

# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Verify services are running
docker-compose ps
```

#### Option B: Manual Installation

Install PostgreSQL 16 and Redis 7, then:

```bash
# Create database
createdb smartcanopy

# Run schema
psql smartcanopy < database/schema.sql
```

### 4. Seed Plant Database

```bash
# Activate virtual environment
source venv/bin/activate

# Run seed script
python scripts/seed_plants.py
```

This will populate the database with 5 sample tree species. To add more species, see `scripts/seed_plants.py`.

### 5. Configure API Keys

Edit `.env` file:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional (for hardiness zone lookups)
USDA_HARDINESS_API_KEY=your-key-here

# Database (adjust if needed)
DATABASE_URL=postgresql+asyncpg://smartcanopy:your-password@localhost:5432/smartcanopy
DB_PASSWORD=your-password-here

# Redis
REDIS_URL=redis://localhost:6379/0
```

## Running the System

### Test CV Model

```bash
# Test Google Earth Engine connection
python test_gee.py

# Download imagery for an address
python download_imagery.py

# Run full planting site detection
python planting_site_detector.py
```

Edit the `test_address` variable in each script to analyze different locations.

### Start API Server (Coming Soon)

```bash
# Start FastAPI backend
uvicorn api.main:app --reload

# API will be available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

## Project Structure

```
urban-tree-ai/
├── agent/                      # AI Agent system
│   ├── agent.py               # Core agent with Claude integration
│   ├── config.py              # Configuration management
│   ├── tools/                 # 7 specialized tools
│   │   ├── base_tool.py       # Base tool framework
│   │   ├── species_recommender.py
│   │   ├── pricing_calculator.py
│   │   └── ...
│   ├── services/              # Data services
│   │   ├── plant_database.py  # SQLAlchemy models
│   │   ├── cache_service.py   # Redis caching
│   │   └── ...
│   └── prompts/               # Agent prompts
│
├── api/                       # FastAPI backend
│   ├── main.py               # API application
│   ├── routes/               # API endpoints
│   └── schemas/              # Pydantic schemas
│
├── database/                  # Database files
│   └── schema.sql            # PostgreSQL schema
│
├── scripts/                   # Utility scripts
│   └── seed_plants.py        # Database seeding
│
├── data_pipeline.py          # GEE imagery fetching
├── download_imagery.py       # Image downloader
├── osm_filter.py            # OpenStreetMap integration
├── test_deepforest.py       # Tree detection
├── planting_site_detector.py # Main CV pipeline
│
├── docker-compose.yml        # Docker services
├── requirements.txt          # Python dependencies
└── .env.example             # Environment template
```

## Data Sources

- **USDA PLANTS Database**: Plant species information
- **i-Tree Species Database**: Environmental benefits (CO2, stormwater, air quality)
- **USDA Hardiness Zone API**: Climate zone lookups
- **Google Earth Engine**: Satellite imagery (NAIP, DEM)
- **OpenStreetMap**: Infrastructure data (roads, buildings)

## Development

### Database Management

```bash
# Access PostgreSQL with pgAdmin (optional)
docker-compose --profile tools up pgadmin

# Visit http://localhost:5050
# Login: admin@smartcanopy.local / your-password

# Access Redis with Redis Commander (optional)
docker-compose --profile tools up redis-commander

# Visit http://localhost:8081
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# With coverage
pytest --cov=agent --cov=api
```

## Key Parameters

### Buffer Radius (`buffer_m`)
- Controls geographic area analyzed around an address
- Default: 100m for analysis, 500m for imagery fetching
- Larger = more area but slower processing

### NDVI Thresholds
- Min: 0.15 (excludes pavement)
- Max: 0.65 (excludes dense forest)
- Adjust in `planting_site_detector.py:find_planting_sites()`

### Slope Threshold
- Max: 15° (steeper slopes excluded)

### DeepForest Confidence
- Default: 0.3
- Lower = more detections (including false positives)
- Higher = fewer, more confident detections

## Troubleshooting

### Google Earth Engine Errors

```bash
# Re-authenticate
earthengine authenticate

# Verify project
earthengine ls
```

### Database Connection Errors

```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres

# Restart services
docker-compose restart postgres
```

### Redis Connection Errors

```bash
# Check Redis
docker-compose ps redis

# Test connection
redis-cli ping
```

## Contributing

This is an academic/research project. For questions or contributions, please open an issue.

## License

[Add your license here]

## Acknowledgments

- **DeepForest**: Tree detection model
- **Google Earth Engine**: Satellite imagery
- **Anthropic Claude**: AI agent capabilities
- **i-Tree**: Environmental benefits data
- **USDA**: Plant species and hardiness zone data
