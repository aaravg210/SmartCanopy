"""
SmartCanopy AI Agent - Core agent with Claude API integration
Orchestrates tool execution and conversation management
"""

import anthropic
from typing import List, Dict, Any, Optional, AsyncIterator
import logging
from pathlib import Path

from agent.config import settings
from agent.tools.base_tool import BaseTool, ToolExecutionError

logger = logging.getLogger(__name__)


class SmartCanopyAgent:
    """
    Core AI agent for SmartCanopy tree planting recommendations

    Integrates with Claude API for natural language understanding
    and orchestrates specialized tools for tree recommendations,
    environmental calculations, and planting guidance.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        tools: Optional[List[BaseTool]] = None
    ):
        """
        Initialize SmartCanopy Agent

        Args:
            api_key: Anthropic API key (defaults to settings.anthropic_api_key)
            model: Claude model to use (defaults to settings.claude_model)
            tools: List of tool instances (defaults to all available tools)
        """
        self.api_key = api_key or settings.anthropic_api_key
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY in .env file"
            )

        # Use sync client for non-streaming operations
        self.client = anthropic.Anthropic(api_key=self.api_key)
        # Use async client for streaming operations
        self.async_client = anthropic.AsyncAnthropic(api_key=self.api_key)
        self.model = model or settings.claude_model
        self.max_tokens = settings.claude_max_tokens
        self.temperature = settings.claude_temperature

        # Load system prompt
        prompt_path = Path(__file__).parent / "prompts" / "system_prompt.txt"
        with open(prompt_path, 'r') as f:
            self.system_prompt = f.read()

        # Register tools
        self.tools: Dict[str, BaseTool] = {}
        if tools:
            for tool in tools:
                self.register_tool(tool)

        logger.info(
            f"SmartCanopy Agent initialized with model {self.model}, "
            f"{len(self.tools)} tools registered"
        )

    def register_tool(self, tool: BaseTool):
        """Register a tool with the agent"""
        self.tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def get_claude_tools(self) -> List[Dict[str, Any]]:
        """Convert registered tools to Claude API format"""
        return [tool.to_claude_tool() for tool in self.tools.values()]

    async def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        conversation_id: Optional[str] = None,
        max_tool_rounds: int = 5
    ) -> Dict[str, Any]:
        """
        Process a user message and return agent response

        Args:
            message: User's message
            conversation_history: Previous messages in conversation
            conversation_id: Optional conversation ID for logging
            max_tool_rounds: Maximum number of tool execution rounds

        Returns:
            Dict with 'response' (final text), 'tool_calls' (list of tools used),
            'conversation_history' (updated history)
        """
        # Initialize conversation history
        if conversation_history is None:
            conversation_history = []

        # Add user message
        conversation_history.append({
            "role": "user",
            "content": message
        })

        tool_calls_made = []
        rounds = 0

        while rounds < max_tool_rounds:
            rounds += 1

            try:
                # Call Claude API
                api_params = {
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "system": self.system_prompt,
                    "messages": conversation_history
                }

                # Only add tools if we have them
                if self.tools:
                    api_params["tools"] = self.get_claude_tools()

                response = self.client.messages.create(**api_params)

                # Process response
                if response.stop_reason == "end_turn":
                    # Final response - extract text
                    final_text = self._extract_text_from_content(response.content)
                    conversation_history.append({
                        "role": "assistant",
                        "content": response.content
                    })

                    logger.info(
                        f"Conversation completed in {rounds} rounds, "
                        f"{len(tool_calls_made)} tools called"
                    )

                    return {
                        "response": final_text,
                        "tool_calls": tool_calls_made,
                        "conversation_history": conversation_history,
                        "rounds": rounds
                    }

                elif response.stop_reason == "tool_use":
                    # Execute tools and continue conversation
                    conversation_history.append({
                        "role": "assistant",
                        "content": response.content
                    })

                    # Track which tools were called (before execution)
                    for block in response.content:
                        if block.type == "tool_use":
                            tool_calls_made.append({
                                "tool": block.name,
                                "input": block.input,
                                "result": None  # Will be filled after execution
                            })

                    # Extract and execute tool calls
                    tool_results = await self._execute_tools(
                        response.content,
                        conversation_id
                    )

                    # Update tool calls with results
                    tool_index = 0
                    for result in tool_results:
                        if tool_index < len(tool_calls_made):
                            # Add result to corresponding tool call
                            if "is_error" in result and result["is_error"]:
                                tool_calls_made[tool_index]["result"] = {"error": result["content"]}
                            else:
                                # Parse result if it's JSON string
                                try:
                                    import json
                                    tool_calls_made[tool_index]["result"] = json.loads(result["content"])
                                except:
                                    tool_calls_made[tool_index]["result"] = result["content"]
                            tool_index += 1

                    # Add tool results to conversation
                    conversation_history.append({
                        "role": "user",
                        "content": tool_results
                    })

                    # Continue loop to get next response
                    continue

                elif response.stop_reason == "max_tokens":
                    # Response was truncated
                    logger.warning("Response truncated due to max_tokens limit")
                    final_text = self._extract_text_from_content(response.content)
                    conversation_history.append({
                        "role": "assistant",
                        "content": response.content
                    })

                    return {
                        "response": final_text + "\n\n[Response truncated - please continue]",
                        "tool_calls": tool_calls_made,
                        "conversation_history": conversation_history,
                        "rounds": rounds,
                        "truncated": True
                    }

                else:
                    # Unexpected stop reason
                    logger.error(f"Unexpected stop reason: {response.stop_reason}")
                    raise RuntimeError(f"Unexpected stop reason: {response.stop_reason}")

            except anthropic.APIError as e:
                logger.error(f"Claude API error: {e}")
                raise
            except Exception as e:
                logger.error(f"Error in chat: {e}")
                raise

        # Max rounds reached
        logger.warning(f"Max tool rounds ({max_tool_rounds}) reached")
        final_text = "I apologize, but I've reached the limit of tool executions. Please try breaking your request into smaller steps."

        return {
            "response": final_text,
            "tool_calls": tool_calls_made,
            "conversation_history": conversation_history,
            "rounds": rounds,
            "max_rounds_reached": True
        }

    async def chat_stream(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        conversation_id: Optional[str] = None,
        max_tool_rounds: int = 5
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream agent response in real-time

        Yields dictionaries with 'type' field:
        - {'type': 'text', 'content': str} - Text chunk
        - {'type': 'tool_start', 'tool_name': str, 'inputs': dict} - Tool execution starting
        - {'type': 'tool_result', 'tool_name': str, 'result': dict} - Tool execution complete
        - {'type': 'done', 'conversation_history': list} - Conversation complete

        Args:
            message: User's message
            conversation_history: Previous messages in conversation
            conversation_id: Optional conversation ID for logging
            max_tool_rounds: Maximum number of tool execution rounds
        """
        # Initialize conversation history
        if conversation_history is None:
            conversation_history = []

        # Add user message
        conversation_history.append({
            "role": "user",
            "content": message
        })

        rounds = 0

        while rounds < max_tool_rounds:
            rounds += 1

            try:
                # Stream Claude API response using async client
                async with self.async_client.messages.stream(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=self.system_prompt,
                    messages=conversation_history,
                    tools=self.get_claude_tools() if self.tools else None
                ) as stream:

                    # Collect content blocks for conversation history
                    content_blocks = []
                    current_text = ""

                    async for event in stream:
                        if event.type == "content_block_start":
                            if event.content_block.type == "text":
                                current_text = ""

                        elif event.type == "content_block_delta":
                            if event.delta.type == "text_delta":
                                # Stream text to user
                                yield {
                                    "type": "text",
                                    "content": event.delta.text
                                }
                                current_text += event.delta.text

                        elif event.type == "content_block_stop":
                            if current_text:
                                content_blocks.append({
                                    "type": "text",
                                    "text": current_text
                                })
                                current_text = ""

                    # Get final message
                    final_message = await stream.get_final_message()

                    # Add assistant response to history
                    conversation_history.append({
                        "role": "assistant",
                        "content": final_message.content
                    })

                    # Check stop reason
                    if final_message.stop_reason == "end_turn":
                        # Conversation complete
                        yield {
                            "type": "done",
                            "conversation_history": conversation_history,
                            "rounds": rounds
                        }
                        return

                    elif final_message.stop_reason == "tool_use":
                        # Execute tools
                        tool_results = []

                        for block in final_message.content:
                            if block.type == "tool_use":
                                # Notify tool execution starting
                                yield {
                                    "type": "tool_start",
                                    "tool_name": block.name,
                                    "inputs": block.input
                                }

                                # Execute tool
                                try:
                                    tool = self.tools.get(block.name)
                                    if not tool:
                                        raise ValueError(f"Unknown tool: {block.name}")

                                    result = await tool.run(
                                        conversation_id=conversation_id,
                                        **block.input
                                    )

                                    tool_results.append({
                                        "type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": str(result)
                                    })

                                    # Notify tool execution complete
                                    yield {
                                        "type": "tool_result",
                                        "tool_name": block.name,
                                        "result": result,
                                        "success": True
                                    }

                                except ToolExecutionError as e:
                                    logger.error(f"Tool execution error: {e}")
                                    tool_results.append({
                                        "type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": f"Error: {e.message}",
                                        "is_error": True
                                    })

                                    yield {
                                        "type": "tool_result",
                                        "tool_name": block.name,
                                        "error": e.message,
                                        "success": False
                                    }

                        # Add tool results to conversation
                        conversation_history.append({
                            "role": "user",
                            "content": tool_results
                        })

                        # Continue loop
                        continue

                    elif final_message.stop_reason == "max_tokens":
                        yield {
                            "type": "text",
                            "content": "\n\n[Response truncated - please continue]"
                        }
                        yield {
                            "type": "done",
                            "conversation_history": conversation_history,
                            "rounds": rounds,
                            "truncated": True
                        }
                        return

            except anthropic.APIError as e:
                logger.error(f"Claude API error: {e}")
                yield {
                    "type": "error",
                    "error": str(e)
                }
                return
            except Exception as e:
                logger.error(f"Error in chat_stream: {e}")
                yield {
                    "type": "error",
                    "error": str(e)
                }
                return

        # Max rounds reached
        yield {
            "type": "text",
            "content": "\n\nI apologize, but I've reached the limit of tool executions."
        }
        yield {
            "type": "done",
            "conversation_history": conversation_history,
            "rounds": rounds,
            "max_rounds_reached": True
        }

    async def _execute_tools(
        self,
        content_blocks: List[Any],
        conversation_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute tool calls from Claude's response

        Args:
            content_blocks: Content blocks from Claude API response
            conversation_id: Optional conversation ID for logging

        Returns:
            List of tool results in Claude API format
        """
        results = []

        for block in content_blocks:
            if block.type == "tool_use":
                tool_name = block.name
                tool_inputs = block.input
                tool_use_id = block.id

                logger.info(f"Executing tool: {tool_name} with inputs: {tool_inputs}")

                try:
                    # Get tool instance
                    tool = self.tools.get(tool_name)
                    if not tool:
                        raise ValueError(f"Unknown tool: {tool_name}")

                    # Execute tool
                    result = await tool.run(
                        conversation_id=conversation_id,
                        **tool_inputs
                    )

                    # Format result for Claude
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": str(result)
                    })

                    logger.info(f"Tool {tool_name} executed successfully")

                except ToolExecutionError as e:
                    logger.error(f"Tool execution error in {tool_name}: {e}")
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": f"Error executing {tool_name}: {e.message}",
                        "is_error": True
                    })

                except Exception as e:
                    logger.error(f"Unexpected error in {tool_name}: {e}")
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": f"Unexpected error: {str(e)}",
                        "is_error": True
                    })

        return results

    def _extract_text_from_content(self, content_blocks: List[Any]) -> str:
        """Extract text from Claude API content blocks"""
        text_parts = []
        for block in content_blocks:
            if block.type == "text":
                text_parts.append(block.text)
        return "\n".join(text_parts)

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        tool_stats = {}
        for name, tool in self.tools.items():
            tool_stats[name] = {
                "execution_count": tool._execution_count,
                "total_time_ms": tool._total_execution_time_ms,
                "avg_time_ms": (
                    tool._total_execution_time_ms / tool._execution_count
                    if tool._execution_count > 0
                    else 0
                )
            }

        return {
            "model": self.model,
            "tools_registered": len(self.tools),
            "tool_stats": tool_stats
        }
