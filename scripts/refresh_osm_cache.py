"""
Download and cache OpenStreetMap infrastructure data for the Bay Area (OCF service area).

Run once before deployment, then monthly to stay current:
    python scripts/refresh_osm_cache.py

Outputs three GeoPackage files to cache/:
    ocf_roads.gpkg      — highway network for Santa Clara + Alameda counties
    ocf_buildings.gpkg  — building footprints
    ocf_parking.gpkg    — parking areas

These files are loaded by OSMFilter at startup, eliminating live OSM API calls
during analysis and making infrastructure filtering faster and more reliable.
"""

import os
import sys
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache')

# OCF service area: Santa Clara County + parts of Alameda County
# Bounding box covers San Jose, Santa Clara, Sunnyvale, Mountain View, Palo Alto,
# Milpitas, Fremont (southern Alameda), and surrounding cities.
BBOX_WEST = -122.25
BBOX_SOUTH = 37.10
BBOX_EAST = -121.55
BBOX_NORTH = 37.60

AREA_POLYGON = box(BBOX_WEST, BBOX_SOUTH, BBOX_EAST, BBOX_NORTH)


def fetch_and_save(tags: dict, out_path: str, layer_name: str):
    print(f"\nFetching {layer_name}…")
    try:
        gdf = ox.features.features_from_polygon(AREA_POLYGON, tags=tags)
        # Keep only geometry + a minimal set of attributes to reduce file size
        keep_cols = [c for c in gdf.columns if c in ("geometry", "highway", "building", "amenity", "name")]
        gdf = gdf[keep_cols].copy()
        gdf = gdf[gdf.geometry.notna()]
        gdf.to_file(out_path, driver="GPKG")
        print(f"  ✓ Saved {len(gdf)} features → {out_path}")
    except Exception as e:
        print(f"  ✗ Failed to fetch {layer_name}: {e}")
        raise


def main():
    os.makedirs(CACHE_DIR, exist_ok=True)

    print("=" * 60)
    print("Refreshing OCF Bay Area OSM Cache")
    print(f"Bounding box: {BBOX_SOUTH}°N {BBOX_WEST}°E → {BBOX_NORTH}°N {BBOX_EAST}°E")
    print("=" * 60)

    fetch_and_save(
        tags={"highway": True},
        out_path=os.path.join(CACHE_DIR, "ocf_roads.gpkg"),
        layer_name="roads",
    )
    fetch_and_save(
        tags={"building": True},
        out_path=os.path.join(CACHE_DIR, "ocf_buildings.gpkg"),
        layer_name="buildings",
    )
    fetch_and_save(
        tags={"amenity": "parking"},
        out_path=os.path.join(CACHE_DIR, "ocf_parking.gpkg"),
        layer_name="parking",
    )

    print("\n✓ OSM cache refresh complete.")
    print(f"  Files saved in: {os.path.abspath(CACHE_DIR)}")
    print("  Run this script monthly to keep infrastructure data current.")


if __name__ == "__main__":
    main()
