#!/usr/bin/env python3
"""
WebSocket Streaming Test
Tests real-time streaming chat with SmartCanopy Agent
"""

import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/api/agent/ws/test-conversation-123"

    try:
        async with websockets.connect(uri) as websocket:
            print("🔌 Connected to WebSocket")
            print("="*80)

            # Send message
            message = {
                "message": "Calculate environmental benefits of planting 1 American Sycamore for 20 years"
            }

            print(f"\n📤 Sending: {message['message']}\n")
            await websocket.send(json.dumps(message))

            print("🤖 SmartCanopy (streaming):\n")
            full_response = ""

            # Receive streaming response
            while True:
                try:
                    response = await websocket.recv()
                    data = json.loads(response)

                    if data['type'] == 'chunk':
                        # Streaming text chunk
                        print(data['text'], end='', flush=True)
                        full_response += data['text']

                    elif data['type'] == 'tool_use':
                        # Tool being executed
                        print(f"\n\n[🔧 Using tool: {data['tool_name']}]", flush=True)

                    elif data['type'] == 'tool_result':
                        # Tool completed
                        print(f"[✅ Tool complete: {data['tool_name']}]\n", flush=True)

                    elif data['type'] == 'complete':
                        # Response fully generated
                        print("\n\n" + "="*80)
                        print("✅ Response complete!")
                        print(f"Tools used: {len(data['tool_calls'])}")
                        for tool in data['tool_calls']:
                            print(f"  • {tool['tool']}")
                        break

                    elif data['type'] == 'error':
                        print(f"\n❌ Error: {data['message']}")
                        break

                except websockets.exceptions.ConnectionClosed:
                    print("\n\n⚠️ Connection closed")
                    break

            print("="*80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the API server is running:")
        print("  python3 scripts/run_api.py")

if __name__ == "__main__":
    print("\n🌳 SmartCanopy WebSocket Test")
    print("Real-time streaming chat")
    print("\nMake sure the API server is running:")
    print("  python3 scripts/run_api.py")
    print()

    input("Press ENTER to connect...")

    asyncio.run(test_websocket())
