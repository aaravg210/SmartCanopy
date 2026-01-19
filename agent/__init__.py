"""
SmartCanopy AI Agent
AI-powered urban tree planting recommendation system
"""

from typing import Optional, List
import logging

from agent.agent import SmartCanopyAgent
from agent.config import settings
from agent.tools import (
    BaseTool,
    create_all_tools,
    create_database_tools,
    create_standalone_tools,
    TOOL_INFO
)
from agent.services.plant_database import DatabaseManager
from agent.services.cache_service import CacheService

logger = logging.getLogger(__name__)

__all__ = [
    'SmartCanopyAgent',
    'create_agent',
    'create_agent_with_tools',
    'settings',
    'BaseTool',
    'create_all_tools',
    'create_database_tools',
    'create_standalone_tools',
    'TOOL_INFO',
    'DatabaseManager',
    'CacheService'
]


def create_agent(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    database_url: Optional[str] = None,
    redis_url: Optional[str] = None,
    include_photo_analyzer: bool = True,
    tools: Optional[List[BaseTool]] = None
) -> SmartCanopyAgent:
    """
    Create a fully configured SmartCanopy agent with all tools.

    This is the recommended way to create an agent instance. It handles
    dependency injection for all 7 tools automatically.

    Args:
        api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        model: Claude model to use (defaults to settings.claude_model)
        database_url: PostgreSQL URL (defaults to DATABASE_URL env var)
        redis_url: Redis URL (defaults to REDIS_URL env var)
        include_photo_analyzer: Whether to include photo analysis tool
        tools: Optional list of pre-configured tools (overrides automatic creation)

    Returns:
        Configured SmartCanopyAgent instance

    Example:
        >>> # Simple usage with defaults
        >>> agent = create_agent()
        >>>
        >>> # Custom configuration
        >>> agent = create_agent(
        ...     database_url="postgresql+asyncpg://localhost/smartcanopy",
        ...     include_photo_analyzer=False
        ... )
        >>>
        >>> # Use the agent
        >>> response = await agent.chat("What trees grow well in zone 7?")

    Raises:
        ValueError: If required configuration is missing
    """
    if tools is None:
        # Create database and cache services
        db_url = database_url or settings.database_url
        cache_url = redis_url or settings.redis_url

        db_manager = DatabaseManager(db_url)
        cache_service = CacheService(cache_url) if cache_url else None

        # Create all tools with dependencies
        tools = create_all_tools(
            db_manager=db_manager,
            cache_service=cache_service,
            include_photo_analyzer=include_photo_analyzer
        )

        logger.info(f"Created agent with {len(tools)} tools")

    return SmartCanopyAgent(
        api_key=api_key,
        model=model,
        tools=tools
    )


def create_agent_with_tools(
    db_manager: DatabaseManager,
    cache_service: Optional[CacheService] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    include_photo_analyzer: bool = True
) -> SmartCanopyAgent:
    """
    Create an agent with explicit database and cache dependencies.

    Use this when you want more control over service lifecycle,
    e.g., when sharing services across multiple components.

    Args:
        db_manager: Pre-configured database manager
        cache_service: Optional pre-configured cache service
        api_key: Anthropic API key
        model: Claude model to use
        include_photo_analyzer: Whether to include photo analysis tool

    Returns:
        Configured SmartCanopyAgent instance

    Example:
        >>> from agent.services.plant_database import DatabaseManager
        >>> from agent.services.cache_service import CacheService
        >>>
        >>> # Create shared services
        >>> db_manager = DatabaseManager("postgresql+asyncpg://localhost/smartcanopy")
        >>> cache_service = CacheService("redis://localhost:6379/0")
        >>>
        >>> # Create agent with shared services
        >>> agent = create_agent_with_tools(db_manager, cache_service)
    """
    tools = create_all_tools(
        db_manager=db_manager,
        cache_service=cache_service,
        include_photo_analyzer=include_photo_analyzer
    )

    return SmartCanopyAgent(
        api_key=api_key,
        model=model,
        tools=tools
    )
