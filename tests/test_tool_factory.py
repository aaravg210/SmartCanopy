"""
Unit tests for tool factory functions
"""

import pytest
from unittest.mock import MagicMock, patch

from agent.tools import (
    create_all_tools,
    create_database_tools,
    create_standalone_tools,
    TOOL_INFO,
    BaseTool
)
from agent.tools.factory import TOOL_INFO


class TestToolInfo:
    """Test TOOL_INFO metadata"""

    def test_all_seven_tools_defined(self):
        """Test that all 7 tools are defined in TOOL_INFO"""
        assert len(TOOL_INFO) == 7

    def test_tool_names(self):
        """Test that expected tools are present"""
        expected_tools = [
            'species_recommender',
            'pricing_calculator',
            'environmental_calculator',
            'hazard_checker',
            'maintenance_guide',
            'planting_instructions',
            'photo_analyzer'
        ]
        assert set(TOOL_INFO.keys()) == set(expected_tools)

    def test_tool_info_structure(self):
        """Test that each tool has required metadata"""
        for name, info in TOOL_INFO.items():
            assert 'class' in info, f"{name} missing 'class'"
            assert 'requires_db' in info, f"{name} missing 'requires_db'"
            assert 'requires_cache' in info, f"{name} missing 'requires_cache'"
            assert 'description' in info, f"{name} missing 'description'"

    def test_photo_analyzer_is_standalone(self):
        """Test that photo_analyzer doesn't require db or cache"""
        assert TOOL_INFO['photo_analyzer']['requires_db'] is False
        assert TOOL_INFO['photo_analyzer']['requires_cache'] is False


class TestCreateAllTools:
    """Test create_all_tools factory"""

    def test_creates_all_seven_tools(self):
        """Test that create_all_tools returns all 7 tools"""
        mock_db = MagicMock()
        mock_cache = MagicMock()

        with patch('agent.tools.factory.PhotoAnalyzerTool') as mock_photo:
            mock_photo.return_value = MagicMock(spec=BaseTool)

            tools = create_all_tools(mock_db, mock_cache, include_photo_analyzer=True)

            assert len(tools) == 7

    def test_creates_six_tools_without_photo_analyzer(self):
        """Test that create_all_tools without photo_analyzer returns 6 tools"""
        mock_db = MagicMock()
        mock_cache = MagicMock()

        tools = create_all_tools(mock_db, mock_cache, include_photo_analyzer=False)

        assert len(tools) == 6

        # Verify photo_analyzer is not in the list
        tool_names = [t.name for t in tools]
        assert 'photo_analyzer' not in tool_names

    def test_tools_are_base_tool_instances(self):
        """Test that all returned tools are BaseTool instances"""
        mock_db = MagicMock()
        mock_cache = MagicMock()

        tools = create_all_tools(mock_db, mock_cache, include_photo_analyzer=False)

        for tool in tools:
            assert isinstance(tool, BaseTool)

    def test_works_without_cache_service(self):
        """Test that tools can be created without cache service"""
        mock_db = MagicMock()

        tools = create_all_tools(mock_db, cache_service=None, include_photo_analyzer=False)

        assert len(tools) == 6


class TestCreateDatabaseTools:
    """Test create_database_tools factory"""

    def test_excludes_photo_analyzer(self):
        """Test that create_database_tools excludes photo_analyzer"""
        mock_db = MagicMock()
        mock_cache = MagicMock()

        tools = create_database_tools(mock_db, mock_cache)

        tool_names = [t.name for t in tools]
        assert 'photo_analyzer' not in tool_names
        assert len(tools) == 6


class TestCreateStandaloneTools:
    """Test create_standalone_tools factory"""

    def test_creates_photo_analyzer(self):
        """Test that create_standalone_tools creates photo_analyzer"""
        with patch('agent.tools.factory.PhotoAnalyzerTool') as mock_photo:
            mock_tool = MagicMock(spec=BaseTool)
            mock_tool.name = 'photo_analyzer'
            mock_photo.return_value = mock_tool

            tools = create_standalone_tools()

            assert len(tools) == 1
            assert tools[0].name == 'photo_analyzer'

    def test_handles_photo_analyzer_creation_failure(self):
        """Test graceful handling when PhotoAnalyzerTool fails"""
        with patch('agent.tools.factory.PhotoAnalyzerTool') as mock_photo:
            mock_photo.side_effect = Exception("API key not configured")

            tools = create_standalone_tools()

            # Should return empty list, not raise exception
            assert len(tools) == 0


class TestToolNames:
    """Test that tool names match expected values"""

    def test_tool_name_properties(self):
        """Test that each tool class returns correct name property"""
        mock_db = MagicMock()
        mock_cache = MagicMock()

        tools = create_all_tools(mock_db, mock_cache, include_photo_analyzer=False)

        expected_names = [
            'species_recommender',
            'pricing_calculator',
            'environmental_calculator',
            'hazard_checker',
            'maintenance_guide',
            'planting_instructions'
        ]

        actual_names = [t.name for t in tools]
        assert set(actual_names) == set(expected_names)
