"""
Agent Chat API Routes
Handles conversational interactions with SmartCanopy AI Agent
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime
import uuid

from agent.agent import SmartCanopyAgent
from agent.services.plant_database import DatabaseManager
from agent.services.cache_service import CacheService
from agent.tools import (
    SpeciesRecommenderTool,
    PricingCalculatorTool,
    EnvironmentalCalculatorTool,
    HazardCheckerTool,
    MaintenanceGuideTool,
    PlantingInstructionsTool
)
from agent.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class ChatMessage(BaseModel):
    """Single message in a conversation"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat request payload"""
    message: str = Field(..., min_length=1, description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Previous conversation messages"
    )
    site_context: Optional[Dict[str, Any]] = Field(None, description="Planting site context")
    max_tool_rounds: int = Field(5, ge=1, le=10, description="Maximum tool execution rounds")


class ChatResponse(BaseModel):
    """Chat response"""
    conversation_id: str = Field(..., description="Conversation ID")
    response: str = Field(..., description="Agent response text")
    conversation_history: List[Dict[str, Any]] = Field(..., description="Updated conversation history")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Tools used in this response")
    rounds: int = Field(..., description="Number of API rounds used")
    timestamp: str = Field(..., description="Response timestamp")


# Initialize agent (singleton pattern)
_agent_instance = None
_db_manager = None
_cache_service = None


def get_agent() -> SmartCanopyAgent:
    """Get or create agent instance with all tools"""
    global _agent_instance, _db_manager, _cache_service

    if _agent_instance is None:
        logger.info("Initializing SmartCanopy Agent...")

        try:
            # Initialize database and cache
            _db_manager = DatabaseManager(settings.database_url)
            _cache_service = CacheService(settings.redis_url)

            # Initialize all tools
            tools = [
                SpeciesRecommenderTool(_db_manager, _cache_service),
                PricingCalculatorTool(_db_manager),
                EnvironmentalCalculatorTool(_db_manager, _cache_service),
                HazardCheckerTool(_db_manager),
                MaintenanceGuideTool(_db_manager),
                PlantingInstructionsTool(_db_manager)
            ]

            _agent_instance = SmartCanopyAgent(tools=tools)
            logger.info(f"✅ Agent initialized with {len(tools)} tools")

        except Exception as e:
            logger.warning(f"Could not initialize tools: {e}")
            logger.warning("Agent will run in conversation-only mode")
            _agent_instance = SmartCanopyAgent(tools=[])

    return _agent_instance


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with SmartCanopy AI Agent

    **Request:**
    - `message`: User's message (required)
    - `conversation_id`: Optional conversation ID for context
    - `conversation_history`: Optional previous messages
    - `site_context`: Optional planting site data
    - `max_tool_rounds`: Max tool execution rounds (default: 5)

    **Response:**
    - Agent's response with conversation history and tool usage
    """
    try:
        # Get agent instance
        agent = get_agent()

        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())

        logger.info(f"Processing chat request - conversation_id: {conversation_id}")
        logger.debug(f"User message: {request.message[:100]}...")

        # Call agent
        result = await agent.chat(
            message=request.message,
            conversation_history=request.conversation_history,
            conversation_id=conversation_id,
            max_tool_rounds=request.max_tool_rounds
        )

        # Format response
        response = ChatResponse(
            conversation_id=conversation_id,
            response=result['response'],
            conversation_history=result['conversation_history'],
            tool_calls=result['tool_calls'],
            rounds=result['rounds'],
            timestamp=datetime.utcnow().isoformat()
        )

        logger.info(f"Chat response - rounds: {result['rounds']}, tools: {len(result['tool_calls'])}")

        return response

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )


@router.websocket("/ws/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for real-time streaming chat

    **Usage:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/agent/ws/conversation-id');

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'chunk') {
            // Append text chunk
            console.log(data.text);
        } else if (data.type === 'tool_use') {
            // Tool is being executed
            console.log('Using tool:', data.tool_name);
        } else if (data.type === 'complete') {
            // Response complete
            console.log('Done!', data.full_response);
        }
    };

    ws.send(JSON.stringify({ message: 'Hello!' }));
    ```
    """
    await websocket.accept()
    logger.info(f"WebSocket connected - conversation_id: {conversation_id}")

    conversation_history = []

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            request_data = json.loads(data)

            user_message = request_data.get('message', '')
            if not user_message:
                await websocket.send_json({
                    'type': 'error',
                    'message': 'No message provided'
                })
                continue

            logger.info(f"WebSocket message received: {user_message[:100]}...")

            # Get agent
            agent = get_agent()

            # Add user message to history
            conversation_history.append({
                'role': 'user',
                'content': user_message
            })

            try:
                # Stream response from agent
                full_response = ""
                tool_calls_made = []

                async for chunk in agent.chat_stream(
                    message=user_message,
                    conversation_history=conversation_history[:-1],  # Exclude current message
                    conversation_id=conversation_id
                ):
                    if chunk['type'] == 'text':
                        # Send text chunk (chat_stream yields 'content', not 'text')
                        text_content = chunk.get('content', chunk.get('text', ''))
                        await websocket.send_json({
                            'type': 'chunk',
                            'text': text_content
                        })
                        full_response += text_content

                    elif chunk['type'] == 'tool_start':
                        # Notify tool execution starting (chat_stream yields 'tool_start', not 'tool_use')
                        await websocket.send_json({
                            'type': 'tool_use',
                            'tool_name': chunk['tool_name'],
                            'tool_input': chunk.get('inputs', {})
                        })
                        tool_calls_made.append({
                            'tool': chunk['tool_name'],
                            'input': chunk.get('inputs', {})
                        })

                    elif chunk['type'] == 'tool_result':
                        # Tool completed
                        await websocket.send_json({
                            'type': 'tool_result',
                            'tool_name': chunk['tool_name'],
                            'success': chunk.get('success', True)
                        })

                    elif chunk['type'] == 'done':
                        # Stream complete - update conversation history
                        conversation_history = chunk['conversation_history']
                        break

                # Note: conversation_history already updated by 'done' chunk above

                # Send completion message
                await websocket.send_json({
                    'type': 'complete',
                    'full_response': full_response,
                    'tool_calls': tool_calls_made,
                    'conversation_id': conversation_id
                })

            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}", exc_info=True)
                await websocket.send_json({
                    'type': 'error',
                    'message': f'Error: {str(e)}'
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected - conversation_id: {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.close()
        except:
            pass


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get conversation history by ID

    **Note:** Currently returns placeholder. Full implementation
    requires conversation storage in database.
    """
    # TODO: Implement conversation retrieval from database
    return {
        "conversation_id": conversation_id,
        "message": "Conversation storage not yet implemented",
        "messages": []
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete conversation history

    **Note:** Currently returns placeholder. Full implementation
    requires conversation storage in database.
    """
    # TODO: Implement conversation deletion
    return {
        "conversation_id": conversation_id,
        "message": "Conversation deleted (placeholder)",
        "success": True
    }
