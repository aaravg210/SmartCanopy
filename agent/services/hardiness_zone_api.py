"""
USDA Hardiness Zone API integration
Fetches hardiness zone data by ZIP code
"""

import httpx
from typing import Optional, Dict, Any
import logging

from agent.config import settings
from agent.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class HardinessZoneAPI:
    """
    Wrapper for USDA Hardiness Zone API

    Provides ZIP code to hardiness zone lookups with caching.
    Falls back to static mapping if API unavailable.
    """

    # Fallback static ZIP → Zone mapping for common areas
    # This is a subset - expand as needed
    STATIC_ZIP_ZONES = {
        # California
        '94102': '10b', '94103': '10b', '95123': '10a',  # San Francisco, San Jose
        '90210': '10a', '90001': '10a',  # Los Angeles
        '92101': '10b',  # San Diego

        # New York
        '10001': '7b', '10002': '7b', '11201': '7b',  # NYC
        '14201': '6b',  # Buffalo

        # Texas
        '75201': '8a', '77001': '9a', '78701': '8b',  # Dallas, Houston, Austin

        # Florida
        '33101': '11a', '32801': '9b',  # Miami, Orlando

        # Illinois
        '60601': '6a',  # Chicago

        # Washington
        '98101': '9a',  # Seattle

        # Add more as needed...
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_service: Optional[CacheService] = None
    ):
        """
        Initialize Hardiness Zone API client

        Args:
            api_key: API key for USDA Hardiness Zone API (optional)
            cache_service: Cache service for storing results
        """
        self.api_key = api_key or settings.usda_hardiness_api_key
        self.cache_service = cache_service
        self.base_url = "https://phzmapi.org"  # Public Hardiness Zone API

    async def get_zone_by_zip(
        self,
        zip_code: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get hardiness zone for a ZIP code

        Args:
            zip_code: 5-digit US ZIP code
            use_cache: Whether to use cached results

        Returns:
            Dict with 'zone' (str), 'zone_numeric' (int), 'temperature_range' (str)

        Example:
            {
                'zone': '9b',
                'zone_numeric': 9,
                'temperature_range': '25 to 30 °F'
            }
        """
        # Validate ZIP code
        if not zip_code or len(zip_code) != 5 or not zip_code.isdigit():
            raise ValueError(f"Invalid ZIP code: {zip_code}. Must be 5 digits.")

        # Check cache
        if use_cache and self.cache_service:
            cache_key = f"hardiness_zone:{zip_code}"
            cached = await self.cache_service.get(cache_key)
            if cached:
                logger.debug(f"Hardiness zone for {zip_code} found in cache")
                return cached

        # Try API first
        try:
            result = await self._fetch_from_api(zip_code)
            if result:
                # Cache result (30 days TTL)
                if self.cache_service:
                    cache_key = f"hardiness_zone:{zip_code}"
                    await self.cache_service.set(
                        cache_key,
                        result,
                        ttl=settings.cache_ttl_hardiness_zone
                    )
                return result
        except Exception as e:
            logger.warning(f"API fetch failed for {zip_code}: {e}")

        # Fallback to static mapping
        logger.info(f"Using static mapping for ZIP {zip_code}")
        return self._get_from_static_map(zip_code)

    async def _fetch_from_api(self, zip_code: str) -> Optional[Dict[str, Any]]:
        """
        Fetch hardiness zone from API

        Args:
            zip_code: 5-digit ZIP code

        Returns:
            Zone data dict or None if unavailable
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Public Hardiness Zone API endpoint
                url = f"{self.base_url}/{zip_code}.json"
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()

                    # Parse response
                    zone = data.get('zone', '')
                    if zone:
                        return self._parse_zone_data(zone)

                elif response.status_code == 404:
                    logger.warning(f"ZIP code {zip_code} not found in API")
                    return None
                else:
                    logger.error(
                        f"API error: {response.status_code} - {response.text}"
                    )
                    return None

        except httpx.TimeoutException:
            logger.error(f"API timeout for ZIP {zip_code}")
            return None
        except Exception as e:
            logger.error(f"API error for ZIP {zip_code}: {e}")
            return None

    def _get_from_static_map(self, zip_code: str) -> Dict[str, Any]:
        """
        Get zone from static mapping

        Args:
            zip_code: 5-digit ZIP code

        Returns:
            Zone data dict

        Raises:
            ValueError: If ZIP code not in static map
        """
        # Check exact match
        if zip_code in self.STATIC_ZIP_ZONES:
            zone = self.STATIC_ZIP_ZONES[zip_code]
            return self._parse_zone_data(zone)

        # Try to infer from regional patterns (rough approximation)
        # This is NOT accurate - just a fallback
        first_digit = zip_code[0]
        regional_zones = {
            '0': '5b',  # Northeast (MA, CT, etc.)
            '1': '6a',  # Northeast (NY, PA, etc.)
            '2': '7a',  # Mid-Atlantic (DC, VA, etc.)
            '3': '7b',  # Southeast (FL, GA, etc.)
            '4': '6b',  # Midwest (IN, OH, etc.)
            '5': '5a',  # North Central (MN, ND, etc.)
            '6': '6a',  # Central (IL, MO, etc.)
            '7': '7b',  # South (TX, AR, etc.)
            '8': '8a',  # Southwest (AZ, NM, etc.)
            '9': '9a',  # West Coast (CA, OR, WA, etc.)
        }

        if first_digit in regional_zones:
            zone = regional_zones[first_digit]
            logger.warning(
                f"Using regional approximation for ZIP {zip_code}: {zone}. "
                "This may be inaccurate - recommend manual verification."
            )
            return self._parse_zone_data(zone)

        # No data available
        raise ValueError(
            f"Hardiness zone not available for ZIP {zip_code}. "
            "Please provide zone manually or try a nearby ZIP code."
        )

    def _parse_zone_data(self, zone: str) -> Dict[str, Any]:
        """
        Parse zone string into structured data

        Args:
            zone: Zone string like '9b' or '10a'

        Returns:
            Dict with zone, zone_numeric, temperature_range
        """
        # Extract numeric part
        zone_numeric = int(''.join(c for c in zone if c.isdigit()))

        # Map zones to temperature ranges (USDA standard)
        temperature_ranges = {
            1: '-60 to -50 °F',
            2: '-50 to -40 °F',
            3: '-40 to -30 °F',
            4: '-30 to -20 °F',
            5: '-20 to -10 °F',
            6: '-10 to 0 °F',
            7: '0 to 10 °F',
            8: '10 to 20 °F',
            9: '20 to 30 °F',
            10: '30 to 40 °F',
            11: '40 to 50 °F',
            12: '50 to 60 °F',
            13: '60 to 70 °F'
        }

        # Refine based on a/b suffix
        if 'a' in zone.lower():
            temp_range = temperature_ranges.get(zone_numeric, 'Unknown')
            # 'a' is the colder half
            if zone_numeric in temperature_ranges:
                low = zone_numeric * 10 - 60
                high = low + 5
                temp_range = f"{low} to {high} °F"
        elif 'b' in zone.lower():
            temp_range = temperature_ranges.get(zone_numeric, 'Unknown')
            # 'b' is the warmer half
            if zone_numeric in temperature_ranges:
                low = zone_numeric * 10 - 55
                high = low + 5
                temp_range = f"{low} to {high} °F"
        else:
            temp_range = temperature_ranges.get(zone_numeric, 'Unknown')

        return {
            'zone': zone,
            'zone_numeric': zone_numeric,
            'temperature_range': temp_range
        }

    def add_static_mapping(self, zip_code: str, zone: str):
        """
        Add a ZIP code to the static mapping

        Useful for adding known zones during development

        Args:
            zip_code: 5-digit ZIP code
            zone: Hardiness zone (e.g., '9b')
        """
        if len(zip_code) == 5 and zip_code.isdigit():
            self.STATIC_ZIP_ZONES[zip_code] = zone
            logger.info(f"Added static mapping: {zip_code} → {zone}")
        else:
            raise ValueError(f"Invalid ZIP code: {zip_code}")


# Singleton instance
_hardiness_api: Optional[HardinessZoneAPI] = None


def get_hardiness_api(cache_service: Optional[CacheService] = None) -> HardinessZoneAPI:
    """Get singleton HardinessZoneAPI instance"""
    global _hardiness_api
    if _hardiness_api is None:
        _hardiness_api = HardinessZoneAPI(cache_service=cache_service)
    return _hardiness_api
