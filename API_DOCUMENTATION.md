# SmartCanopy API Documentation

**Version:** 1.0.0
**Base URL:** `http://localhost:8000`

---

## Quick Start

### Start the API Server

```bash
# Option 1: Using the run script
python3 scripts/run_api.py

# Option 2: Using uvicorn directly
uvicorn api.main:app --reload

# Option 3: Using the main file
python3 api/main.py
```

### Prerequisites

1. **Database Running** (for full functionality):
   ```bash
   docker compose up -d postgres redis
   ```

2. **Environment Variables** in `.env`:
   ```bash
   ANTHROPIC_API_KEY=your-key-here
   DATABASE_URL=postgresql+asyncpg://...
   REDIS_URL=redis://localhost:6379/0
   ```

3. **Database Seeded**:
   ```bash
   python3 scripts/seed_plants.py
   ```

---

## Interactive API Documentation

Once the server is running:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

---

## Endpoints

### Health & Info

#### `GET /api/health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

#### `GET /`
Root endpoint with API information

---

## Agent Endpoints

### `POST /api/agent/chat`
Chat with SmartCanopy AI Agent

**Request Body:**
```json
{
  "message": "Tell me about planting trees",
  "conversation_id": "optional-uuid",
  "conversation_history": [],
  "site_context": {},
  "max_tool_rounds": 5
}
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "response": "Agent's response text...",
  "conversation_history": [...],
  "tool_calls": [
    {
      "tool": "environmental_calculator",
      "input": {...},
      "result": {...}
    }
  ],
  "rounds": 2,
  "timestamp": "2026-01-17T12:00:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Calculate environmental benefits of planting 1 American Sycamore for 20 years"
  }'
```

---

### `WS /api/agent/ws/{conversation_id}`
WebSocket endpoint for real-time streaming chat

**Usage (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/agent/ws/my-conversation-id');

ws.onopen = () => {
  ws.send(JSON.stringify({
    message: 'Hello SmartCanopy!'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'chunk':
      // Streaming text chunk
      console.log(data.text);
      break;

    case 'tool_use':
      // Agent is using a tool
      console.log('Using tool:', data.tool_name);
      break;

    case 'tool_result':
      // Tool execution complete
      console.log('Tool completed:', data.tool_name);
      break;

    case 'complete':
      // Response fully generated
      console.log('Full response:', data.full_response);
      break;

    case 'error':
      // Error occurred
      console.error('Error:', data.message);
      break;
  }
};
```

**Message Types:**
- `chunk` - Text streaming chunk
- `tool_use` - Tool being executed (includes tool_name, tool_input)
- `tool_result` - Tool execution complete
- `complete` - Response fully generated (includes full_response, tool_calls)
- `error` - Error message

---

### `GET /api/agent/conversations/{conversation_id}`
Get conversation history (placeholder - not yet implemented)

### `DELETE /api/agent/conversations/{conversation_id}`
Delete conversation (placeholder - not yet implemented)

---

## Species Database Endpoints

### `GET /api/species/search`
Search plant species database

**Query Parameters:**
- `query` (string): Search by common or scientific name
- `hardiness_zone` (int 1-13): Filter by USDA hardiness zone
- `tree_type` (string): Filter by type (deciduous, evergreen, conifer)
- `purpose` (string): Filter by purpose (shade, privacy, wildlife, aesthetic, stormwater)
- `native_only` (bool): Only native species
- `drought_tolerant` (bool): Filter drought-tolerant species
- `max_height_ft` (int): Maximum mature height
- `limit` (int 1-100): Maximum results (default: 20)

**Examples:**
```bash
# Search all species
curl "http://localhost:8000/api/species/search?limit=5"

# Search by hardiness zone
curl "http://localhost:8000/api/species/search?hardiness_zone=10"

# Search by name
curl "http://localhost:8000/api/species/search?query=oak"

# Native drought-tolerant trees under 30ft
curl "http://localhost:8000/api/species/search?native_only=true&drought_tolerant=true&max_height_ft=30"
```

**Response:**
```json
[
  {
    "species_id": "PLOC",
    "common_name": "American Sycamore",
    "scientific_name": "Platanus occidentalis",
    "tree_type": "deciduous",
    "mature_height_ft": 70,
    "mature_spread_ft": 50,
    "hardiness_zone_min": 4,
    "hardiness_zone_max": 9,
    "drought_tolerant": false,
    "native_regions": ["eastern_us"],
    "co2_sequestration_kg_year": 195.0,
    "stormwater_interception_gal_year": 752.0,
    "air_pollution_removal_kg_year": 2.1,
    "price_6ft": 120.0
  }
]
```

---

### `GET /api/species/{species_id}`
Get detailed species information

**Example:**
```bash
curl "http://localhost:8000/api/species/PLOC"
```

**Response:**
```json
{
  "species_id": "PLOC",
  "common_name": "American Sycamore",
  "scientific_name": "Platanus occidentalis",
  "tree_type": "deciduous",
  "mature_height_ft": 70,
  "mature_spread_ft": 50,
  "hardiness_zone_min": 4,
  "hardiness_zone_max": 9,
  "drought_tolerant": false,
  "native_regions": ["eastern_us"],
  "co2_sequestration_kg_year": 195.0,
  "stormwater_interception_gal_year": 752.0,
  "air_pollution_removal_kg_year": 2.1,
  "price_6ft": 120.0,
  "growth_rate": "fast",
  "sunlight_requirements": "full_sun",
  "moisture_tolerance": "wet",
  "soil_types": ["clay", "loam", "sandy"],
  "maintenance_level": "low",
  "maintenance_notes": {...},
  "created_at": "2026-01-17T12:00:00Z"
}
```

---

### `GET /api/species/`
List all species with pagination

**Query Parameters:**
- `limit` (int 1-200): Results per page (default: 50)
- `offset` (int): Number to skip (default: 0)

**Example:**
```bash
curl "http://localhost:8000/api/species/?limit=10&offset=0"
```

---

## Computer Vision Endpoints

### `POST /api/cv/analyze`
Run CV model analysis on an address

**Request Body:**
```json
{
  "address": "123 Main St, San Francisco, CA",
  "buffer_m": 100,
  "save_images": true
}
```

**Parameters:**
- `address` (required): Full address to analyze
- `buffer_m` (50-500): Analysis radius in meters (default: 100)
- `save_images` (bool): Save RGB/NDVI/slope images to disk

**Response:**
```json
{
  "analysis_id": "uuid",
  "address": "123 Main St, San Francisco, CA 94102",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "planting_sites": [
    {
      "site_id": "uuid",
      "location_lat": 37.7749,
      "location_lon": -122.4194,
      "avg_ndvi": 0.45,
      "ndvi_category": "moderate_vegetation",
      "avg_slope": 3.2,
      "slope_category": "flat",
      "area_sq_ft": 250,
      "suitability_score": 0.78,
      "has_nearby_roads": true,
      "has_nearby_buildings": false
    }
  ],
  "existing_trees_count": 12,
  "imagery_saved": true,
  "timestamp": "2026-01-17T12:00:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/cv/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "address": "Golden Gate Park, San Francisco, CA",
    "buffer_m": 100
  }'
```

**Note:** Requires Google Earth Engine authentication

---

### `GET /api/cv/analysis/{analysis_id}`
Get CV analysis results by ID

**Example:**
```bash
curl "http://localhost:8000/api/cv/analysis/uuid-here"
```

---

## Site Data Endpoints

### `GET /api/sites/{site_id}`
Get planting site details

**Example:**
```bash
curl "http://localhost:8000/api/sites/uuid-here"
```

**Response:**
```json
{
  "site_id": "uuid",
  "address": "123 Main St, San Francisco, CA",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "avg_ndvi": 0.45,
  "ndvi_category": "moderate_vegetation",
  "avg_slope": 3.2,
  "slope_category": "flat",
  "area_sq_ft": 250,
  "suitability_score": 0.78,
  "recommended_max_height_ft": 35,
  "recommended_max_spread_ft": 27,
  "has_nearby_roads": true,
  "has_nearby_buildings": false,
  "osm_data": {...}
}
```

---

### `POST /api/sites/{site_id}/photo`
Upload and analyze site photo

**Form Data:**
- `file` (required): Image file (JPEG/PNG, max 10MB)
- `question` (optional): Specific question about the site

**Example:**
```bash
curl -X POST http://localhost:8000/api/sites/uuid-here/photo \
  -F "file=@site_photo.jpg" \
  -F "question=Is this site suitable for planting?"
```

**Response:**
```json
{
  "photo_id": "uuid",
  "site_id": "uuid",
  "analysis": {
    "site_characteristics": {
      "dimensions": "Approximately 15x20 feet",
      "sunlight_exposure": "Full sun, south-facing",
      "soil_condition": "Well-drained, appears healthy"
    },
    "existing_features": [...],
    "suitability_assessment": {
      "overall_rating": "highly_suitable",
      "recommended_tree_sizes": ["medium", "large"]
    },
    "recommendations": [...]
  },
  "file_path": "uploads/uuid.jpg"
}
```

---

### `GET /api/sites/{site_id}/photos`
Get all photos for a site

**Example:**
```bash
curl "http://localhost:8000/api/sites/uuid-here/photos"
```

---

## Error Responses

All endpoints return errors in a consistent format:

```json
{
  "error": {
    "message": "Error description",
    "status_code": 400
  }
}
```

**Common Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid input)
- `404` - Not Found
- `500` - Internal Server Error

---

## Agent Tools

When chatting with the agent, it can automatically use these 7 tools:

### 1. Species Recommender
Recommends tree species based on site conditions

**Triggered by:** "recommend trees", "what should I plant", "best species for..."

**Requires:** Site ID from CV analysis

### 2. Pricing Calculator
Estimates costs for trees and planting

**Triggered by:** "how much", "cost", "price", "budget"

**Parameters:** Species, quantity, tree size, ZIP code

### 3. Environmental Calculator
Calculates CO2, stormwater, air quality benefits

**Triggered by:** "environmental benefits", "CO2", "carbon", "stormwater"

**Returns:** Relatable equivalents (car-free days, bathtubs of water)

### 4. Hazard Checker
Verifies safety clearances

**Triggered by:** "safe to plant", "clearances", "utilities"

**Checks:** Buildings, roads, overhead utilities

### 5. Photo Analyzer
Analyzes uploaded site photos

**Triggered by:** Photo upload via site endpoint

**Uses:** Claude Vision API

### 6. Maintenance Guide
Provides care instructions

**Triggered by:** "how to care", "maintenance", "watering", "pruning"

**Customizes by:** Tree age, season, species

### 7. Planting Instructions
Step-by-step planting guide

**Triggered by:** "how to plant", "planting steps", "instructions"

**Includes:** Tools needed, timing, site-specific notes

---

## Testing the API

### Run Test Suite

```bash
python3 scripts/test_api.py
```

### Manual Testing with curl

```bash
# Health check
curl http://localhost:8000/api/health

# Chat with agent
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about environmental benefits of trees"}'

# Search species
curl "http://localhost:8000/api/species/search?query=oak&limit=5"

# Get species details
curl "http://localhost:8000/api/species/PLOC"
```

### Testing with Python

```python
import httpx
import asyncio

async def test_chat():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/agent/chat",
            json={
                "message": "Calculate benefits of 1 American Sycamore for 20 years"
            },
            timeout=30.0
        )

        data = response.json()
        print(data['response'])
        print(f"Tools used: {len(data['tool_calls'])}")

asyncio.run(test_chat())
```

---

## Rate Limiting

Default: 100 requests per minute per IP

Configure in `.env`:
```bash
RATE_LIMIT_PER_MINUTE=100
```

---

## CORS

Allowed origins (configure in `.env`):
```bash
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:5173
```

---

## Deployment

### Production Checklist

1. Set `DEBUG=false` in `.env`
2. Use production database URL
3. Configure proper `ALLOWED_ORIGINS`
4. Set up HTTPS/SSL
5. Configure rate limiting
6. Set up monitoring/logging
7. Use production WSGI server (gunicorn + uvicorn workers)

### Example Production Command

```bash
gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

---

## Support

For issues or questions:
- Check the test suite: `python3 scripts/test_api.py`
- Review logs: Set `LOG_LEVEL=DEBUG` in `.env`
- See project documentation: [README.md](README.md), [PROJECT_STATUS.md](PROJECT_STATUS.md)

---

**Built with:** FastAPI, Claude AI, PostgreSQL, Redis, Google Earth Engine
**For:** SmartCanopy AI - Science Fair 2026
