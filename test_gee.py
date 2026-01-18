"""
Test basic Google Earth Engine access
"""

import ee

def test_gee_connection():
    """Test if GEE is working"""
    try:
        ee.Initialize(project='urban-tree-ai')
        print("✓ GEE initialized successfully!")
        
        # Test: Get a simple image
        point = ee.Geometry.Point([-122.084, 37.422])
        
        # Try to access NAIP imagery
        naip = ee.ImageCollection('USDA/NAIP/DOQQ') \
            .filterBounds(point) \
            .first()
        
        if naip:
            print("✓ Successfully accessed NAIP imagery!")
            info = naip.getInfo()
            print(f"✓ Image ID: {info['id']}")
            print(f"✓ Image has {len(info['bands'])} bands")
            return True
        else:
            print("✗ Could not access NAIP imagery")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Google Earth Engine connection...")
    print("=" * 50)
    
    success = test_gee_connection()
    
    if success:
        print("\n" + "=" * 50)
        print("SUCCESS! You're ready to fetch satellite data.")
    else:
        print("\n" + "=" * 50)
        print("FAILED. Check your GEE authentication.")