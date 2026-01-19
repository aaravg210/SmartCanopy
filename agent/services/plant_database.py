"""
SQLAlchemy models and database operations for SmartCanopy
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, TIMESTAMP,
    CheckConstraint, ForeignKey, Index, func, JSON, TypeDecorator
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid as uuid_module


# Cross-database compatible types
class GUID(TypeDecorator):
    """Platform-independent GUID type that uses PostgreSQL's UUID or String(36) for SQLite"""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            # Handle various UUID formats that might come back from different drivers
            if isinstance(value, uuid_module.UUID):
                return value
            # Convert string or other UUID-like objects to UUID
            return uuid_module.UUID(str(value))
        return value

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))


class JSONType(TypeDecorator):
    """Platform-independent JSON type that uses JSONB on PostgreSQL or JSON elsewhere"""
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB)
        else:
            return dialect.type_descriptor(JSON)


Base = declarative_base()


# ============================================================================
# Models
# ============================================================================

class PlantSpecies(Base):
    """Tree species catalog with characteristics and environmental benefits"""
    __tablename__ = 'plant_species'

    species_id = Column(String(10), primary_key=True)
    scientific_name = Column(String(255), nullable=False)
    common_name = Column(String(255), nullable=False)
    family = Column(String(100))

    # Growth characteristics
    mature_height_ft_min = Column(Integer)
    mature_height_ft_max = Column(Integer)
    mature_spread_ft_min = Column(Integer)
    mature_spread_ft_max = Column(Integer)
    growth_rate = Column(String(20))

    # Hardiness
    hardiness_zone_min = Column(Integer)
    hardiness_zone_max = Column(Integer)

    # Environmental preferences
    sunlight = Column(String(50))
    soil_types = Column(JSONType)
    moisture_tolerance = Column(String(50))
    drought_tolerant = Column(Boolean, default=False)

    # Environmental benefits (from i-Tree)
    co2_sequestration_kg_year = Column(Float)
    air_pollution_removal_kg_year = Column(Float)
    stormwater_gallons_year = Column(Float)
    energy_savings_kwh_year = Column(Float)

    # Classification
    native_regions = Column(JSONType)
    tree_type = Column(String(50))
    purposes = Column(JSONType)

    # Maintenance
    maintenance_level = Column(String(20))
    pest_resistance = Column(String(20))
    disease_resistance = Column(String(20))

    # Pricing
    price_sapling = Column(Float)
    price_6ft = Column(Float)
    price_8ft = Column(Float)
    price_10ft = Column(Float)

    # Metadata
    image_url = Column(String(500))
    description = Column(Text)
    planting_instructions = Column(Text)
    maintenance_notes = Column(JSONType)

    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recommendations = relationship("Recommendation", back_populates="species")

    def __repr__(self):
        return f"<PlantSpecies(id={self.species_id}, name={self.common_name})>"


class PlantingSite(Base):
    """Analyzed planting sites from CV model"""
    __tablename__ = 'planting_sites'

    site_id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)
    analysis_id = Column(GUID(), nullable=False)

    # Location
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    zip_code = Column(String(10))

    # Site characteristics
    location_pixels = Column(JSONType)
    area_pixels = Column(Integer)
    avg_ndvi = Column(Float)
    avg_slope = Column(Float)
    suitability_score = Column(Float)

    # Infrastructure context
    osm_data = Column(JSONType)
    exclusion_warnings = Column(JSONType)

    # Imagery references
    rgb_image_path = Column(Text)
    ndvi_image_path = Column(Text)
    slope_image_path = Column(Text)

    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recommendations = relationship("Recommendation", back_populates="site")
    photos = relationship("UploadedPhoto", back_populates="site")

    def __repr__(self):
        return f"<PlantingSite(id={self.site_id}, address={self.address})>"


class Conversation(Base):
    """User chat sessions with the AI agent"""
    __tablename__ = 'conversations'

    conversation_id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)
    user_id = Column(GUID())
    session_id = Column(String(255))

    # Context
    address = Column(Text)
    site_ids = Column(JSONType)

    # Conversation state
    messages = Column(JSONType)
    current_phase = Column(String(50))

    # Metadata
    started_at = Column(TIMESTAMP, default=datetime.utcnow)
    last_message_at = Column(TIMESTAMP, default=datetime.utcnow)
    completed = Column(Boolean, default=False)

    # Settings
    user_preferences = Column(JSONType)

    # Relationships
    recommendations = relationship("Recommendation", back_populates="conversation")
    tool_executions = relationship("ToolExecution", back_populates="conversation")
    photos = relationship("UploadedPhoto", back_populates="conversation")

    def __repr__(self):
        return f"<Conversation(id={self.conversation_id}, address={self.address})>"


class Recommendation(Base):
    """Tree species recommendations made by the agent"""
    __tablename__ = 'recommendations'

    recommendation_id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)
    conversation_id = Column(GUID(), ForeignKey('conversations.conversation_id', ondelete='CASCADE'))
    site_id = Column(GUID(), ForeignKey('planting_sites.site_id', ondelete='CASCADE'))
    species_id = Column(String(10), ForeignKey('plant_species.species_id'))

    # Recommendation context
    suitability_score = Column(Float)
    reasoning = Column(Text)
    quantity = Column(Integer, default=1)
    tree_size = Column(String(20))

    # Calculated benefits
    estimated_cost = Column(Float)
    environmental_benefits = Column(JSONType)

    # User actions
    user_selected = Column(Boolean, default=False)
    user_feedback = Column(Text)
    user_rating = Column(Integer)

    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="recommendations")
    site = relationship("PlantingSite", back_populates="recommendations")
    species = relationship("PlantSpecies", back_populates="recommendations")

    def __repr__(self):
        return f"<Recommendation(id={self.recommendation_id}, species={self.species_id})>"


class HardinessZone(Base):
    """Cached USDA hardiness zone data by ZIP code"""
    __tablename__ = 'hardiness_zones'

    zip_code = Column(String(10), primary_key=True)
    hardiness_zone = Column(String(5), nullable=False)
    zone_numeric = Column(Integer)

    # Source metadata
    source = Column(String(50), default='usda_api')
    last_updated = Column(TIMESTAMP, default=datetime.utcnow)

    # Additional climate data
    avg_min_temp_f = Column(Integer)
    climate_data = Column(JSONType)

    def __repr__(self):
        return f"<HardinessZone(zip={self.zip_code}, zone={self.hardiness_zone})>"


class ToolExecution(Base):
    """Log of all agent tool executions for monitoring"""
    __tablename__ = 'tool_executions'

    execution_id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)
    conversation_id = Column(GUID(), ForeignKey('conversations.conversation_id', ondelete='CASCADE'))

    tool_name = Column(String(100), nullable=False)
    input_parameters = Column(JSONType)
    output_result = Column(JSONType)

    # Performance metrics
    execution_time_ms = Column(Integer)
    cache_hit = Column(Boolean, default=False)

    # Error tracking
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    executed_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="tool_executions")

    def __repr__(self):
        return f"<ToolExecution(id={self.execution_id}, tool={self.tool_name})>"


class UploadedPhoto(Base):
    """User-uploaded site photos for analysis"""
    __tablename__ = 'uploaded_photos'

    photo_id = Column(GUID(), primary_key=True, default=uuid_module.uuid4)
    conversation_id = Column(GUID(), ForeignKey('conversations.conversation_id', ondelete='CASCADE'))
    site_id = Column(GUID(), ForeignKey('planting_sites.site_id'))

    # File information
    file_path = Column(Text, nullable=False)
    file_size_bytes = Column(Integer)
    mime_type = Column(String(50))

    # Analysis results
    analysis_result = Column(JSONType)

    uploaded_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="photos")
    site = relationship("PlantingSite", back_populates="photos")

    def __repr__(self):
        return f"<UploadedPhoto(id={self.photo_id}, path={self.file_path})>"


# ============================================================================
# Database Operations
# ============================================================================

class DatabaseManager:
    """Manages database connections and operations"""

    def __init__(self, database_url: str):
        """
        Initialize database manager

        Args:
            database_url: PostgreSQL connection string
        """
        self.engine = create_async_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def create_tables(self):
        """Create all tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """Drop all tables (use with caution)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    def get_session(self) -> AsyncSession:
        """Get a new database session"""
        return self.SessionLocal()


# ============================================================================
# Query Helpers
# ============================================================================

class SpeciesQuery:
    """Helper methods for querying plant species"""

    @staticmethod
    async def search_by_name(session: AsyncSession, query: str) -> List[PlantSpecies]:
        """
        Search species by common or scientific name

        Args:
            session: Database session
            query: Search query string

        Returns:
            List of matching species
        """
        from sqlalchemy import select, or_, func

        stmt = select(PlantSpecies).where(
            or_(
                func.lower(PlantSpecies.common_name).contains(query.lower()),
                func.lower(PlantSpecies.scientific_name).contains(query.lower())
            )
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def filter_by_hardiness(
        session: AsyncSession,
        zone_numeric: int
    ) -> List[PlantSpecies]:
        """
        Get species compatible with hardiness zone

        Args:
            session: Database session
            zone_numeric: Numeric hardiness zone (e.g., 9 for zone 9a/9b)

        Returns:
            List of compatible species
        """
        from sqlalchemy import select

        stmt = select(PlantSpecies).where(
            PlantSpecies.hardiness_zone_min <= zone_numeric,
            PlantSpecies.hardiness_zone_max >= zone_numeric
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def filter_by_purpose(
        session: AsyncSession,
        purposes: List[str]
    ) -> List[PlantSpecies]:
        """
        Get species matching desired purposes

        Args:
            session: Database session
            purposes: List of purposes (e.g., ["shade", "wildlife"])

        Returns:
            List of matching species
        """
        from sqlalchemy import select

        # Use JSONB contains operator
        stmt = select(PlantSpecies).where(
            PlantSpecies.purposes.contains(purposes)
        )
        result = await session.execute(stmt)
        return result.scalars().all()


class SiteQuery:
    """Helper methods for querying planting sites"""

    @staticmethod
    async def get_by_analysis_id(
        session: AsyncSession,
        analysis_id: uuid_module.UUID
    ) -> List[PlantingSite]:
        """
        Get all sites from a CV analysis

        Args:
            session: Database session
            analysis_id: Analysis UUID

        Returns:
            List of planting sites
        """
        from sqlalchemy import select

        stmt = select(PlantingSite).where(
            PlantingSite.analysis_id == analysis_id
        ).order_by(PlantingSite.suitability_score.desc())
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_top_sites(
        session: AsyncSession,
        analysis_id: uuid_module.UUID,
        limit: int = 5
    ) -> List[PlantingSite]:
        """
        Get top N most suitable sites

        Args:
            session: Database session
            analysis_id: Analysis UUID
            limit: Number of sites to return

        Returns:
            List of top planting sites
        """
        from sqlalchemy import select

        stmt = select(PlantingSite).where(
            PlantingSite.analysis_id == analysis_id
        ).order_by(PlantingSite.suitability_score.desc()).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()


class ConversationQuery:
    """Helper methods for querying conversations"""

    @staticmethod
    async def get_active_by_session(
        session: AsyncSession,
        session_id: str
    ) -> Optional[Conversation]:
        """
        Get active conversation for session

        Args:
            session: Database session
            session_id: Session identifier

        Returns:
            Active conversation or None
        """
        from sqlalchemy import select

        stmt = select(Conversation).where(
            Conversation.session_id == session_id,
            Conversation.completed == False
        ).order_by(Conversation.started_at.desc()).limit(1)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_conversation(
        session: AsyncSession,
        session_id: str,
        address: Optional[str] = None,
        site_ids: Optional[List[str]] = None
    ) -> Conversation:
        """
        Create new conversation

        Args:
            session: Database session
            session_id: Session identifier
            address: Optional address
            site_ids: Optional list of site UUIDs

        Returns:
            New conversation object
        """
        conversation = Conversation(
            session_id=session_id,
            address=address,
            site_ids=site_ids or [],
            messages=[],
            current_phase='exploration'
        )
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        return conversation
