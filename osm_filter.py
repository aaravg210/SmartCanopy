# OpenStreetMap Integration
# Filters planting sites using road, building, and parking footprints.
# For Bay Area deployments: pre-cache county OSM data with scripts/refresh_osm_cache.py
# and set OSM_CACHE_DIR to avoid live fetching on every analysis.

import os
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point, box
import numpy as np
from PIL import Image
import rasterio
from rasterio import features

# Clearance distances (meters) — planted trees must not be closer than these
BUFFER_ROAD_M = 8       # roads (was 3m; raised for root/utility clearance)
BUFFER_BUILDING_M = 5   # buildings
BUFFER_PARKING_M = 5    # parking lots

# A site is rejected if ANY excluded pixel falls within this radius of its centre (pixels).
# Set to 0 to reject only when the exact centre pixel is excluded.
SITE_REJECTION_RADIUS_PX = 3

# Path to pre-downloaded Bay Area OSM GeoPackage files.
# Set environment variable OSM_CACHE_DIR to override, or keep as default.
_DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
OSM_CACHE_DIR = os.environ.get("OSM_CACHE_DIR", _DEFAULT_CACHE_DIR)

CACHE_ROADS_PATH = os.path.join(OSM_CACHE_DIR, "ocf_roads.gpkg")
CACHE_BUILDINGS_PATH = os.path.join(OSM_CACHE_DIR, "ocf_buildings.gpkg")
CACHE_PARKING_PATH = os.path.join(OSM_CACHE_DIR, "ocf_parking.gpkg")


class OSMFilter:
    """Filters planting sites using OpenStreetMap infrastructure data."""

    def __init__(self):
        self._roads_cache: gpd.GeoDataFrame = None
        self._buildings_cache: gpd.GeoDataFrame = None
        self._parking_cache: gpd.GeoDataFrame = None
        self._cache_loaded = False
        print("✓ OSM Filter initialized")

    def _load_cache(self):
        """Load pre-downloaded Bay Area OSM data from disk (fast path)."""
        if self._cache_loaded:
            return
        try:
            if os.path.exists(CACHE_ROADS_PATH):
                self._roads_cache = gpd.read_file(CACHE_ROADS_PATH)
                print(f"  ✓ Loaded OSM roads cache ({len(self._roads_cache)} features)")
            if os.path.exists(CACHE_BUILDINGS_PATH):
                self._buildings_cache = gpd.read_file(CACHE_BUILDINGS_PATH)
                print(f"  ✓ Loaded OSM buildings cache ({len(self._buildings_cache)} features)")
            if os.path.exists(CACHE_PARKING_PATH):
                self._parking_cache = gpd.read_file(CACHE_PARKING_PATH)
                print(f"  ✓ Loaded OSM parking cache ({len(self._parking_cache)} features)")
            self._cache_loaded = True
        except Exception as e:
            print(f"  ⚠  Could not load OSM cache: {e} — will fetch live")

    def _clip_to_bbox(self, gdf: gpd.GeoDataFrame, bbox_geom) -> gpd.GeoDataFrame:
        """Spatial clip to a bounding box geometry (WGS84)."""
        if gdf is None or len(gdf) == 0:
            return gpd.GeoDataFrame()
        return gdf[gdf.intersects(bbox_geom)].copy()

    def get_infrastructure_data(self, lat: float, lon: float, buffer_m: int = 100):
        """
        Return road, building, and parking GeoDataFrames for a location.

        Uses pre-downloaded Bay Area cache files when available; falls back to
        live OSM API fetch.
        """
        print(f"Fetching OpenStreetMap data for ({lat:.5f}, {lon:.5f})…")
        self._load_cache()

        # Build a bounding-box polygon slightly larger than the analysis area
        # so we catch infrastructure that straddles the edge.
        metres_per_deg_lat = 111320
        metres_per_deg_lon = 111320 * np.cos(np.radians(lat))
        lat_buf = (buffer_m + 20) / metres_per_deg_lat
        lon_buf = (buffer_m + 20) / metres_per_deg_lon
        bbox_geom = box(lon - lon_buf, lat - lat_buf, lon + lon_buf, lat + lat_buf)

        roads = self._fetch_layer(
            "roads", lat, lon, buffer_m, bbox_geom,
            self._roads_cache, {"highway": True}
        )
        buildings = self._fetch_layer(
            "buildings", lat, lon, buffer_m, bbox_geom,
            self._buildings_cache, {"building": True}
        )
        parking = self._fetch_layer(
            "parking", lat, lon, buffer_m, bbox_geom,
            self._parking_cache, {"amenity": "parking"}
        )

        return {"roads": roads, "buildings": buildings, "parking": parking}

    def _fetch_layer(self, name: str, lat: float, lon: float, buffer_m: int,
                     bbox_geom, cache: gpd.GeoDataFrame, tags: dict) -> gpd.GeoDataFrame:
        """Return features for one layer, preferring cache over live API."""
        if cache is not None and len(cache) > 0:
            result = self._clip_to_bbox(cache, bbox_geom)
            print(f"  - {name} (cache): {len(result)} features")
            return result

        # Live fetch fallback
        try:
            gdf = ox.features.features_from_point(
                (lat, lon), tags=tags, dist=buffer_m
            )
            print(f"  ✓ {name} (live): {len(gdf)} features")
            return gdf
        except Exception as e:
            print(f"  ⚠  No {name} found or error: {e}")
            return gpd.GeoDataFrame()

    def create_exclusion_mask(self, osm_data: dict, lat: float, lon: float,
                              image_width: int, image_height: int,
                              buffer_m: int = 100) -> np.ndarray:
        """
        Build a binary mask of pixels to EXCLUDE from planting.

        Uses larger clearance buffers than the original implementation to be more
        conservative. The mask is True where planting is NOT allowed.
        """
        print("Creating exclusion mask from OSM data…")

        metres_per_degree_lat = 111320
        metres_per_degree_lon = 111320 * np.cos(np.radians(lat))
        lat_buf = buffer_m / metres_per_degree_lat
        lon_buf = buffer_m / metres_per_degree_lon

        bounds = {
            "minx": lon - lon_buf, "maxx": lon + lon_buf,
            "miny": lat - lat_buf, "maxy": lat + lat_buf,
        }

        from rasterio.transform import from_bounds
        transform = from_bounds(
            bounds["minx"], bounds["miny"],
            bounds["maxx"], bounds["maxy"],
            image_width, image_height,
        )

        exclusion_mask = np.zeros((image_height, image_width), dtype=bool)

        layer_buffers = {
            "roads": BUFFER_ROAD_M,
            "buildings": BUFFER_BUILDING_M,
            "parking": BUFFER_PARKING_M,
        }

        for name, gdf in osm_data.items():
            if len(gdf) == 0:
                continue
            clearance_m = layer_buffers.get(name, BUFFER_ROAD_M)
            print(f"  - Masking {name} (buffer: {clearance_m}m)…")
            try:
                gdf_buf = gdf.copy()
                gdf_buf = gdf_buf.to_crs(epsg=3857)
                gdf_buf["geometry"] = gdf_buf.geometry.buffer(clearance_m)
                gdf_buf = gdf_buf.to_crs(epsg=4326)

                shapes = [(geom, 1) for geom in gdf_buf.geometry if geom is not None]
                if not shapes:
                    continue

                mask_layer = features.rasterize(
                    shapes,
                    out_shape=(image_height, image_width),
                    transform=transform,
                    fill=0,
                    dtype=np.uint8,
                )
                exclusion_mask |= mask_layer.astype(bool)
            except Exception as e:
                print(f"    ⚠  Error masking {name}: {e}")

        excluded_pct = exclusion_mask.sum() / (image_width * image_height) * 100
        print(f"✓ Exclusion mask: {excluded_pct:.1f}% of image excluded")
        return exclusion_mask

    def filter_planting_sites(self, suitable_sites: list,
                               exclusion_mask: np.ndarray) -> list:
        """
        Remove planting sites that overlap with excluded infrastructure.

        A site is rejected if its centre pixel OR any pixel within
        SITE_REJECTION_RADIUS_PX of its centre is excluded (zero-tolerance
        for safety — the old 30 % threshold was too permissive).
        """
        print("Filtering planting sites against infrastructure mask…")
        filtered = []

        for site in suitable_sites:
            x, y = site["location"]

            # Check centre pixel
            if exclusion_mask[y, x]:
                continue

            # Check neighbourhood radius
            if SITE_REJECTION_RADIUS_PX > 0:
                r = SITE_REJECTION_RADIUS_PX
                y_min = max(0, y - r)
                y_max = min(exclusion_mask.shape[0], y + r + 1)
                x_min = max(0, x - r)
                x_max = min(exclusion_mask.shape[1], x + r + 1)
                if exclusion_mask[y_min:y_max, x_min:x_max].any():
                    continue

            filtered.append(site)

        print(f"✓ Filtered: {len(suitable_sites)} → {len(filtered)} sites "
              f"({len(suitable_sites) - len(filtered)} removed near infrastructure)")
        return filtered


if __name__ == "__main__":
    osm_filter = OSMFilter()
    lat, lon = 37.33548, -121.88823  # San Jose City Hall
    osm_data = osm_filter.get_infrastructure_data(lat, lon, buffer_m=100)
    print("\n✓ OSM Filter working")
    print(f"  Roads: {len(osm_data['roads'])}")
    print(f"  Buildings: {len(osm_data['buildings'])}")
    print(f"  Parking: {len(osm_data['parking'])}")
