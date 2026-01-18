# SmartCanopy AI Agent - Testing Guide

Complete guide to testing the AI Agent and its FastAPI integration.

---

## 🎯 Testing Options

There are **4 ways** to test the SmartCanopy AI Agent:

1. **Direct Agent Testing** (without API) - Test agent logic directly
2. **API Testing** (with FastAPI) - Test through REST endpoints
3. **WebSocket Testing** (real-time streaming) - Test streaming chat
4. **Interactive Browser Testing** (Swagger UI) - Visual testing

---

## Option 1: Direct Agent Testing (No API Required)

### Test 1A: Interactive Chat (Easiest!)

This tests the agent directly without the API layer.

```bash
# Start from project root
source venv/bin/activate

# Optional: Start database for full functionality
docker compose up -d postgres redis

# Run interactive chat
python3 scripts/chat_with_agent.py
```

**What to try:**
```
👤 You: Tell me about environmental benefits of trees

👤 You: Calculate the environmental benefits of planting 1 American Sycamore for 20 years

👤 You: How much does it cost to plant a 6-foot tree in California?

👤 You: What's the best tree for San Francisco?
```

**Type `quit` to exit**

---

### Test 1B: Pre-Scripted Demo

```bash
source venv/bin/activate
python3 scripts/demo_conversation.py
```

Shows 3 example conversations demonstrating agent personality.

---

### Test 1C: Comprehensive Test Suite

```bash
source venv/bin/activate
python3 scripts/test_agent.py
```

Tests:
- Agent initialization
- Conversation flow
- Tool execution (environmental calculator, pricing calculator)
- Database integration

---

## Option 2: API Testing (FastAPI Backend)

### Test 2A: Start the API Server

**Terminal 1 - Start API:**
```bash
source venv/bin/activate

# Make sure database is running
docker compose up -d postgres redis

# Start API server
python3 scripts/run_api.py
```

You should see:
```
🌳 SmartCanopy API Server
================================
Environment: Development
Database: localhost:5432/smartcanopy
Redis: redis://localhost:6379/0

Starting server...
================================

📖 API Documentation:
  • Swagger UI: http://localhost:8000/api/docs
  • ReDoc: http://localhost:8000/api/redoc
```

Keep this terminal running!

---

### Test 2B: Run API Test Suite

**Terminal 2 - Run Tests:**
```bash
source venv/bin/activate
python3 scripts/test_api.py
```

This will test:
1. ✅ Health check
2. ✅ Root endpoint
3. ✅ Species search
4. ✅ Species detail
5. ✅ Agent chat (basic conversation)
6. ✅ Agent chat with tools (environmental calculator)

---

### Test 2C: Manual API Testing with curl

**Test Health Check:**
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

---

**Test Agent Chat (Basic):**
```bash
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What can you help me with?"
  }'
```

Expected response:
```json
{
  "conversation_id": "uuid-here",
  "response": "# Welcome to SmartCanopy AI! 🌳\n\nI'm your urban forestry assistant...",
  "conversation_history": [...],
  "tool_calls": [],
  "rounds": 1,
  "timestamp": "2026-01-17T..."
}
```

---

**Test Agent Chat (With Tools - Environmental Calculator):**
```bash
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Calculate the environmental benefits of planting 1 American Sycamore for 20 years"
  }' | json_pp
```

Expected response:
```json
{
  "conversation_id": "uuid",
  "response": "# Environmental Benefits of 1 American Sycamore Over 20 Years\n\n## CO2 Sequestration\n- **Total:** 1,914.5 kg\n- **Equivalent:** 151 days of car-free driving...",
  "tool_calls": [
    {
      "tool": "environmental_calculator",
      "input": {
        "species_id": "PLOC",
        "quantity": 1,
        "years_projection": 20
      },
      "result": {
        "cumulative_benefits": {
          "co2_kg": 1914.5,
          "stormwater_gallons": 15512.4
        },
        "equivalent_metrics": {
          "car_free_days": "151 days of car-free driving",
          "bathtubs_of_water": "387 bathtubs of stormwater managed"
        }
      }
    }
  ],
  "rounds": 2
}
```

**Key observations:**
- Agent used the `environmental_calculator` tool
- Response includes relatable equivalents (perfect for science fair!)
- Took 2 rounds (user message → tool call → final response)

---

**Test Agent Chat (Pricing Calculator):**
```bash
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How much does it cost to plant a 6-foot American Sycamore in San Francisco with professional planting?"
  }' | json_pp
```

Should use `pricing_calculator` tool with CA regional multiplier (1.3x).

---

**Test Species Search:**
```bash
# Search by name
curl "http://localhost:8000/api/species/search?query=sycamore"

# Search by hardiness zone
curl "http://localhost:8000/api/species/search?hardiness_zone=10&limit=5"

# Get specific species
curl "http://localhost:8000/api/species/PLOC" | json_pp
```

---

### Test 2D: Python Test Script

Create `test_my_agent.py`:
```python
#!/usr/bin/env python3
import httpx
import asyncio
import json

async def test_agent():
    async with httpx.AsyncClient() as client:
        # Test 1: Basic conversation
        print("\n" + "="*80)
        print("TEST 1: Basic Conversation")
        print("="*80)

        response = await client.post(
            "http://localhost:8000/api/agent/chat",
            json={"message": "What can you help me with?"},
            timeout=30.0
        )

        data = response.json()
        print(f"\n🤖 Agent: {data['response'][:300]}...")
        print(f"\nRounds: {data['rounds']}")
        print(f"Tools used: {len(data['tool_calls'])}")

        # Save conversation ID for continuity
        conversation_id = data['conversation_id']
        conversation_history = data['conversation_history']


        # Test 2: Environmental benefits (triggers tool)
        print("\n" + "="*80)
        print("TEST 2: Environmental Calculator Tool")
        print("="*80)

        response = await client.post(
            "http://localhost:8000/api/agent/chat",
            json={
                "message": "Calculate environmental benefits of 1 American Sycamore for 20 years",
                "conversation_id": conversation_id,
                "conversation_history": conversation_history
            },
            timeout=30.0
        )

        data = response.json()
        print(f"\n🤖 Agent: {data['response'][:500]}...")
        print(f"\nRounds: {data['rounds']}")
        print(f"Tools used: {len(data['tool_calls'])}")

        if data['tool_calls']:
            for tool_call in data['tool_calls']:
                print(f"\n📊 Tool: {tool_call['tool']}")
                print(f"Input: {json.dumps(tool_call['input'], indent=2)}")
                if 'cumulative_benefits' in tool_call['result']:
                    benefits = tool_call['result']['cumulative_benefits']
                    print(f"\nResults:")
                    print(f"  CO2: {benefits['co2_kg']:,.1f} kg")
                    print(f"  Stormwater: {benefits['stormwater_gallons']:,.1f} gallons")

                if 'equivalent_metrics' in tool_call['result']:
                    print(f"\nEquivalents:")
                    for metric, value in tool_call['result']['equivalent_metrics'].items():
                        print(f"  • {value}")


        # Test 3: Pricing (triggers another tool)
        print("\n" + "="*80)
        print("TEST 3: Pricing Calculator Tool")
        print("="*80)

        conversation_history = data['conversation_history']

        response = await client.post(
            "http://localhost:8000/api/agent/chat",
            json={
                "message": "How much would this cost with professional planting in ZIP 94102?",
                "conversation_id": conversation_id,
                "conversation_history": conversation_history
            },
            timeout=30.0
        )

        data = response.json()
        print(f"\n🤖 Agent: {data['response'][:500]}...")
        print(f"\nRounds: {data['rounds']}")
        print(f"Tools used: {len(data['tool_calls'])}")

        if data['tool_calls']:
            for tool_call in data['tool_calls']:
                print(f"\n💰 Tool: {tool_call['tool']}")
                if 'total_cost' in tool_call['result']:
                    print(f"Total Cost: ${tool_call['result']['total_cost']}")
                    print(f"Regional Multiplier: {tool_call['result']['breakdown'].get('regional_multiplier', 1.0)}x")


        print("\n" + "="*80)
        print("✅ All Tests Complete!")
        print("="*80)

if __name__ == "__main__":
    print("\n🧪 SmartCanopy Agent Integration Test")
    print("Testing agent through FastAPI backend\n")

    asyncio.run(test_agent())
```

Run it:
```bash
python3 test_my_agent.py
```

---

## Option 3: WebSocket Testing (Real-Time Streaming)

The WebSocket endpoint provides **real-time streaming** - text appears as it's generated!

### Test 3A: Python WebSocket Client

Create `test_websocket.py`:
```python
#!/usr/bin/env python3
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/api/agent/ws/test-conversation-123"

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
                break

        print("="*80)

if __name__ == "__main__":
    print("\n🌳 SmartCanopy WebSocket Test")
    print("Real-time streaming chat\n")

    asyncio.run(test_websocket())
```

Run it:
```bash
python3 test_websocket.py
```

You'll see text appear **in real-time** as the agent generates it!

---

### Test 3B: JavaScript WebSocket Client

Create `test_websocket.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>SmartCanopy WebSocket Test</title>
    <style>
        body { font-family: monospace; margin: 20px; }
        #output {
            border: 1px solid #ccc;
            padding: 10px;
            min-height: 400px;
            white-space: pre-wrap;
        }
        input { width: 80%; padding: 8px; }
        button { padding: 8px 16px; }
    </style>
</head>
<body>
    <h1>🌳 SmartCanopy WebSocket Test</h1>

    <div>
        <input type="text" id="message" placeholder="Type your message..."
               value="Calculate benefits of 1 American Sycamore for 20 years">
        <button onclick="sendMessage()">Send</button>
        <button onclick="clearOutput()">Clear</button>
    </div>

    <h3>Agent Response:</h3>
    <div id="output"></div>

    <script>
        const conversationId = 'test-' + Date.now();
        const ws = new WebSocket(`ws://localhost:8000/api/agent/ws/${conversationId}`);
        const output = document.getElementById('output');

        ws.onopen = () => {
            output.innerHTML += '🔌 Connected!\n\n';
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'chunk') {
                // Streaming text
                output.innerHTML += data.text;
                output.scrollTop = output.scrollHeight;
            }
            else if (data.type === 'tool_use') {
                output.innerHTML += `\n\n[🔧 Using tool: ${data.tool_name}]\n`;
            }
            else if (data.type === 'tool_result') {
                output.innerHTML += `[✅ ${data.tool_name} complete]\n\n`;
            }
            else if (data.type === 'complete') {
                output.innerHTML += '\n\n✅ Response complete!\n';
                output.innerHTML += `Tools used: ${data.tool_calls.length}\n`;
                data.tool_calls.forEach(t => {
                    output.innerHTML += `  • ${t.tool}\n`;
                });
                output.innerHTML += '\n' + '='.repeat(80) + '\n\n';
            }
            else if (data.type === 'error') {
                output.innerHTML += `\n❌ Error: ${data.message}\n`;
            }
        };

        function sendMessage() {
            const message = document.getElementById('message').value;
            output.innerHTML += `👤 You: ${message}\n\n🤖 SmartCanopy:\n`;
            ws.send(JSON.stringify({ message: message }));
        }

        function clearOutput() {
            output.innerHTML = '';
        }

        // Allow Enter key to send
        document.getElementById('message').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
```

Open in browser:
```bash
open test_websocket.html
```

Click "Send" and watch the response stream in real-time!

---

## Option 4: Interactive Browser Testing (Swagger UI)

### Test 4A: Open Swagger UI

1. Start API server:
   ```bash
   python3 scripts/run_api.py
   ```

2. Open browser:
   http://localhost:8000/api/docs

3. Find **"Agent"** section

4. Click `POST /api/agent/chat`

5. Click **"Try it out"**

6. Edit request body:
   ```json
   {
     "message": "Calculate environmental benefits of planting 1 American Sycamore for 20 years",
     "max_tool_rounds": 5
   }
   ```

7. Click **"Execute"**

8. Scroll down to see response!

**Perfect for science fair demos!** Shows professional API documentation.

---

## 🎯 Science Fair Demo Script

Here's a complete demo flow for judges:

### Setup (Before Demo)
```bash
# Terminal 1
docker compose up -d postgres redis
source venv/bin/activate
python3 scripts/run_api.py
```

### Demo Flow

**1. Show Interactive Documentation**
- Open: http://localhost:8000/api/docs
- "This is auto-generated API documentation using OpenAPI standard"

**2. Test Basic Conversation**
- POST `/api/agent/chat`
- Message: "What can you help me with?"
- Show friendly, educational response

**3. Test Environmental Calculator** ⭐ **SCIENCE FAIR HIGHLIGHT!**
- POST `/api/agent/chat`
- Message: "Calculate environmental benefits of planting 1 American Sycamore for 20 years"
- Point out:
  - ✅ Real scientific data (i-Tree database)
  - ✅ CO2: 1,914.5 kg over 20 years
  - ✅ Relatable equivalents: "151 days car-free driving"
  - ✅ Stormwater: "387 bathtubs of water"
  - ✅ Dollar value: $884
- Show `tool_calls` array - agent automatically used environmental_calculator

**4. Test Pricing Calculator**
- POST `/api/agent/chat`
- Message: "How much would this cost with professional planting in San Francisco?"
- Show:
  - ✅ Regional pricing (CA = 1.3x multiplier)
  - ✅ Professional labor costs
  - ✅ Complete breakdown

**5. Show WebSocket Streaming** (Optional - impressive!)
- Open `test_websocket.html` in browser
- Click "Send"
- Watch text appear **in real-time**
- "This provides instant feedback in a web UI"

---

## 🔍 What to Look For When Testing

### Agent Working Correctly ✅
- Responds in markdown format with headers, tables, lists
- Educational and friendly tone
- Automatically selects correct tools
- Returns relatable environmental equivalents
- Maintains conversation context

### Tools Working Correctly ✅
- `tool_calls` array appears in response
- Tool results contain expected data
- Agent incorporates tool results into response
- Environmental calculator returns CO2, stormwater, equivalents
- Pricing calculator applies regional multipliers

### API Working Correctly ✅
- Swagger UI loads at `/api/docs`
- Health check returns `{"status": "healthy"}`
- CORS headers present (for web UI)
- Errors return consistent JSON format
- WebSocket connections stay open during streaming

---

## 🐛 Troubleshooting

### Agent Gives Generic Answers (No Tools)
**Problem:** Database not running - agent works but can't use tools

**Check:**
```bash
docker compose ps
```

**Fix:**
```bash
docker compose up -d postgres redis
```

### "Connection Refused"
**Problem:** API server not running

**Fix:**
```bash
python3 scripts/run_api.py
```

### WebSocket Immediately Closes
**Problem:** Malformed message

**Fix:** Ensure JSON message has `message` field:
```json
{"message": "your text here"}
```

### Agent Slow to Respond
**Normal!**
- Simple responses: 3-5 seconds
- With tools: 8-15 seconds
- Claude API processing time + tool execution

### Tools Not Being Called
**Check:** Is your message triggering tool usage?

**Good prompts:**
- "Calculate benefits..." → triggers environmental_calculator
- "How much does it cost..." → triggers pricing_calculator
- "Recommend trees for..." → triggers species_recommender

**Bad prompts:**
- "Tell me about trees" → no tool needed
- "Hello" → no tool needed

---

## 📊 Expected Results

### Environmental Calculator Output
```json
{
  "cumulative_benefits": {
    "co2_kg": 1914.5,
    "stormwater_gallons": 15512.4,
    "air_pollution_kg": 44.2,
    "energy_savings_kwh": 520.0
  },
  "equivalent_metrics": {
    "car_free_days": "151 days of car-free driving",
    "miles_not_driven": "4,994 miles not driven",
    "bathtubs_of_water": "387 bathtubs of stormwater managed"
  },
  "dollar_value": {
    "total_usd": 884.06
  }
}
```

### Pricing Calculator Output
```json
{
  "total_cost": 425.50,
  "breakdown": {
    "tree_price_per_unit": 120.0,
    "regional_multiplier": 1.3,
    "labor_per_tree": 125.0,
    "materials_per_tree": 50.0
  }
}
```

---

## 🎓 Summary

**4 Ways to Test:**
1. ✅ Direct agent: `python3 scripts/chat_with_agent.py`
2. ✅ API with curl: `curl -X POST http://localhost:8000/api/agent/chat ...`
3. ✅ WebSocket: Real-time streaming (Python or HTML)
4. ✅ Swagger UI: http://localhost:8000/api/docs

**Best for Science Fair:**
- Swagger UI (professional, visual)
- WebSocket demo (impressive real-time streaming)
- Environmental calculator (shows real science)

**Key Metrics to Highlight:**
- 1,914.5 kg CO2 over 20 years
- Equivalent to 151 days without driving
- $884 in environmental value
- 387 bathtubs of stormwater managed

Your agent is **fully operational** and ready to impress! 🌳
