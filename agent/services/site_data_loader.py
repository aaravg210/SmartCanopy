"""
Planting Site Data Loader
Loads planting site data from database with CV model results
"""

from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import json

from agent.services.plant_database import DatabaseManager, PlantingSite

logger = logging.getLogger(__name__)


class SiteDataLoader:
    """
    Loads and processes planting site data from database

    Planting sites are created by the CV model (PlantingSiteDetector)
    and stored with NDVI, slope, OSM data, and coordinates.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize SiteDataLoader

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    async def get_site_by_id(
        self,
        site_id: str,
        session: Optional[AsyncSession] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Load planting site by ID

        Args:
            site_id: UUID of planting site
            session: Optional database session (creates new if not provided)

        Returns:
            Dict with site data or None if not found
        """
        async def _load(sess: AsyncSession):
            stmt = select(PlantingSite).where(PlantingSite.site_id == site_id)
            result = await sess.execute(stmt)
            site = result.scalar_one_or_none()

            if not site:
                logger.warning(f"Site {site_id} not found in database")
                return None

            return self._format_site_data(site)

        if session:
            return await _load(session)
        else:
            async with self.db_manager.get_session() as sess:
                return await _load(sess)

    async def get_sites_by_analysis(
        self,
        analysis_id: str,
        session: Optional[AsyncSession] = None
    ) -> list[Dict[str, Any]]:
        """
        Load all sites from a CV model analysis

        Args:
            analysis_id: UUID of analysis run
            session: Optional database session

        Returns:
            List of site data dicts
        """
        async def _load(sess: AsyncSession):
            stmt = select(PlantingSite).where(
                PlantingSite.analysis_id == analysis_id
            ).order_by(PlantingSite.suitability_score.desc())
            result = await sess.execute(stmt)
            sites = result.scalars().all()

            return [self._format_site_data(site) for site in sites]

        if session:
            return await _load(session)
        else:
            async with self.db_manager.get_session() as sess:
                return await _load(sess)

    async def get_sites_by_address(
        self,
        address: str,
        session: Optional[AsyncSession] = None
    ) -> list[Dict[str, Any]]:
        """
        Load sites by address

        Args:
            address: Address string
            session: Optional database session

        Returns:
            List of site data dicts sorted by suitability
        """
        async def _load(sess: AsyncSession):
            stmt = select(PlantingSite).where(
                PlantingSite.address.ilike(f'%{address}%')
            ).order_by(PlantingSite.suitability_score.desc())
            result = await sess.execute(stmt)
            sites = result.scalars().all()

            return [self._format_site_data(site) for site in sites]

        if session:
            return await _load(session)
        else:
            async with self.db_manager.get_session() as sess:
                return await _load(sess)

    def _format_site_data(self, site: PlantingSite) -> Dict[str, Any]:
        """
        Format database site record into tool-friendly dict

        Args:
            site: PlantingSite database model

        Returns:
            Formatted site data dict
        """
        # Parse OSM data if it exists
        osm_data = {}
        if site.osm_data:
            if isinstance(site.osm_data, str):
                osm_data = json.loads(site.osm_data)
            else:
                osm_data = site.osm_data

        # Parse location pixels
        location_pixels = None
        if site.location_pixels:
            if isinstance(site.location_pixels, str):
                location_pixels = json.loads(site.location_pixels)
            else:
                location_pixels = site.location_pixels

        # Calculate area in square feet from pixels
        # Image is 512x512 pixels covering 200m x 200m (buffer_m=100 default)
        # 1 pixel = 0.39m x 0.39m = 0.152 m² = 1.64 sq ft
        area_sq_ft = None
        if site.area_pixels:
            default_buffer_m = 100
            image_size_px = 512
            meters_per_pixel = (2 * default_buffer_m) / image_size_px
            sq_feet_per_pixel = (meters_per_pixel ** 2) * 10.76
            area_sq_ft = int(site.area_pixels * sq_feet_per_pixel)

        # Categorize NDVI
        ndvi_category = self._categorize_ndvi(site.avg_ndvi)

        # Categorize slope
        slope_category = self._categorize_slope(site.avg_slope)

        return {
            'site_id': str(site.site_id),
            'analysis_id': str(site.analysis_id),
            'address': site.address,
            'latitude': site.latitude,
            'longitude': site.longitude,
            'location_pixels': location_pixels,

            # Vegetation and terrain
            'avg_ndvi': round(site.avg_ndvi, 3) if site.avg_ndvi else None,
            'ndvi_category': ndvi_category,
            'avg_slope': round(site.avg_slope, 2) if site.avg_slope else None,
            'slope_category': slope_category,

            # Area
            'area_pixels': site.area_pixels,
            'area_sq_ft': area_sq_ft,

            # Suitability
            'suitability_score': round(site.suitability_score, 3) if site.suitability_score else None,

            # Infrastructure
            'osm_data': osm_data,
            'has_nearby_roads': self._check_osm_feature(osm_data, 'roads'),
            'has_nearby_buildings': self._check_osm_feature(osm_data, 'buildings'),
            'has_nearby_parking': self._check_osm_feature(osm_data, 'parking'),

            # Images
            'rgb_image_path': site.rgb_image_path,

            # Metadata
            'created_at': site.created_at.isoformat() if site.created_at else None
        }

    def _categorize_ndvi(self, ndvi: Optional[float]) -> str:
        """
        Categorize NDVI value

        Args:
            ndvi: NDVI value (-1 to 1)

        Returns:
            Category string
        """
        if ndvi is None:
            return 'unknown'
        elif ndvi < 0.1:
            return 'bare_soil_or_pavement'
        elif ndvi < 0.3:
            return 'sparse_vegetation'
        elif ndvi < 0.6:
            return 'moderate_vegetation'
        else:
            return 'dense_vegetation'

    def _categorize_slope(self, slope: Optional[float]) -> str:
        """
        Categorize slope value

        Args:
            slope: Slope in degrees

        Returns:
            Category string
        """
        if slope is None:
            return 'unknown'
        elif slope < 5:
            return 'flat'
        elif slope < 10:
            return 'gentle'
        elif slope < 15:
            return 'moderate'
        else:
            return 'steep'

    def _check_osm_feature(self, osm_data: Dict, feature_type: str) -> bool:
        """
        Check if OSM data contains specific feature type

        Args:
            osm_data: OSM data dict
            feature_type: Type of feature ('roads', 'buildings', 'parking')

        Returns:
            True if feature exists nearby
        """
        if not osm_data:
            return False

        features = osm_data.get(feature_type, [])
        return len(features) > 0 if isinstance(features, list) else bool(features)

    def calculate_recommended_tree_size(self, site_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate recommended tree size based on available area

        Args:
            site_data: Site data dict from _format_site_data

        Returns:
            Dict with 'max_height_ft', 'max_spread_ft', 'size_category'
        """
        area_sq_ft = site_data.get('area_sq_ft')

        if not area_sq_ft:
            return {
                'max_height_ft': 40,
                'max_spread_ft': 30,
                'size_category': 'medium',
                'note': 'Area unknown - recommending medium size'
            }

        # Calculate based on area (assuming circular crown)
        # Area = π * (spread/2)²
        # Max spread = 2 * sqrt(area / π)
        import math
        max_spread_ft = int(2 * math.sqrt(area_sq_ft / math.pi))

        # Height roughly proportional to spread (typical tree ratio 1.3:1)
        max_height_ft = int(max_spread_ft * 1.3)

        # Categorize size
        if max_height_ft < 25:
            size_category = 'small'
        elif max_height_ft < 45:
            size_category = 'medium'
        else:
            size_category = 'large'

        return {
            'max_height_ft': max_height_ft,
            'max_spread_ft': max_spread_ft,
            'size_category': size_category,
            'area_sq_ft': area_sq_ft
        }


# Helper function for creating loader
def create_site_loader(database_url: str) -> SiteDataLoader:
    """
    Create SiteDataLoader instance

    Args:
        database_url: Database connection URL

    Returns:
        Configured SiteDataLoader
    """
    db_manager = DatabaseManager(database_url)
    return SiteDataLoader(db_manager)
