"""
Planting Site Detection Algorithm
Combines DeepForest, NDVI, and slope to identify optimal tree planting locations
"""

from test_deepforest import DeepForestDetector
from download_imagery import ImageryDownloader
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from osm_filter import OSMFilter


class PlantingSiteDetector:
    """Identifies optimal tree planting locations"""
    
    def __init__(self):
        self.tree_detector = DeepForestDetector()
        self.image_downloader = ImageryDownloader()
        self.osm_filter = OSMFilter()
    
    def analyze_address(self, address: str, buffer_m: int = 100):
        """
        Complete analysis pipeline for an address
        
        Returns planting site recommendations
        """
        
        print("\n" + "="*60)
        print(f"ANALYZING: {address}")
        print("="*60 + "\n")
        
        # Step 1: Download imagery
        print("Step 1/7: Downloading satellite imagery...")
        result = self.image_downloader.download_for_address(
            address,
            output_dir="analysis_data",
            buffer_m=buffer_m
        )
        print("image_downloader Result:",result)
        if not result:
            print("✗ Failed to download imagery")
            return None
        
        # Step 2: Detect existing trees
        print("\nStep 2/7: Detecting existing trees...")
        tree_predictions = self.tree_detector.predict_trees(result['rgb_path'])
        
        # Step 3: Load and process 
        # NDVI
        print("\nStep 3/7: Analyzing vegetation coverage...")
        ndvi_img = np.array(Image.open(result['ndvi_path']).convert('L'))  # Grayscale
        ndvi_normalized = ndvi_img / 255.0  # Scale to 0-1
        
        # Step 4: Load and process slope
        print("\nStep 4/7: Analyzing terrain...")
        slope_img = np.array(Image.open(result['slope_path']).convert('L'))
        slope_normalized = slope_img / 255.0 * 30  # Scale to 0-30 degrees
        
        # Step 5: Identify planting sites
        print("\nStep 5/7: Identifying planting opportunities...")
        planting_sites = self.find_planting_sites(
            tree_predictions,
            ndvi_normalized,
            slope_normalized,
            result['rgb_path']
        )
        # NEW Step 6: Get OSM data (osm stuff)
        print("\nStep 6/7: Fetching OpenStreetMap data...")
        osm_data = self.osm_filter.get_infrastructure_data(
            result['coordinates'][0],  # lat
            result['coordinates'][1],  # lon
            buffer_m=buffer_m
        )
    
        # NEW Step 7: Create exclusion mask (osm stuff) 
        print("\nStep 7/7: Applying infrastructure filters...")
        img = Image.open(result['rgb_path'])
        exclusion_mask = self.osm_filter.create_exclusion_mask(
            osm_data,
            result['coordinates'][0],  # lat
            result['coordinates'][1],  # lon
            img.width,
            img.height,
            buffer_m=buffer_m
        )
        # Filter planting sites
        filtered_sites = self.osm_filter.filter_planting_sites(
            planting_sites,
            exclusion_mask
    
        )
        
        # Generate report
        self.generate_report(address, tree_predictions, filtered_sites)

        return {
        'address': address,
        'existing_trees': len(tree_predictions) if tree_predictions is not None else 0,
        'planting_sites': filtered_sites,  # Filtered!
        'imagery': result,
        'osm_data': osm_data,
        'exclusion_mask': exclusion_mask
        }



    
    def find_planting_sites(self, tree_predictions, ndvi, slope, rgb_path):
        """Identify suitable locations with texture analysis"""
        
        # Load RGB for texture analysis
        rgb_img = np.array(Image.open(rgb_path))
        gray = np.mean(rgb_img, axis=2)
                
        # Create tree mask
        tree_mask = np.zeros(ndvi.shape, dtype=bool)
        height, width = ndvi.shape
        if tree_predictions is not None and len(tree_predictions) > 0:
            for _, tree in tree_predictions.iterrows():
                xmin = max(0, int(tree['xmin']))
                ymin = max(0, int(tree['ymin']))
                xmax = min(width, int(tree['xmax']))
                ymax = min(height, int(tree['ymax']))
                tree_mask[ymin:ymax, xmin:xmax] = True
        
        # Resize slope if needed
        if slope.shape != ndvi.shape:
            from PIL import Image as PILImage
            slope_img = PILImage.fromarray((slope * 255).astype(np.uint8))
            slope_img = slope_img.resize((ndvi.shape[1], ndvi.shape[0]), PILImage.BILINEAR)
            slope = np.array(slope_img) / 255.0 * 30
                
        # IMPROVED CRITERIA
        suitable = (
            (ndvi > 0.15) &           # Removes things like pavement
            (ndvi < 0.65) &           # Not dense forest
            (slope < 15) &            # Flat enough
            (~tree_mask)              # No existing tree
        )
        
        # Find contiguous regions
        from scipy import ndimage
        labeled, num_features = ndimage.label(suitable)
        
        planting_sites = []
        for i in range(1, num_features + 1):
            site_mask = (labeled == i)
            area = np.sum(site_mask)
            
            # Minimum area threshold (e.g., 100 pixels)
            if area > 100:
                # Get centroid
                positions = np.where(site_mask)
                center_y = int(np.mean(positions[0]))
                center_x = int(np.mean(positions[1]))
                
                # Calculate average NDVI and slope for this site
                avg_ndvi = float(np.mean(ndvi[site_mask]))
                avg_slope = float(np.mean(slope[site_mask]))
                
                # Suitability score (0-1)
                # Higher NDVI is better (more vegetation)
                # Lower slope is better (easier to plant)
                suitability = (avg_ndvi * 0.7) + ((1 - avg_slope/30) * 0.3)
                
                planting_sites.append({
                    'location': (center_x, center_y),
                    'area_pixels': int(area),
                    'avg_ndvi': avg_ndvi,
                    'avg_slope': avg_slope,
                    'suitability_score': suitability
                })
        
        # Sort by suitability score
        planting_sites.sort(key=lambda x: x['suitability_score'], reverse=True)
        
        print(f"✓ Identified {len(planting_sites)} potential planting sites")
        
        return planting_sites
    
    def generate_report(self, address, tree_predictions, planting_sites):
        """Print summary report"""
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        
        num_trees = len(tree_predictions) if tree_predictions is not None else 0
        print(f"\n📍 Location: {address}")
        print(f"🌳 Existing trees detected: {num_trees}")
        print(f"🌱 Suitable planting sites found: {len(planting_sites)}")
        
        if len(planting_sites) > 0:
            print(f"\n🏆 TOP 5 RECOMMENDED SITES:")
            for i, site in enumerate(planting_sites[:5], 1):
                print(f"\n  Site {i}:")
                print(f"    Location: {site['location']}")
                print(f"    Area: {site['area_pixels']} pixels")
                print(f"    Vegetation health (NDVI): {site['avg_ndvi']:.2f}")
                print(f"    Slope: {site['avg_slope']:.1f}°")
                print(f"    Suitability: {site['suitability_score']:.2%}")
        
        print("\n" + "="*60 + "\n")


    def visualize_with_osm(self, rgb_path, exclusion_mask, planting_sites):
    
        img = Image.open(rgb_path)
        
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
        
        # Original
        ax1.imshow(img)
        ax1.set_title('Original Image')
        ax1.axis('off')
        
        # Exclusion mask overlay
        ax2.imshow(img)
        # Show excluded areas in red transparent overlay
        masked = np.zeros((*exclusion_mask.shape, 4))
        masked[exclusion_mask] = [1, 0, 0, 0.5]  # Red, 50% transparent
        ax2.imshow(masked)
        ax2.set_title('Excluded Areas (Roads/Buildings)')
        ax2.axis('off')
        
        # Final planting sites
        ax3.imshow(img)
        ax3.imshow(masked)  # Show exclusions
        for site in planting_sites:
            x, y = site['location']
            ax3.plot(x, y, 'go', markersize=10)  # Green dots
            ax3.text(x, y, f"{site['suitability_score']:.0%}", 
                    color='white', fontsize=8, ha='center')
        ax3.set_title(f'Final Planting Sites ({len(planting_sites)})')
        ax3.axis('off')
        
        plt.tight_layout()
        plt.savefig('analysis_data/osm_filtering_result.png', dpi=150)
        plt.show()
        
        print("✓ Visualization saved to analysis_data/osm_filtering_result.png")


if __name__ == "__main__":
    detector = PlantingSiteDetector()
    
    # Test address
    test_address = "2214 Chisin St, San Jose, CA"
    
    result = detector.analyze_address(test_address, buffer_m=100)
    
    if result:
        print("✓ SUCCESS! Planting site detection is working!")
        detector.visualize_with_osm(
        result['imagery']['rgb_path'],
        result['exclusion_mask'],
        result['planting_sites']
        )

    else:
        print("✗ Analysis failed")

