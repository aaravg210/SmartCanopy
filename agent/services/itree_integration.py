"""
i-Tree Species Database Integration
Fetches environmental benefits data for tree species
"""

import httpx
from typing import Optional, Dict, Any
import logging

from agent.services.cache_service import CacheService
from agent.config import settings

logger = logging.getLogger(__name__)


class ITreeAPI:
    """
    Wrapper for i-Tree Species Database API

    Provides environmental benefits data (CO2, air quality, stormwater, energy)
    with fallback to database values if API unavailable.
    """

    def __init__(self, cache_service: Optional[CacheService] = None):
        """
        Initialize i-Tree API client

        Args:
            cache_service: Cache service for storing results
        """
        self.cache_service = cache_service
        self.base_url = "https://species.itreetools.org/api"

    async def get_species_benefits(
        self,
        species_id: str,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get environmental benefits for a species

        Args:
            species_id: Species identifier (e.g., 'PLOC' for Platanus occidentalis)
            use_cache: Whether to use cached results

        Returns:
            Dict with environmental benefits or None if unavailable

        Example:
            {
                'co2_sequestration_kg_year': 195.0,
                'air_pollution_removal_kg_year': 4.8,
                'stormwater_gallons_year': 1250,
                'energy_savings_kwh_year': 58,
                'avoided_runoff_value_usd': 38,
                'pollution_removal_value_usd': 24
            }
        """
        # Check cache
        if use_cache and self.cache_service:
            cache_key = f"itree_benefits:{species_id}"
            cached = await self.cache_service.get(cache_key)
            if cached:
                logger.debug(f"i-Tree data for {species_id} found in cache")
                return cached

        # Try API
        try:
            result = await self._fetch_from_api(species_id)
            if result:
                # Cache result (7 days TTL)
                if self.cache_service:
                    cache_key = f"itree_benefits:{species_id}"
                    await self.cache_service.set(
                        cache_key,
                        result,
                        ttl=settings.cache_ttl_environmental
                    )
                return result
        except Exception as e:
            logger.warning(f"i-Tree API fetch failed for {species_id}: {e}")

        return None

    async def _fetch_from_api(self, species_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch species benefits from i-Tree API

        Args:
            species_id: Species identifier

        Returns:
            Benefits dict or None if unavailable
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # i-Tree API endpoint
                url = f"{self.base_url}/species/{species_id}"
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()

                    # Parse benefits from response
                    # Note: Actual i-Tree API structure may vary
                    # This is a representative structure
                    benefits = data.get('benefits', {})

                    return {
                        'co2_sequestration_kg_year': benefits.get('co2_sequestration'),
                        'air_pollution_removal_kg_year': benefits.get('pollution_removal'),
                        'stormwater_gallons_year': benefits.get('stormwater_interception'),
                        'energy_savings_kwh_year': benefits.get('energy_savings'),
                        'avoided_runoff_value_usd': benefits.get('runoff_value'),
                        'pollution_removal_value_usd': benefits.get('pollution_value')
                    }

                elif response.status_code == 404:
                    logger.warning(f"Species {species_id} not found in i-Tree database")
                    return None
                else:
                    logger.error(
                        f"i-Tree API error: {response.status_code} - {response.text}"
                    )
                    return None

        except httpx.TimeoutException:
            logger.error(f"i-Tree API timeout for species {species_id}")
            return None
        except Exception as e:
            logger.error(f"i-Tree API error for species {species_id}: {e}")
            return None

    def estimate_benefits_from_size(
        self,
        base_benefits: Dict[str, float],
        tree_height_ft: float,
        mature_height_ft: float
    ) -> Dict[str, float]:
        """
        Estimate current benefits based on tree size

        Environmental benefits scale with tree size. Young trees
        provide less benefit than mature trees.

        Args:
            base_benefits: Benefits at mature size
            tree_height_ft: Current tree height
            mature_height_ft: Mature tree height

        Returns:
            Scaled benefits dict
        """
        # Calculate size ratio (0 to 1)
        size_ratio = min(tree_height_ft / mature_height_ft, 1.0)

        # Benefits scale roughly with crown volume (height^2 approximation)
        # Young trees: 10% of mature benefits
        # Juvenile trees: Linear ramp to 80%
        # Mature trees: 80-100%

        if size_ratio < 0.15:  # Sapling/young
            scale_factor = 0.10
        elif size_ratio < 0.6:  # Juvenile
            # Linear interpolation from 10% to 80%
            scale_factor = 0.10 + (size_ratio - 0.15) * (0.70 / 0.45)
        else:  # Approaching mature
            # Linear interpolation from 80% to 100%
            scale_factor = 0.80 + (size_ratio - 0.6) * (0.20 / 0.4)

        # Apply scaling
        return {
            'co2_sequestration_kg_year': base_benefits.get('co2_sequestration_kg_year', 0) * scale_factor,
            'air_pollution_removal_kg_year': base_benefits.get('air_pollution_removal_kg_year', 0) * scale_factor,
            'stormwater_gallons_year': base_benefits.get('stormwater_gallons_year', 0) * scale_factor,
            'energy_savings_kwh_year': base_benefits.get('energy_savings_kwh_year', 0) * scale_factor,
            'scale_factor': round(scale_factor, 2),
            'tree_maturity': 'young' if size_ratio < 0.15 else 'juvenile' if size_ratio < 0.6 else 'mature'
        }

    def calculate_dollar_value(
        self,
        benefits: Dict[str, float],
        years: int = 1
    ) -> Dict[str, Any]:
        """
        Convert environmental benefits to dollar values

        Args:
            benefits: Benefits dict with kg/year and gallons/year values
            years: Number of years to calculate for

        Returns:
            Dict with dollar values and totals
        """
        # Pricing (2024 estimates)
        CO2_PRICE_PER_TON = 51.0  # EPA social cost of carbon
        POLLUTION_PRICE_PER_KG = 5.0  # Air quality value
        STORMWATER_PRICE_PER_GALLON = 0.03  # Utility cost
        ENERGY_PRICE_PER_KWH = 0.15  # Average electricity rate

        # Annual benefits
        co2_kg = benefits.get('co2_sequestration_kg_year', 0)
        pollution_kg = benefits.get('air_pollution_removal_kg_year', 0)
        stormwater_gal = benefits.get('stormwater_gallons_year', 0)
        energy_kwh = benefits.get('energy_savings_kwh_year', 0)

        # Calculate annual dollar values
        co2_value = (co2_kg / 1000) * CO2_PRICE_PER_TON  # Convert kg to tons
        pollution_value = pollution_kg * POLLUTION_PRICE_PER_KG
        stormwater_value = stormwater_gal * STORMWATER_PRICE_PER_GALLON
        energy_value = energy_kwh * ENERGY_PRICE_PER_KWH

        annual_total = co2_value + pollution_value + stormwater_value + energy_value
        lifetime_total = annual_total * years

        return {
            'annual': {
                'co2_value_usd': round(co2_value, 2),
                'air_quality_value_usd': round(pollution_value, 2),
                'stormwater_value_usd': round(stormwater_value, 2),
                'energy_value_usd': round(energy_value, 2),
                'total_usd': round(annual_total, 2)
            },
            'lifetime': {
                'years': years,
                'total_usd': round(lifetime_total, 2)
            },
            'pricing_assumptions': {
                'co2_per_ton': CO2_PRICE_PER_TON,
                'pollution_per_kg': POLLUTION_PRICE_PER_KG,
                'stormwater_per_gallon': STORMWATER_PRICE_PER_GALLON,
                'energy_per_kwh': ENERGY_PRICE_PER_KWH
            }
        }

    def generate_equivalent_metrics(
        self,
        benefits: Dict[str, float],
        years: int = 1
    ) -> Dict[str, str]:
        """
        Generate relatable equivalent metrics

        Args:
            benefits: Benefits dict
            years: Number of years

        Returns:
            Dict with equivalent metrics as human-readable strings
        """
        co2_kg_total = benefits.get('co2_sequestration_kg_year', 0) * years

        # Equivalents
        # Average car: 4.6 metric tons CO2/year = 4,600 kg/year
        # Average car: 12,000 miles/year
        car_free_days = (co2_kg_total / 4600) * 365
        miles_not_driven = (co2_kg_total / 4600) * 12000

        # Average tree sequesters ~21 kg CO2/year
        equivalent_trees = co2_kg_total / 21 / years

        # Stormwater
        stormwater_total = benefits.get('stormwater_gallons_year', 0) * years
        # Average bathtub: 40 gallons
        bathtubs = stormwater_total / 40

        return {
            'car_free_days': f"{int(car_free_days)} days of car-free driving",
            'miles_not_driven': f"{int(miles_not_driven):,} miles not driven",
            'equivalent_trees': f"{int(equivalent_trees)} average trees",
            'bathtubs_of_water': f"{int(bathtubs)} bathtubs of stormwater managed"
        }


# Singleton instance
_itree_api: Optional[ITreeAPI] = None


def get_itree_api(cache_service: Optional[CacheService] = None) -> ITreeAPI:
    """Get singleton ITreeAPI instance"""
    global _itree_api
    if _itree_api is None:
        _itree_api = ITreeAPI(cache_service=cache_service)
    return _itree_api
