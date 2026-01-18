# OpenStreetMap Integration

import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point, box
import numpy as np
from PIL import Image
import rasterio
from rasterio import features

class OSMFilter:
    """Filters planting sites using OpenStreetMap data"""
    
    def __init__(self):
        """Initialize OSM filter"""
        print("✓ OSM Filter initialized")
    
    def get_infrastructure_data(self, lat: float, lon: float, buffer_m: int = 100):
        """
        Fetch infrastructure data from OpenStreetMap
        
        Args:
            lat: Latitude
            lon: Longitude
            buffer_m: Buffer radius in meters
            
        Returns:
            Dictionary with roads, buildings, etc.
        """
        print(f"Fetching OpenStreetMap data for ({lat}, {lon})...")
        
        try:
            # Get roads/highways
            print("  - Fetching roads...")
            roads = ox.features.features_from_point(
                (lat, lon),
                tags={'highway': True},
                dist=buffer_m
            )
            print(f"    ✓ Found {len(roads)} road segments")
        except Exception as e:
            print(f"    ⚠️  No roads found or error: {e}")
            roads = gpd.GeoDataFrame()
        
        try:
            # Get buildings
            print("  - Fetching buildings...")
            buildings = ox.features.features_from_point(
                (lat, lon),
                tags={'building': True},
                dist=buffer_m
            )
            print(f"    ✓ Found {len(buildings)} buildings")
        except Exception as e:
            print(f"    ⚠️  No buildings found or error: {e}")
            buildings = gpd.GeoDataFrame()
        
        try:
            # Get parking areas
            print("  - Fetching parking areas...")
            parking = ox.features.features_from_point( 
                (lat, lon),
                tags={'amenity': 'parking'},
                dist=buffer_m
            )
            print(f"    ✓ Found {len(parking)} parking areas")
        except Exception as e:
            print(f"    ⚠️  No parking found or error: {e}")
            parking = gpd.GeoDataFrame()
        
        return {
            'roads': roads,
            'buildings': buildings,
            'parking': parking
        }
    
    def create_exclusion_mask(self, osm_data: dict, lat: float, lon: float, 
                             image_width: int, image_height: int, 
                             buffer_m: int = 100):
        """
        Create a binary mask of areas to EXCLUDE from planting
        
        Args:
            osm_data: Dictionary from get_infrastructure_data()
            lat, lon: Center coordinates
            image_width, image_height: Size of the satellite image in pixels
            buffer_m: Buffer radius in meters
            
        Returns:
            numpy array (True = exclude, False = okay to plant)
        """
        print("Creating exclusion mask from OSM data...")
        
        # Calculate bounds in geographic coordinates
        # Approximate: 1 degree latitude ≈ 111km
        # 1 degree longitude varies by latitude, but roughly ≈ 111km * cos(lat)
        meters_per_degree_lat = 111320
        meters_per_degree_lon = 111320 * np.cos(np.radians(lat))
        
        padding_factor = 1.1
        lat_buffer = buffer_m / meters_per_degree_lat
        lon_buffer = buffer_m / meters_per_degree_lon
        
        bounds = {
            'minx': lon - lon_buffer,
            'maxx': lon + lon_buffer,
            'miny': lat - lat_buffer,
            'maxy': lat + lat_buffer
        }
        
        # Create transform (maps pixel coordinates to geographic coordinates)
        from rasterio.transform import from_bounds
        transform = from_bounds(
            bounds['minx'], bounds['miny'],
            bounds['maxx'], bounds['maxy'],
            image_width, image_height
        )
        
        # Initialize empty mask
        exclusion_mask = np.zeros((image_height, image_width), dtype=bool)
        
        # Rasterize each infrastructure type
        for name, gdf in osm_data.items():
            if len(gdf) == 0:
                continue
            
            print(f"  - Masking {name}...")
            
            # Convert geometries to mask
            try:
                # Add buffer to roads/buildings (don't plant too close)
                gdf_buffered = gdf.copy()
                gdf_buffered = gdf_buffered.to_crs(epsg=3857)           # convert to meters
                gdf_buffered['geometry'] = gdf_buffered.geometry.buffer(3)  # 3 meters
                gdf_buffered = gdf_buffered.to_crs(epsg=4326)           # convert back to lat/lon
                
                # Rasterize
                shapes = [(geom, 1) for geom in gdf_buffered.geometry]
                mask_layer = features.rasterize(
                    shapes,
                    out_shape=(image_height, image_width),
                    transform=transform,
                    fill=0,
                    dtype=np.uint8
                )
                
                exclusion_mask = exclusion_mask | (mask_layer > 0)
                
            except Exception as e:
                print(f"    ⚠️  Error masking {name}: {e}")
        
        excluded_pixels = np.sum(exclusion_mask)
        excluded_percent = (excluded_pixels / (image_width * image_height)) * 100
        
        print(f"✓ Exclusion mask created")
        print(f"  Excluded area: {excluded_percent:.1f}% of image")
        
        return exclusion_mask
    
    def filter_planting_sites(self, suitable_sites: list, exclusion_mask: np.ndarray):
        """
        Filter out planting sites that overlap with excluded areas
        
        Args:
            suitable_sites: List of planting sites from planting_site_detector
            exclusion_mask: Boolean mask (True = exclude)
            
        Returns:
            Filtered list of planting sites
        """
        print("Filtering planting sites with OSM data...")
        
        filtered_sites = []
        
        for site in suitable_sites:
            x, y = site['location']
            
            # Check if site center is in excluded area
            if exclusion_mask[y, x]:
                continue  # Skip this site
            
            # Check if majority of site area is excluded
            # (For sites with area_pixels, check a small region around center)
            check_radius = 5  # pixels
            y_min = max(0, y - check_radius)
            y_max = min(exclusion_mask.shape[0], y + check_radius)
            x_min = max(0, x - check_radius)
            x_max = min(exclusion_mask.shape[1], x + check_radius)
            
            region = exclusion_mask[y_min:y_max, x_min:x_max]
            excluded_fraction = np.sum(region) / region.size
            
            if excluded_fraction < 0.3:  # Less than 30% excluded
                filtered_sites.append(site)
        
        print(f"✓ Filtered: {len(suitable_sites)} → {len(filtered_sites)} sites")
        print(f"  Removed: {len(suitable_sites) - len(filtered_sites)} sites on infrastructure")
        
        return filtered_sites


if __name__ == "__main__":
    # Test the OSM filter
    osm_filter = OSMFilter()
    
    # Test coordinates
    lat, lon = 37.24421, -121.78934  # Coords 37.24421° N, 121.78934° W

    # Fetch data
    osm_data = osm_filter.get_infrastructure_data(lat, lon, buffer_m=100)
    
    print("\n✓ OSM Filter is working!")
    print("\nData fetched:")
    print(f"  - Roads: {len(osm_data['roads'])} segments")
    print(f"  - Buildings: {len(osm_data['buildings'])} structures")
    print(f"  - Parking: {len(osm_data['parking'])} areas")


