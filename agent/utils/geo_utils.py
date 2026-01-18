"""
Geographic utilities for coordinate transformations and distance calculations
"""

import math
from typing import Tuple, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate distance between two lat/lon points using Haversine formula

    Args:
        lat1, lon1: First point coordinates (degrees)
        lat2, lon2: Second point coordinates (degrees)

    Returns:
        Distance in feet
    """
    # Earth radius in feet
    R = 20902231  # ~3,959 miles

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    # Haversine formula
    a = (
        math.sin(delta_lat / 2) ** 2 +
        math.cos(lat1_rad) * math.cos(lat2_rad) *
        math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def pixels_to_feet(
    pixels: int,
    resolution_m: float = 1.0
) -> float:
    """
    Convert pixel area to square feet

    Args:
        pixels: Number of pixels
        resolution_m: Image resolution in meters per pixel (NAIP is typically 1m)

    Returns:
        Area in square feet
    """
    # 1 meter = 3.28084 feet
    meters_per_pixel = resolution_m
    feet_per_pixel = meters_per_pixel * 3.28084

    # Area conversion
    sq_ft = pixels * (feet_per_pixel ** 2)
    return sq_ft


def feet_to_pixels(
    feet: float,
    resolution_m: float = 1.0
) -> int:
    """
    Convert square feet to pixel area

    Args:
        feet: Area in square feet
        resolution_m: Image resolution in meters per pixel

    Returns:
        Number of pixels
    """
    # Reverse of pixels_to_feet
    feet_per_pixel = resolution_m * 3.28084
    pixels = feet / (feet_per_pixel ** 2)
    return int(pixels)


def calculate_tree_footprint_area(
    mature_spread_ft: float
) -> float:
    """
    Calculate circular footprint area of tree crown

    Args:
        mature_spread_ft: Mature tree spread/width in feet

    Returns:
        Area in square feet
    """
    radius_ft = mature_spread_ft / 2
    area = math.pi * (radius_ft ** 2)
    return area


def check_clearance(
    tree_lat: float,
    tree_lon: float,
    feature_lat: float,
    feature_lon: float,
    mature_spread_ft: float,
    required_clearance_ft: float
) -> Dict[str, Any]:
    """
    Check if tree has adequate clearance from a feature

    Args:
        tree_lat, tree_lon: Tree location coordinates
        feature_lat, feature_lon: Feature location coordinates
        mature_spread_ft: Mature tree spread in feet
        required_clearance_ft: Required clearance distance in feet

    Returns:
        Dict with 'has_clearance' (bool), 'actual_distance_ft' (float),
        'required_distance_ft' (float)
    """
    # Calculate distance between tree center and feature
    distance_ft = haversine_distance(tree_lat, tree_lon, feature_lat, feature_lon)

    # Account for tree spread - need clearance from edge of canopy
    tree_radius_ft = mature_spread_ft / 2
    actual_clearance_ft = distance_ft - tree_radius_ft

    # Required distance is clearance + tree radius
    required_distance_ft = required_clearance_ft + tree_radius_ft

    return {
        'has_clearance': actual_clearance_ft >= required_clearance_ft,
        'actual_distance_ft': round(actual_clearance_ft, 1),
        'required_clearance_ft': required_clearance_ft,
        'distance_from_center_ft': round(distance_ft, 1),
        'tree_radius_ft': round(tree_radius_ft, 1)
    }


def get_cardinal_direction(bearing: float) -> str:
    """
    Convert bearing angle to cardinal direction

    Args:
        bearing: Bearing in degrees (0-360)

    Returns:
        Cardinal direction string (N, NE, E, SE, S, SW, W, NW)
    """
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    index = int((bearing + 22.5) / 45) % 8
    return directions[index]


def calculate_bearing(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate bearing from point 1 to point 2

    Args:
        lat1, lon1: Starting point coordinates (degrees)
        lat2, lon2: Ending point coordinates (degrees)

    Returns:
        Bearing in degrees (0-360)
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)

    # Calculate bearing
    x = math.sin(delta_lon) * math.cos(lat2_rad)
    y = (
        math.cos(lat1_rad) * math.sin(lat2_rad) -
        math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
    )

    bearing_rad = math.atan2(x, y)
    bearing_deg = math.degrees(bearing_rad)

    # Normalize to 0-360
    return (bearing_deg + 360) % 360


def estimate_sunlight_from_ndvi(
    ndvi: float,
    surrounding_ndvi: List[float]
) -> str:
    """
    Estimate sunlight exposure based on NDVI values

    Args:
        ndvi: Site NDVI value
        surrounding_ndvi: NDVI values of surrounding area

    Returns:
        Sunlight category: 'full_sun', 'partial_shade', or 'full_shade'
    """
    # Higher surrounding NDVI suggests shade from nearby vegetation
    avg_surrounding = sum(surrounding_ndvi) / len(surrounding_ndvi) if surrounding_ndvi else ndvi

    # If site NDVI significantly lower than surroundings, likely shaded
    ndvi_diff = ndvi - avg_surrounding

    if ndvi_diff < -0.15:
        return 'full_shade'
    elif ndvi_diff < -0.05:
        return 'partial_shade'
    else:
        # Also consider absolute NDVI
        if ndvi > 0.5:
            return 'partial_shade'  # Dense vegetation suggests some shade
        else:
            return 'full_sun'


def slope_to_category(slope_degrees: float) -> Dict[str, Any]:
    """
    Categorize slope and provide planting considerations

    Args:
        slope_degrees: Slope in degrees

    Returns:
        Dict with 'category', 'difficulty', 'considerations'
    """
    if slope_degrees < 5:
        return {
            'category': 'flat',
            'difficulty': 'easy',
            'considerations': ['Standard planting techniques', 'Good water drainage']
        }
    elif slope_degrees < 10:
        return {
            'category': 'gentle',
            'difficulty': 'moderate',
            'considerations': ['Plant on contour', 'Mulch to prevent erosion']
        }
    elif slope_degrees < 15:
        return {
            'category': 'moderate',
            'difficulty': 'challenging',
            'considerations': [
                'Plant on contour to prevent runoff',
                'Create terrace or berm',
                'Heavy mulching required',
                'Consider erosion control plants'
            ]
        }
    else:
        return {
            'category': 'steep',
            'difficulty': 'very challenging',
            'considerations': [
                'Professional assessment recommended',
                'May require terracing',
                'Erosion control critical',
                'Consider ground cover instead of trees',
                'Staking essential'
            ]
        }


def ndvi_to_soil_moisture_estimate(ndvi: float) -> str:
    """
    Estimate soil moisture level from NDVI

    Args:
        ndvi: NDVI value

    Returns:
        Moisture category: 'dry', 'medium', or 'wet'
    """
    if ndvi < 0.2:
        return 'dry'
    elif ndvi < 0.5:
        return 'medium'
    else:
        return 'wet'


def calculate_planting_density(
    area_sq_ft: float,
    mature_spread_ft: float,
    spacing_multiplier: float = 1.5
) -> Dict[str, Any]:
    """
    Calculate how many trees can fit in an area

    Args:
        area_sq_ft: Available area in square feet
        mature_spread_ft: Mature tree spread in feet
        spacing_multiplier: Spacing factor (1.0 = touching, 1.5 = comfortable)

    Returns:
        Dict with 'max_trees', 'spacing_ft', 'total_crown_area_sq_ft'
    """
    # Effective spread with spacing
    effective_spread_ft = mature_spread_ft * spacing_multiplier

    # Area per tree (circular)
    area_per_tree = math.pi * (effective_spread_ft / 2) ** 2

    # Maximum number of trees
    max_trees = int(area_sq_ft / area_per_tree)

    # Actual spacing between tree centers
    spacing_ft = effective_spread_ft

    # Total crown area at maturity
    crown_area_per_tree = math.pi * (mature_spread_ft / 2) ** 2
    total_crown_area = max_trees * crown_area_per_tree

    return {
        'max_trees': max(1, max_trees),  # At least 1
        'spacing_ft': round(spacing_ft, 1),
        'total_crown_area_sq_ft': round(total_crown_area, 1),
        'coverage_percent': round((total_crown_area / area_sq_ft) * 100, 1)
    }
