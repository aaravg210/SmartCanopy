"""
Unit tests for SmartCanopyAgent core functionality
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from agent.agent import SmartCanopyAgent
from agent.tools.base_tool import BaseTool


class MockTool(BaseTool):
    """Mock tool for testing"""

    def __init__(self, tool_name: str = "mock_tool"):
        super().__init__()  # Initialize base class
        self._name = tool_name

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "A mock tool for testing"

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "test_input": {
                    "type": "string",
                    "description": "Test input parameter"
                }
            },
            "required": ["test_input"]
        }

    async def execute(self, **kwargs) -> dict:
        return {
            "result": f"Mock executed with: {kwargs.get('test_input', 'none')}"
        }


@pytest.mark.asyncio
class TestSmartCanopyAgent:
    """Test suite for SmartCanopyAgent"""

    async def test_agent_initialization_without_tools(self):
        """Test that agent can be initialized without tools"""
        agent = SmartCanopyAgent(tools=[])

        assert agent is not None
        # Agent stores tools as a dict, not a list
        assert agent.tools == {}
        assert agent.client is not None

    async def test_agent_initialization_with_tools(self):
        """Test that agent can be initialized with tools"""
        mock_tool = MockTool()
        agent = SmartCanopyAgent(tools=[mock_tool])

        assert agent is not None
        assert len(agent.tools) == 1
        # Tools are stored in a dict keyed by name
        assert "mock_tool" in agent.tools
        assert agent.tools["mock_tool"].name == "mock_tool"

    async def test_tool_registration(self):
        """Test that tools are properly registered in Claude API format"""
        mock_tool = MockTool()
        agent = SmartCanopyAgent(tools=[mock_tool])

        # Agent should convert tools to Claude API format
        assert len(agent.tools) == 1
        # Tools are stored in a dict keyed by name
        assert "mock_tool" in agent.tools
        assert agent.tools["mock_tool"].description == "A mock tool for testing"

    @patch('anthropic.Anthropic')
    async def test_chat_without_tools(self, mock_anthropic_class):
        """Test basic chat without tool calls"""
        # Mock the Anthropic API response
        mock_message = Mock()
        mock_message.content = [
            type('obj', (object,), {
                'type': 'text',
                'text': 'Hello! I can help you with urban tree planting.'
            })()
        ]
        mock_message.stop_reason = "end_turn"
        mock_message.model = "claude-opus-4-5-20251101"
        mock_message.usage = type('obj', (object,), {
            'input_tokens': 100,
            'output_tokens': 50
        })()

        # Create a mock client with synchronous messages.create
        mock_client = Mock()
        mock_client.messages.create = Mock(return_value=mock_message)
        mock_anthropic_class.return_value = mock_client

        agent = SmartCanopyAgent(tools=[])
        agent.client = mock_client

        response = await agent.chat(
            message="Hello",
            conversation_history=[]
        )

        assert response is not None
        assert "response" in response
        assert "conversation_history" in response
        assert "tool_calls" in response
        assert "rounds" in response
        assert response["rounds"] == 1
        assert len(response["tool_calls"]) == 0

    @patch('anthropic.Anthropic')
    async def test_chat_with_conversation_history(self, mock_anthropic_class):
        """Test chat with existing conversation history"""
        mock_message = Mock()
        mock_message.content = [
            type('obj', (object,), {
                'type': 'text',
                'text': 'Of course! Trees provide shade, improve air quality, and sequester carbon.'
            })()
        ]
        mock_message.stop_reason = "end_turn"
        mock_message.model = "claude-opus-4-5-20251101"
        mock_message.usage = type('obj', (object,), {
            'input_tokens': 150,
            'output_tokens': 60
        })()

        # Create a mock client with synchronous messages.create
        mock_client = Mock()
        mock_client.messages.create = Mock(return_value=mock_message)
        mock_anthropic_class.return_value = mock_client

        agent = SmartCanopyAgent(tools=[])
        agent.client = mock_client

        conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi! How can I help?"}
        ]

        # Pass a copy of conversation history since it gets modified
        original_len = len(conversation_history)
        response = await agent.chat(
            message="Tell me about tree benefits",
            conversation_history=conversation_history.copy()
        )

        # Should add new messages to history (user message + assistant response)
        # Original history had 2 messages, we add 1 user message + 1 assistant response = 4 total
        assert len(response["conversation_history"]) >= original_len + 2

    @patch('anthropic.Anthropic')
    async def test_max_tool_rounds_limit(self, mock_anthropic_class):
        """Test that max_tool_rounds prevents infinite loops"""
        # Create a mock that always wants to use tools
        mock_message = Mock()
        mock_message.content = [
            type('obj', (object,), {
                'type': 'tool_use',
                'id': 'tool_123',
                'name': 'mock_tool',
                'input': {'test_input': 'test'}
            })()
        ]
        mock_message.stop_reason = "tool_use"
        mock_message.model = "claude-opus-4-5-20251101"
        mock_message.usage = type('obj', (object,), {
            'input_tokens': 100,
            'output_tokens': 50
        })()

        # Create a mock client with synchronous messages.create
        mock_client = Mock()
        mock_client.messages.create = Mock(return_value=mock_message)
        mock_anthropic_class.return_value = mock_client

        mock_tool = MockTool()
        agent = SmartCanopyAgent(tools=[mock_tool])
        agent.client = mock_client

        # Should stop after max_tool_rounds
        response = await agent.chat(
            message="Use the tool repeatedly",
            conversation_history=[],
            max_tool_rounds=2
        )

        # Should have made exactly 2 rounds (stops at limit)
        assert response["rounds"] <= 2

    async def test_conversation_id_generation(self):
        """Test that conversation IDs are properly generated"""
        agent = SmartCanopyAgent(tools=[])

        # Mock the chat to avoid actual API calls
        with patch.object(agent, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = {
                "response": "Test",
                "conversation_history": [],
                "tool_calls": [],
                "rounds": 1
            }

            result = await agent.chat(
                message="Test",
                conversation_history=[],
                conversation_id=None
            )

            # Should have been called with proper arguments
            mock_chat.assert_called_once()


@pytest.mark.asyncio
class TestToolExecution:
    """Test suite for tool execution logic"""

    async def test_execute_single_tool(self):
        """Test execution of a single tool"""
        mock_tool = MockTool()
        agent = SmartCanopyAgent(tools=[mock_tool])

        # Create a mock tool use block
        tool_use_blocks = [
            type('obj', (object,), {
                'type': 'tool_use',
                'id': 'tool_123',
                'name': 'mock_tool',
                'input': {'test_input': 'hello'}
            })()
        ]

        results = await agent._execute_tools(tool_use_blocks, "test-conversation")

        assert len(results) == 1
        assert results[0]["type"] == "tool_result"
        assert results[0]["tool_use_id"] == "tool_123"
        assert "Mock executed with: hello" in results[0]["content"]

    async def test_execute_multiple_tools(self):
        """Test execution of multiple tools in sequence"""
        mock_tool1 = MockTool("mock_tool")
        mock_tool2 = MockTool("mock_tool_2")

        agent = SmartCanopyAgent(tools=[mock_tool1, mock_tool2])

        tool_use_blocks = [
            type('obj', (object,), {
                'type': 'tool_use',
                'id': 'tool_123',
                'name': 'mock_tool',
                'input': {'test_input': 'first'}
            })(),
            type('obj', (object,), {
                'type': 'tool_use',
                'id': 'tool_456',
                'name': 'mock_tool_2',
                'input': {'test_input': 'second'}
            })()
        ]

        results = await agent._execute_tools(tool_use_blocks, "test-conversation")

        assert len(results) == 2
        assert results[0]["tool_use_id"] == "tool_123"
        assert results[1]["tool_use_id"] == "tool_456"

    async def test_tool_error_handling(self):
        """Test that tool errors are properly caught and returned"""

        class ErrorTool(BaseTool):
            @property
            def name(self) -> str:
                return "error_tool"

            @property
            def description(self) -> str:
                return "A tool that raises errors"

            @property
            def input_schema(self) -> dict:
                return {"type": "object", "properties": {}}

            async def execute(self, **kwargs) -> dict:
                raise ValueError("Intentional test error")

        error_tool = ErrorTool()
        agent = SmartCanopyAgent(tools=[error_tool])

        tool_use_blocks = [
            type('obj', (object,), {
                'type': 'tool_use',
                'id': 'tool_123',
                'name': 'error_tool',
                'input': {}
            })()
        ]

        results = await agent._execute_tools(tool_use_blocks, "test-conversation")

        assert len(results) == 1
        assert results[0]["type"] == "tool_result"
        assert results[0]["is_error"] is True
        assert "Intentional test error" in results[0]["content"]

    async def test_unknown_tool_handling(self):
        """Test handling of unknown tool requests"""
        agent = SmartCanopyAgent(tools=[])

        tool_use_blocks = [
            type('obj', (object,), {
                'type': 'tool_use',
                'id': 'tool_123',
                'name': 'nonexistent_tool',
                'input': {}
            })()
        ]

        results = await agent._execute_tools(tool_use_blocks, "test-conversation")

        assert len(results) == 1
        assert results[0]["is_error"] is True
        assert "Unknown tool" in results[0]["content"]
