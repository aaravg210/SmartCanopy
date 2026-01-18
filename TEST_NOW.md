# Test SmartCanopy AI NOW

This guide tells you exactly how to test the system and what to expect.

---

## Summary of Test Results

I've fixed multiple issues in the test suite. Here's the current status:

| Test Category | Status | Notes |
|---------------|--------|-------|
| **Agent Core Tests** | ✅ 11/11 passing | All agent tests pass |
| **API Integration Tests** | ⚠️ 24/36 passing | Database injection needed for remaining tests |
| **Tool Tests** | ⚠️ Partial | Requires database fixtures |
| **E2E Tests** | ⚠️ Not run | Requires full stack |
| **Performance Tests** | ⚠️ Not run | Requires full stack |

---

## Quick Start: Tests That Work Now

### Test 1: System Status Check

```bash
source venv/bin/activate
python test_system_status.py
```

This checks that all components are installed and configured.

### Test 2: Agent Core Tests (All Pass!)

```bash
source venv/bin/activate
pytest tests/test_agent.py -v
```

**Expected:** 11 tests, all passing

### Test 3: Start the API Server

```bash
source venv/bin/activate
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Then visit:**
- **API Docs:** http://localhost:8000/api/docs (note: `/api/` prefix!)
- **Health Check:** http://localhost:8000/api/health
- **Root:** http://localhost:8000/

### Test 4: Test CV Model

```bash
source venv/bin/activate
python test_gee.py
python planting_site_detector.py
```

These test the computer vision pipeline (tree detection, NDVI, etc.)

### Test 5: Simple Agent Chat

```bash
source venv/bin/activate
python test_chat_simple.py
```

This tests the agent without the full API.

---

## Tests That Require Setup

### Tests #4, #8: WebSocket and Connection Tests

**These require the API server to be running first!**

**Step 1:** Start the API server in one terminal:
```bash
source venv/bin/activate
uvicorn api.main:app --reload
```

**Step 2:** In another terminal, run the test:
```bash
source venv/bin/activate
python test_websocket.py
```

**OR** open `test_websocket.html` in your browser.

**Error you saw:** `[Errno 61] Connect call failed` - This means the API server wasn't running.

### Tests #6 & #7: Database Setup

The database tests require PostgreSQL. Here's how to set it up:

**Option A: Using Docker (Recommended)**
```bash
# Start PostgreSQL
docker run -d \
  --name smartcanopy-postgres \
  -e POSTGRES_USER=smartcanopy \
  -e POSTGRES_PASSWORD=smartcanopy \
  -e POSTGRES_DB=smartcanopy \
  -p 5432:5432 \
  postgres:15

# Wait for it to start
sleep 10

# Run database setup
source venv/bin/activate
python scripts/setup_database.py
python scripts/seed_plants.py
```

**Option B: Using Local PostgreSQL**
```bash
# Create the database
createdb smartcanopy

# Update .env with your connection string
# DATABASE_URL=postgresql://localhost/smartcanopy

# Run setup
python scripts/setup_database.py
python scripts/seed_plants.py
```

**After database setup, the species/site tests should work.**

### Test #10: Full Test Suite

After I fixed the tests, the results improved significantly:

**Before fixes:** 15 failed, 15 passed, 54 errors
**After fixes:** 12 failed, 24 passed, 0 errors

The remaining failures are mostly because:
1. API integration tests need the database injected into the test client
2. Some tests expect endpoints that use a real database

To run the tests:
```bash
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run only the passing tests
pytest tests/test_agent.py -v
```

---

## What I Fixed

### Issue 1: API URLs (Test #2)
- **Problem:** Tests used `/health` but API has `/api/health`
- **Fixed:** Updated all test URLs to use `/api/` prefix

### Issue 2: Database Types (Test #10)
- **Problem:** PostgreSQL-specific types (JSONB, UUID) don't work with SQLite
- **Fixed:** Created cross-database compatible types (JSONType, GUID)

### Issue 3: Model Field Mismatches (Test #10)
- **Problem:** Test fixtures used wrong field names
- **Fixed:** Updated fixtures to match actual model fields

### Issue 4: Mock Type Mismatches (Test #10)
- **Problem:** Tests mocked AsyncAnthropic but agent uses sync Anthropic
- **Fixed:** Updated mocks to use correct types

---

## Current Test Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run all agent tests (11 tests, all pass)
pytest tests/test_agent.py -v

# Run API integration tests (24/36 pass without database)
pytest tests/test_api_integration.py -v

# Run with timeout to avoid hanging
pytest tests/ -v --timeout=60

# Run specific test
pytest tests/test_agent.py::TestSmartCanopyAgent::test_agent_initialization -v

# Run with coverage
pytest tests/ --cov=agent --cov=api --cov-report=html
```

---

## API Endpoint Reference

The API uses `/api/` prefix for all endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root info |
| `/api/health` | GET | Health check |
| `/api/docs` | GET | Swagger UI |
| `/api/redoc` | GET | ReDoc |
| `/api/openapi.json` | GET | OpenAPI schema |
| `/api/agent/chat` | POST | Chat with agent |
| `/api/agent/ws/{id}` | WS | WebSocket chat |
| `/api/species/search` | GET | Search species |
| `/api/species/{id}` | GET | Get species detail |
| `/api/sites/{id}` | GET | Get site detail |
| `/api/cv/analyze` | POST | Run CV analysis |

---

## Testing Sequence

1. **Quick Win:** `pytest tests/test_agent.py -v` - All 11 pass
2. **System Check:** `python test_system_status.py` - Verify setup
3. **Start API:** `uvicorn api.main:app --reload`
4. **Visit Docs:** http://localhost:8000/api/docs
5. **Test CV:** `python planting_site_detector.py`
6. **Setup DB:** `docker run postgres...` + `python scripts/setup_database.py`
7. **Full Tests:** `pytest tests/ -v`

---

## Troubleshooting

### "Connection refused" errors
The API server isn't running. Start it first:
```bash
uvicorn api.main:app --reload
```

### "404 Not Found" on /docs
Use `/api/docs` not `/docs`. All API endpoints have `/api/` prefix.

### "JSONB" or database errors
The database models now use cross-compatible types. Make sure you're using the latest code.

### Tests timing out
Use `--timeout=60` flag to set a timeout:
```bash
pytest tests/ -v --timeout=60
```

---

## Files Changed to Fix Tests

1. **`agent/services/plant_database.py`** - Added cross-DB compatible types (GUID, JSONType)
2. **`tests/test_agent.py`** - Fixed mock types, tool initialization
3. **`tests/test_api_integration.py`** - Fixed URL paths
4. **`tests/conftest.py`** - Fixed fixture field names

---

## Next Steps

1. Run `pytest tests/test_agent.py -v` - should all pass
2. Start API server and visit http://localhost:8000/api/docs
3. Set up PostgreSQL if you want full database tests
4. Run full test suite: `pytest tests/ -v`

Questions? Let me know what specific tests you want to run!
