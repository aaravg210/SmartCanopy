# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Urban Tree Planting Site Detection** system that identifies optimal locations for planting new trees in urban areas using satellite imagery, AI-powered tree detection, and geospatial analysis.

The system analyzes addresses to:
1. Fetch satellite imagery (NAIP) from Google Earth Engine
2. Detect existing trees using DeepForest (pre-trained object detection model)
3. Calculate vegetation health (NDVI) and terrain characteristics (slope)
4. Filter out infrastructure (roads, buildings, parking) using OpenStreetMap
5. Recommend optimal planting sites with suitability scores

## Environment Setup

### Python Environment
- Python 3.13
- Use the existing virtual environment: `source venv/bin/activate`

### Activate:
Before running scripts, activate the venv with:
source venv/bin/activate


### Google Earth Engine Authentication
**CRITICAL**: Before running any scripts, Google Earth Engine must be authenticated:
```bash
earthengine authenticate
```
The project is configured to use GEE project ID: `urban-tree-ai`

All scripts that use GEE call `ee.Initialize(project='urban-tree-ai')` - this will fail if authentication hasn't been completed.

## Running the System

### Test Individual Components

1. **Test GEE Connection**:
   ```bash
   python test_gee.py
   ```

2. **Test DeepForest Tree Detection**:
   ```bash
   python test_deepforest.py
   ```
   Note: Modify the `image_path` variable in `__main__` to point to an existing RGB image

3. **Test Data Pipeline** (fetch imagery for an address):
   ```bash
   python data_pipeline.py
   ```
   Modify `test_address` in `__main__` to analyze different locations

4. **Download Imagery Locally**:
   ```bash
   python download_imagery.py
   ```
   Modify `test_address` and `output_dir` as needed

5. **Test OSM Infrastructure Filtering**:
   ```bash
   python osm_filter.py
   ```

### Full Analysis Pipeline

Run the complete planting site detection:
```bash
python planting_site_detector.py
```

Modify the `test_address` and `buffer_m` (analysis radius in meters) in the `__main__` block to analyze different locations.

## Architecture

### Data Flow Pipeline

```
Address Input
    ↓
[data_pipeline.py] → Geocoding (geopy) → Coordinates
    ↓
    └→ Google Earth Engine
       ├→ Fetch NAIP imagery (RGB + NIR)
       ├→ Calculate NDVI
       └→ Fetch terrain (elevation, slope)
    ↓
[download_imagery.py] → Download images locally
    ↓
[test_deepforest.py] → DeepForest model → Existing tree locations
    ↓
[osm_filter.py] → OpenStreetMap → Infrastructure exclusion masks
    ↓
[planting_site_detector.py] → Combine all data
    ↓
Planting Site Recommendations (with suitability scores)
```

### Key Components

**data_pipeline.py** (`TreeDataPipeline` class):
- Core GEE integration
- Geocoding addresses to coordinates
- Fetching NAIP imagery (RGB + NIR bands)
- NDVI calculation: `(NIR - Red) / (NIR + Red)`
- Terrain data from SRTM DEM
- Generates visualization URLs for GEE images

**download_imagery.py** (`ImageryDownloader` class):
- Downloads GEE imagery to local files (RGB, NDVI, slope)
- Saves to `test_data/` or `analysis_data/` directories
- Creates filename-safe address strings

**test_deepforest.py** (`DeepForestDetector` class):
- Loads pre-trained DeepForest model for tree detection
- `predict_trees()`: Detects trees in RGB images with confidence threshold
- Returns bounding boxes (xmin, ymin, xmax, ymax) with confidence scores
- `visualize_predictions()`: Creates visualization with detected trees

**osm_filter.py** (`OSMFilter` class):
- Fetches infrastructure from OpenStreetMap (roads, buildings, parking)
- Creates binary exclusion masks (True = don't plant here)
- Applies 3-meter buffer around infrastructure
- Filters planting sites to avoid infrastructure

**planting_site_detector.py** (`PlantingSiteDetector` class):
- Orchestrates the complete analysis pipeline
- Combines tree detection, NDVI, slope, and OSM filtering
- `find_planting_sites()`: Identifies suitable locations using:
  - NDVI range: 0.15-0.65 (enough vegetation, not dense forest)
  - Slope: < 15° (flat enough to plant)
  - No existing trees (from DeepForest)
  - Minimum area: 100 pixels
- Calculates suitability scores (0-1) based on NDVI and slope
- `visualize_with_osm()`: Creates visualization showing exclusions and recommended sites

### Data Storage

- `cache/`: GEE API response caching (JSON files by hash)
- `test_data/`: Sample downloaded imagery for testing
- `analysis_data/`: Full analysis outputs with imagery and results
- `claude/skills/`: Claude Code skills from anthropics/skills repository

### Key Parameters

**Buffer Radius** (`buffer_m`):
- Default: 100m for analysis, 500m for data fetching
- Controls the geographic area analyzed around the address
- Larger buffers = more area but slower processing

**NDVI Thresholds** (in `planting_site_detector.py:find_planting_sites()`):
- Min: 0.15 (excludes pavement, bare soil)
- Max: 0.65 (excludes dense existing forest)
- Adjust these to change what counts as "suitable"

**Slope Threshold**:
- Max: 15° (in `find_planting_sites()`)
- Terrain steeper than this is excluded

**DeepForest Confidence**:
- Default: 0.3 (in `test_deepforest.py:predict_trees()`)
- Lower = more tree detections (including false positives)
- Higher = fewer, more confident detections

## Important Notes

### Coordinate Systems
- Input/output: WGS84 lat/lon (EPSG:4326)
- OSM buffering temporarily converts to Web Mercator (EPSG:3857) for meter-based buffers

### Image Resolution
- NAIP imagery: 1m resolution (typical)
- SRTM terrain: 30m resolution
- Downloaded images: 512x512 pixels by default (controlled in `get_image_url()`)

### GEE Rate Limits
- The system uses GEE's `getThumbURL()` which has rate limits
- Large buffer areas or many requests may hit limits
- The `cache/` directory helps avoid repeated GEE requests

### Model Files
- DeepForest downloads pre-trained weights on first run via `model.use_release()`
- Subsequent runs use cached weights
