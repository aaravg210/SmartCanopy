"""
Base tool framework for SmartCanopy Agent
All agent tools inherit from BaseTool
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """
    Abstract base class for all agent tools

    All tools must implement:
    - name: Tool identifier for Claude API
    - description: What the tool does (shown to Claude)
    - input_schema: JSON Schema for tool parameters
    - execute: Tool logic that returns results
    """

    def __init__(self):
        """Initialize tool"""
        self._execution_count = 0
        self._total_execution_time_ms = 0

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Tool name used by Claude API

        Returns:
            Tool identifier (e.g., "species_recommender")
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Tool description shown to Claude

        Should explain:
        - What the tool does
        - When to use it
        - What it returns

        Returns:
            Description string
        """
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """
        JSON Schema for tool input parameters

        Returns:
            JSON Schema dict following Claude API format
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute tool logic

        Args:
            **kwargs: Tool input parameters matching input_schema

        Returns:
            Tool result as dictionary

        Raises:
            ToolExecutionError: If tool execution fails
        """
        pass

    async def run(
        self,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run tool with logging and error handling

        Args:
            conversation_id: Optional conversation ID for logging
            **kwargs: Tool input parameters

        Returns:
            Tool result with metadata
        """
        start_time = time.time()
        cache_hit = False

        try:
            # Validate inputs against schema
            self._validate_inputs(kwargs)

            # Check cache if tool supports it
            if hasattr(self, 'cache') and hasattr(self, '_check_cache'):
                cached_result = await self._check_cache(kwargs)
                if cached_result is not None:
                    cache_hit = True
                    result = cached_result
                else:
                    # Execute tool
                    result = await self.execute(**kwargs)

                    # Cache result
                    if hasattr(self, '_cache_result'):
                        await self._cache_result(kwargs, result)
            else:
                # Execute tool without caching
                result = await self.execute(**kwargs)

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Update stats
            self._execution_count += 1
            self._total_execution_time_ms += execution_time_ms

            # Log execution
            await self._log_execution(
                conversation_id=conversation_id,
                input_parameters=kwargs,
                output_result=result,
                execution_time_ms=execution_time_ms,
                cache_hit=cache_hit,
                success=True
            )

            logger.info(
                f"Tool {self.name} executed successfully "
                f"(time: {execution_time_ms}ms, cache: {cache_hit})"
            )

            return result

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Log error
            await self._log_execution(
                conversation_id=conversation_id,
                input_parameters=kwargs,
                output_result=None,
                execution_time_ms=execution_time_ms,
                cache_hit=False,
                success=False,
                error_message=str(e)
            )

            logger.error(f"Tool {self.name} execution failed: {e}")

            raise ToolExecutionError(
                tool_name=self.name,
                message=str(e),
                inputs=kwargs
            )

    def _validate_inputs(self, inputs: Dict[str, Any]):
        """
        Validate inputs against schema

        Args:
            inputs: Tool input parameters

        Raises:
            ValueError: If validation fails
        """
        schema = self.input_schema
        required_fields = schema.get('required', [])

        # Check required fields
        for field in required_fields:
            if field not in inputs or inputs[field] is None:
                raise ValueError(f"Missing required field: {field}")

        # Note: Could add more detailed validation using jsonschema library
        # For now, basic validation is sufficient

    async def _log_execution(
        self,
        conversation_id: Optional[str],
        input_parameters: Dict,
        output_result: Optional[Dict],
        execution_time_ms: int,
        cache_hit: bool,
        success: bool,
        error_message: Optional[str] = None
    ):
        """
        Log tool execution to database

        Args:
            conversation_id: Conversation ID
            input_parameters: Tool inputs
            output_result: Tool outputs
            execution_time_ms: Execution time
            cache_hit: Whether result came from cache
            success: Whether execution succeeded
            error_message: Error message if failed
        """
        try:
            from agent.services.plant_database import DatabaseManager, ToolExecution
            from agent.config import settings
            import uuid

            db_manager = DatabaseManager(settings.database_url)
            async with db_manager.get_session() as session:
                log_entry = ToolExecution(
                    conversation_id=uuid.UUID(conversation_id) if conversation_id else None,
                    tool_name=self.name,
                    input_parameters=input_parameters,
                    output_result=output_result,
                    execution_time_ms=execution_time_ms,
                    cache_hit=cache_hit,
                    success=success,
                    error_message=error_message
                )
                session.add(log_entry)
                await session.commit()

        except Exception as e:
            # Don't fail tool execution if logging fails
            logger.warning(f"Failed to log tool execution: {e}")

    def to_claude_tool(self) -> Dict[str, Any]:
        """
        Convert tool to Claude API tool definition format

        Returns:
            Tool definition dict for Claude API
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get tool execution statistics

        Returns:
            Stats dictionary
        """
        avg_time = (
            self._total_execution_time_ms / self._execution_count
            if self._execution_count > 0 else 0
        )

        return {
            "tool_name": self.name,
            "execution_count": self._execution_count,
            "total_time_ms": self._total_execution_time_ms,
            "average_time_ms": round(avg_time, 2)
        }


class ToolExecutionError(Exception):
    """Exception raised when tool execution fails"""

    def __init__(self, tool_name: str, message: str, inputs: Dict[str, Any]):
        self.tool_name = tool_name
        self.message = message
        self.inputs = inputs
        super().__init__(f"Tool '{tool_name}' failed: {message}")


class CachedTool(BaseTool):
    """
    Base class for tools that support caching

    Subclasses should implement:
    - cache_ttl: Time to live for cached results
    """

    def __init__(self, cache_service):
        """
        Initialize cached tool

        Args:
            cache_service: CacheService instance
        """
        super().__init__()
        self.cache = cache_service

    @property
    @abstractmethod
    def cache_ttl(self) -> int:
        """
        Cache time-to-live in seconds

        Returns:
            TTL in seconds
        """
        pass

    async def _check_cache(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if result is cached

        Args:
            params: Tool input parameters

        Returns:
            Cached result or None
        """
        from agent.services.cache_service import ToolCache

        tool_cache = ToolCache(self.cache)
        return await tool_cache.get_result(self.name, params)

    async def _cache_result(self, params: Dict[str, Any], result: Dict[str, Any]):
        """
        Cache tool result

        Args:
            params: Tool input parameters
            result: Tool output
        """
        from agent.services.cache_service import ToolCache

        tool_cache = ToolCache(self.cache)
        await tool_cache.set_result(self.name, params, result, self.cache_ttl)


# ============================================================================
# Tool Registry
# ============================================================================

class ToolRegistry:
    """Registry for managing available tools"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """
        Register a tool

        Args:
            tool: Tool instance
        """
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get tool by name

        Args:
            tool_name: Tool name

        Returns:
            Tool instance or None
        """
        return self._tools.get(tool_name)

    def get_all(self) -> Dict[str, BaseTool]:
        """
        Get all registered tools

        Returns:
            Dictionary of tool name -> tool instance
        """
        return self._tools.copy()

    def to_claude_tools(self) -> list:
        """
        Convert all tools to Claude API format

        Returns:
            List of tool definitions
        """
        return [tool.to_claude_tool() for tool in self._tools.values()]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all tools

        Returns:
            Statistics dictionary
        """
        return {
            "total_tools": len(self._tools),
            "tools": {
                name: tool.get_stats()
                for name, tool in self._tools.items()
            }
        }


# Global tool registry
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    Get global tool registry

    Returns:
        ToolRegistry instance
    """
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
