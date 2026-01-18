"""
Download imagery from Google Earth Engine for local processing
"""

import ee
import requests
from PIL import Image
from io import BytesIO
import os
from data_pipeline import TreeDataPipeline

class ImageryDownloader:
    """Downloads GEE imagery to local files"""
    
    def __init__(self):
        """Initialize"""
        self.pipeline = TreeDataPipeline()
    
    def download_image_from_url(self, url: str, save_path: str):
        """
        Download image from GEE URL
        
        Args:
            url: Image URL from getThumbURL()
            save_path: Where to save (e.g., 'output.png')
        """
        print(f"Downloading image to {save_path}...")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            img = Image.open(BytesIO(response.content))
            img.save(save_path)
            print(f"✓ Saved to {save_path}")
            
            return img
            
        except Exception as e:
            print(f"✗ Download failed: {e}")
            return None
    
    def download_for_address(self, address: str, output_dir: str = "data", 
                        buffer_m: int = 100):

        """
        Download all imagery for an address
        
        Args:
            address: Address to analyze
            output_dir: Directory to save images
            
        Returns:
            Dictionary with paths to downloaded files
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Get data from GEE
        result = self.pipeline.analyze_location(address, buffer_m=buffer_m)


        if not result:
            return None
        
        # Clean address for filename
        clean_address = address.replace(',', '').replace(' ', '_').replace('/', '_')[:50]
        
        # Download RGB image
        rgb_path = os.path.join(output_dir, f"{clean_address}_rgb.png")
        rgb_img = self.download_image_from_url(result['urls']['rgb'], rgb_path)
        
        # Download NDVI image
        ndvi_path = os.path.join(output_dir, f"{clean_address}_ndvi.png")
        ndvi_img = self.download_image_from_url(result['urls']['ndvi'], ndvi_path)
        
        # Get slope URL and download
        terrain = result['imagery']['terrain']
        region = result['region']
        
        slope_url = self.pipeline.get_image_url(
            terrain,
            region,
            bands=['slope'],
            min_val=0,
            max_val=30
        )
        
        slope_path = os.path.join(output_dir, f"{clean_address}_slope.png")
        slope_img = self.download_image_from_url(slope_url, slope_path)
        print(f"\n✓ All images downloaded to address  {clean_address}/")
        print(f"\n✓ All images downloaded to {output_dir}/")
        
        return {
            'rgb_path': rgb_path,
            'ndvi_path': ndvi_path,
            'slope_path': slope_path,
            'rgb_image': rgb_img,
            'ndvi_image': ndvi_img,
            'slope_image': slope_img,
            'coordinates': result['coordinates'],
            'address': address
        }


if __name__ == "__main__":
    downloader = ImageryDownloader()
    
    # Test address - CHANGE THIS TO YOUR ADDRESS!
    test_address = "2214 Chisin St, San Jose, CA"
    
    print(f"\nDownloading imagery for: {test_address}\n")
    result = downloader.download_for_address(test_address, output_dir="test_data")
    
    if result:
        print("\n✓ SUCCESS!")
        print("\nFiles saved:")
        print(f"  - RGB: {result['rgb_path']}")
        print(f"  - NDVI: {result['ndvi_path']}")
        print(f"  - Slope: {result['slope_path']}")
        print("\nYou can now open these images!")
        print("Next: Install DeepForest for tree detection")
    else:
        print("\n✗ FAILED")