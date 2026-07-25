"""
Core Data Pipeline for Urban Tree Analysis
Fetches satellite imagery, NDVI, and terrain data from Google Earth Engine
"""

import ee
import json
import os
from geopy.geocoders import Nominatim
from typing import Optional, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor

_GEE_PROJECT = os.environ.get('GEE_PROJECT', 'urban-tree-ai')


def _init_gee():
    """
    Initialize GEE, preferring a service account JSON credential for headless
    production deployments (Oracle Cloud, Docker, etc.).

    Priority:
    1. GOOGLE_APPLICATION_CREDENTIALS_JSON env var — JSON string of a GCP
       Service Account key with Earth Engine API access. Set this in production.
    2. Interactive / Application Default Credentials — used for local dev after
       running `earthengine authenticate`.
    """
    sa_json = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if sa_json:
        creds_dict = json.loads(sa_json)
        service_email = creds_dict['client_email']
        credentials = ee.ServiceAccountCredentials(service_email, key_data=sa_json)
        ee.Initialize(credentials=credentials, project=_GEE_PROJECT)
        print("✓ GEE initialized via service account")
    else:
        ee.Initialize(project=_GEE_PROJECT)
        print("✓ GEE initialized via application default credentials")


class TreeDataPipeline:
    """Handles all data fetching from Google Earth Engine"""

    def __init__(self):
        """Initialize GEE and geocoder"""
        try:
            _init_gee()
        except Exception as e:
            print("✗ GEE init failed. For local dev: run `earthengine authenticate`. "
                  "For production: set GOOGLE_APPLICATION_CREDENTIALS_JSON env var.")
            raise e
        
        self.geocoder = Nominatim(user_agent="urban_tree_planner_v1")
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert address to coordinates
        
        Args:
            address: Street address (e.g., "123 Main St, New York, NY")
            
        Returns:
            (latitude, longitude) or None if failed
        """
        try:
            print(f"Geocoding: {address}")
            location = self.geocoder.geocode(address)
            
            if location:
                print(f"✓ Found coordinates: ({location.latitude}, {location.longitude})")
                return (location.latitude, location.longitude)
            else:
                print(f"✗ Could not find location for: {address}")
                return None
                
        except Exception as e:
            print(f"✗ Geocoding error: {e}")
            return None
    
    def get_naip_imagery(self, lat: float, lon: float, buffer_m: int = 500):
        """
        Fetch NAIP imagery for a location
        
        Args:
            lat: Latitude
            lon: Longitude  
            buffer_m: Buffer radius in meters (default 500m)
            
        Returns:
            ee.Image with RGB and NIR bands, or None if no imagery
        """
        print(f"Fetching NAIP imagery (buffer: {buffer_m}m)...")
        
        point = ee.Geometry.Point([lon, lat])
        region = point.buffer(buffer_m).bounds()
        
        # Get most recent NAIP imagery
        naip = ee.ImageCollection('USDA/NAIP/DOQQ') \
            .filterBounds(region) \
            .filterDate('2017-01-01', '2024-12-31') \
            .sort('system:time_start', False) \
            .first()
        
        if naip:
            naip = naip.clip(region)
            print("✓ NAIP imagery found")
            return naip
        else:
            print("✗ No NAIP imagery found for this location")
            return None
    
    def calculate_ndvi(self, image) -> ee.Image:
        """
        Calculate NDVI from NAIP imagery
        
        NDVI = (NIR - Red) / (NIR + Red)
        Higher values = more/healthier vegetation
        
        Args:
            image: NAIP ee.Image (has R, G, B, N bands)
            
        Returns:
            ee.Image with NDVI band added
        """
        print("Calculating NDVI...")
        
        # NAIP bands: R (Red), G (Green), B (Blue), N (NIR)
        nir = image.select('N')
        red = image.select('R')
        
        # Calculate NDVI
        ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
        
        print("✓ NDVI calculated")
        return image.addBands(ndvi)
    
    def get_terrain_data(self, lat: float, lon: float, buffer_m: int = 500):
        """
        Fetch elevation and slope data
        
        Args:
            lat: Latitude
            lon: Longitude
            buffer_m: Buffer radius in meters
            
        Returns:
            ee.Image with elevation and slope bands
        """
        print("Fetching terrain data...")
        
        point = ee.Geometry.Point([lon, lat])
        region = point.buffer(buffer_m).bounds()
        
        # SRTM Digital Elevation Model (30m resolution)
        dem = ee.Image('USGS/SRTMGL1_003').clip(region)
        
        # Calculate slope (in degrees)
        slope = ee.Terrain.slope(dem).rename('slope')
        
        # Add slope band to elevation
        terrain = dem.addBands(slope)
        
        print("✓ Terrain data retrieved")
        return terrain
    
    def get_image_url(self, image, region, bands=['R', 'G', 'B'], 
                     min_val=0, max_val=255) -> str:
        """
        Get a URL to visualize/download the image
        
        Args:
            image: ee.Image to visualize
            region: ee.Geometry for the area
            bands: List of band names to include
            min_val: Minimum value for visualization
            max_val: Maximum value for visualization
            
        Returns:
            URL string for the image
        """
        vis_params = {
            'bands': bands,
            'min': min_val,
            'max': max_val,
            'dimensions': 512,
            'region': region,
            'format': 'png'
        }
        
        url = image.getThumbURL(vis_params)
        return url
    
    def analyze_location(self, address: str, buffer_m: int = 500,
                         coords=None) -> Optional[Dict]:
        """
        Complete data fetching pipeline for a location.

        Args:
            address: Street address (used for display; geocoding is skipped when coords provided)
            buffer_m: Analysis radius in meters
            coords: Optional (lat, lon) tuple from a high-quality geocoder (e.g. Mapbox).
                    Pass this to bypass Nominatim and improve location accuracy.

        Returns:
            Dictionary with all data and metadata, or None if failed
        """
        print("\n" + "="*60)
        print(f"FETCHING DATA FOR: {address}")
        print("="*60 + "\n")

        if coords is not None:
            lat, lon = coords
            print(f"✓ Using provided coordinates: ({lat}, {lon})")
        else:
            resolved = self.geocode_address(address)
            if not resolved:
                return None
            lat, lon = resolved
        
        # Step 2: Get NAIP imagery
        naip = self.get_naip_imagery(lat, lon, buffer_m)
        if not naip:
            print("\n✗ Cannot proceed without imagery")
            return None
        
        # Step 3: Calculate NDVI
        naip_with_ndvi = self.calculate_ndvi(naip)
        
        # Step 4: Get terrain data
        terrain = self.get_terrain_data(lat, lon, buffer_m)
        
        # Step 5: Create region geometry for exports
        point = ee.Geometry.Point([lon, lat])
        region = point.buffer(buffer_m).bounds()
        
        # Step 6: Generate visualization URLs (both GEE requests in parallel)
        print("\nGenerating visualization URLs...")

        with ThreadPoolExecutor(max_workers=2) as executor:
            rgb_future = executor.submit(
                self.get_image_url, naip_with_ndvi, region, ['R', 'G', 'B'], 0, 255
            )
            ndvi_future = executor.submit(
                self.get_image_url, naip_with_ndvi, region, ['NDVI'], -1, 1
            )
            rgb_url = rgb_future.result()
            ndvi_url = ndvi_future.result()

        print("✓ Visualization URLs generated")
        
        # Step 7: Package everything
        result = {
            'address': address,
            'coordinates': coords,
            'buffer_meters': buffer_m,
            'imagery': {
                'naip': naip_with_ndvi,
                'terrain': terrain,
            },
            'urls': {
                'rgb': rgb_url,
                'ndvi': ndvi_url,
            },
            'region': region
        }
        
        print("\n" + "="*60)
        print("DATA FETCHING COMPLETE")
        print("="*60)
        print(f"\nRGB Image URL:\n{rgb_url}\n")
        print(f"NDVI Image URL:\n{ndvi_url}\n")
        
        return result


# Test the pipeline
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = TreeDataPipeline()
    
    # Test with an address - you can change it
    test_address = "Glendale, AZ"
    
    print(f"\nTesting with: {test_address}\n")
    
    result = pipeline.analyze_location(test_address, buffer_m=500)
    
    if result:
        print("\n✓ SUCCESS!")
        print("\nNext steps:")
        print("1. Open the RGB and NDVI URLs in your browser")
        print("2. Try YOUR address by changing test_address above")
        print("3. Next: Download these images for DeepForest")
    else:
        print("\n✗ FAILED - Check error messages above")