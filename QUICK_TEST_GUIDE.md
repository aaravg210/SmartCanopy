# Quick Testing Guide for SmartCanopy AI

This guide shows you how to test the system **right now** with what's currently built.

---

## ✅ What Can You Test Today?

### 1. Test the Agent Directly (Simple Chat)

This tests the core agent without full API setup:

```bash
# Make sure you're in the project directory
cd /Users/aarav/Documents/urban-tree-ai

# Activate virtual environment
source venv/bin/activate

# Run simple chat test
python test_chat_simple.py
```

**What this tests:**
- Agent initialization
- Claude API integration
- Basic conversation flow
- Tool orchestration (if tools are registered)

---

### 2. Test Individual Tools

Each tool can be tested independently:

```bash
source venv/bin/activate

# Test species recommender
python -c "
from agent.tools.species_recommender import SpeciesRecommenderTool
from agent.services.database_manager import DatabaseManager

db = DatabaseManager()
tool = SpeciesRecommenderTool(db, None)
print(f'Tool initialized: {tool.name}')
print(f'Description: {tool.description}')
"
```

---

### 3. Test the CV Model (Already Working)

These tests have been working all along:

```bash
# Test Google Earth Engine connection
python test_gee.py

# Test tree detection model
python test_deepforest.py

# Test the full planting site detector
python planting_site_detector.py
```

**What this tests:**
- GEE satellite imagery fetching
- DeepForest tree detection
- NDVI and slope calculation
- OSM infrastructure filtering
- Planting site recommendations

---

### 4. Database Status Check

Check if the database is set up:

```bash
# Check database connection
python -c "
from agent.services.database_manager import DatabaseManager
import asyncio

async def test_db():
    db = DatabaseManager()
    try:
        async with db.get_session() as session:
            print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database error: {e}')
        print('Need to: docker-compose up -d postgres')

asyncio.run(test_db())
"
```

---

### 5. Check What's Configured

See what you have set up:

```bash
# Check environment variables
cat .env | grep -v "^#" | grep "="

# Check if required services are configured
echo "Checking configuration..."
if [ -f .env ]; then
    echo "✅ .env file exists"
    grep -q "ANTHROPIC_API_KEY" .env && echo "✅ Claude API key set" || echo "❌ Claude API key missing"
    grep -q "DATABASE_URL" .env && echo "✅ Database URL set" || echo "❌ Database URL missing"
else
    echo "❌ .env file missing - copy from .env.example"
fi
```

---

## 🚀 Start Services for Full Testing

### Option A: Quick Start (Minimal Setup)

Just test the agent without database:

```bash
# 1. Make sure ANTHROPIC_API_KEY is set in .env
# 2. Run the simple agent test
source venv/bin/activate
python test_direct_agent.py
```

### Option B: Full Stack (Database + API)

Start all services for complete testing:

```bash
# Terminal 1: Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Wait for services to be ready (about 10 seconds)
sleep 10

# Terminal 2: Run database migrations
source venv/bin/activate
python scripts/setup_database.py

# Terminal 3: Start the API server
source venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 4: Test the API
curl http://localhost:8000/health
```

---

## 🧪 Run Automated Tests (After Fixing Test Issues)

The test suite exists but has some mismatches with the implementation. Here's what to do:

```bash
# See what tests exist
ls -la tests/

# Try running a specific test file
source venv/bin/activate
pytest tests/test_agent.py -v

# If tests fail, that's OK - they're revealing issues
# The failures show what needs to be aligned between tests and implementation
```

---

## 📊 Current System Status

Based on your project files:

✅ **Working:**
- CV Model (tree detection, NDVI, slope analysis)
- Agent core implementation
- Tool implementations (7 tools)
- FastAPI backend
- Database schema
- Test suite (needs minor fixes)

⚠️ **Needs Setup:**
- PostgreSQL database (via Docker or local install)
- Redis cache (optional - tests can mock it)
- Database seeding with plant species data
- Environment variables configuration

❌ **Not Built Yet:**
- Web UI/Frontend
- Production deployment configuration

---

## 🎯 Recommended Testing Sequence

1. **Verify environment** (5 min)
   ```bash
   cat .env | grep ANTHROPIC_API_KEY
   ```

2. **Test CV model** (2 min)
   ```bash
   python test_gee.py
   ```

3. **Test agent directly** (2 min)
   ```bash
   python test_chat_simple.py
   ```

4. **Start database** (if you want full features)
   ```bash
   docker-compose up -d postgres
   python scripts/setup_database.py
   ```

5. **Start API server** (if you want HTTP endpoints)
   ```bash
   uvicorn api.main:app --reload
   # Visit http://localhost:8000/docs
   ```

6. **Run automated tests** (to see coverage)
   ```bash
   pytest tests/ -v
   # Some may fail - that's expected and fixable
   ```

---

## 🔍 What Each Test File Does

| Test File | Purpose | Dependencies Needed |
|-----------|---------|---------------------|
| `test_gee.py` | Google Earth Engine connection | GEE auth |
| `test_deepforest.py` | Tree detection model | Sample images |
| `planting_site_detector.py` | Full CV pipeline | GEE auth |
| `test_chat_simple.py` | Agent basic chat | Claude API key |
| `test_direct_agent.py` | Agent without API server | Claude API key |
| `test_websocket.py` | WebSocket agent chat | API server running |
| `tests/test_agent.py` | Agent unit tests | None (mocked) |
| `tests/test_api_integration.py` | API endpoint tests | Database (can be in-memory) |

---

## 💡 Quick Wins

**Want to see something work immediately?**

```bash
# Test 1: Verify CV model still works
python test_gee.py

# Test 2: See agent tools list
python -c "from agent.agent import SmartCanopyAgent; agent = SmartCanopyAgent(tools=[]); print(f'Agent created with {len(agent.tools)} tools')"

# Test 3: Check API routes
python -c "from api.main import app; print([r.path for r in app.routes])"
```

---

## 🐛 Common Issues

### "ModuleNotFoundError: No module named 'pytest'"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "earthengine authenticate required"
```bash
earthengine authenticate
```

### "Anthropic API key required"
```bash
# Add to .env file:
echo "ANTHROPIC_API_KEY=your-key-here" >> .env
```

### "Database connection failed"
```bash
docker-compose up -d postgres
# Wait 10 seconds
python scripts/setup_database.py
```

---

**Next:** After you test what's working, I can help you:
1. Fix the test suite to match the implementation
2. Set up the database and seed it with plant data
3. Start the API server for interactive testing
4. Build the web UI (next phase)
