"""
Configuration management for SmartCanopy Agent
Loads settings from environment variables with validation
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Keys
    anthropic_api_key: Optional[str] = Field(None, env='ANTHROPIC_API_KEY')
    usda_hardiness_api_key: Optional[str] = Field(None, env='USDA_HARDINESS_API_KEY')

    # Database
    database_url: str = Field(
        default='postgresql+asyncpg://smartcanopy:password@localhost:5432/smartcanopy',
        env='DATABASE_URL'
    )

    # Redis
    redis_url: str = Field(
        default='redis://localhost:6379/0',
        env='REDIS_URL'
    )

    # Claude API Settings
    claude_model: str = Field(
        default='claude-opus-4-5-20251101',
        env='CLAUDE_MODEL'
    )
    claude_max_tokens: int = Field(default=4096, env='CLAUDE_MAX_TOKENS')
    claude_temperature: float = Field(default=1.0, env='CLAUDE_TEMPERATURE')

    # Application Settings
    debug: bool = Field(default=False, env='DEBUG')
    log_level: str = Field(default='INFO', env='LOG_LEVEL')
    allowed_origins: Optional[str] = Field(
        default='http://localhost:3000,http://localhost:8000,http://localhost:5173',
        env='ALLOWED_ORIGINS'
    )

    # File Upload Settings
    upload_dir: str = Field(default='uploads', env='UPLOAD_DIR')
    max_upload_size_mb: int = Field(default=10, env='MAX_UPLOAD_SIZE_MB')

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100, env='RATE_LIMIT_PER_MINUTE')

    # Cache TTL Settings (in seconds)
    cache_ttl_hardiness_zone: int = Field(default=2592000, env='CACHE_TTL_HARDINESS_ZONE')  # 30 days
    cache_ttl_species_rec: int = Field(default=3600, env='CACHE_TTL_SPECIES_REC')  # 1 hour
    cache_ttl_environmental: int = Field(default=604800, env='CACHE_TTL_ENVIRONMENTAL')  # 7 days
    cache_ttl_session: int = Field(default=86400, env='CACHE_TTL_SESSION')  # 24 hours

    # External API URLs
    usda_plants_api_url: str = Field(
        default='https://plantsdb.xyz/search',
        env='USDA_PLANTS_API_URL'
    )
    itree_species_api_url: str = Field(
        default='https://species.itreetools.org/api/species',
        env='ITREE_SPECIES_API_URL'
    )

    # Regional Pricing Multipliers
    regional_pricing_multipliers: dict = {
        'CA': 1.3,
        'NY': 1.25,
        'MA': 1.2,
        'WA': 1.15,
        'OR': 1.1,
        'TX': 0.9,
        'AZ': 0.95,
        'FL': 1.05,
        'default': 1.0
    }

    # Clearance Standards (in feet)
    clearance_building_ft: int = 15
    clearance_road_ft: int = 10
    clearance_sidewalk_ft: int = 8
    clearance_overhead_utility_ft: int = 20

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False
        extra = 'ignore'  # Ignore extra fields like DB_PASSWORD (used by docker-compose)

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v.upper()

    def get_price_multiplier(self, state_code: str) -> float:
        """
        Get regional price multiplier for a state

        Args:
            state_code: Two-letter state code (e.g., 'CA')

        Returns:
            Price multiplier (default 1.0)
        """
        return self.regional_pricing_multipliers.get(
            state_code.upper(),
            self.regional_pricing_multipliers['default']
        )


# Singleton settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get application settings singleton

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Export for convenience
settings = get_settings()
