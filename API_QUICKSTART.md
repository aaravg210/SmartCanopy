# SmartCanopy API - Quick Start Guide

Get the SmartCanopy FastAPI backend up and running in 5 minutes!

---

## ⚡ Quick Start

### 1. Start Database (Required for Full Functionality)

```bash
# Open Docker Desktop (Applications folder)
# Wait ~30 seconds for it to fully start

# Start PostgreSQL and Redis
docker compose up -d postgres redis

# Verify containers are running
docker compose ps
```

You should see:
```
NAME                   STATUS
smartcanopy-postgres   Up
smartcanopy-redis      Up
```

---

### 2. Activate Python Environment

```bash
source venv/bin/activate
```

---

### 3. Start API Server

**Option A: Using the run script (recommended)**
```bash
python3 scripts/run_api.py
```

**Option B: Using uvicorn directly**
```bash
uvicorn api.main:app --reload
```

**Option C: Using the main file**
```bash
python3 api/main.py
```

---

### 4. Test the API

Open your browser and go to:

**📖 Interactive Documentation:**
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

**✅ Health Check:**
```bash
curl http://localhost:8000/api/health
```

**Or run the test suite:**
```bash
python3 scripts/test_api.py
```

---

## 🎯 Example API Calls

### Chat with the Agent

```bash
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about the environmental benefits of planting trees"
  }'
```

### Search for Trees

```bash
# Search by name
curl "http://localhost:8000/api/species/search?query=oak&limit=5"

# Search by hardiness zone
curl "http://localhost:8000/api/species/search?hardiness_zone=10"

# Get specific species
curl "http://localhost:8000/api/species/PLOC"
```

### Calculate Environmental Benefits

```bash
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Calculate the environmental benefits of planting 1 American Sycamore for 20 years"
  }'
```

---

## 🔧 Troubleshooting

### "Connection Refused" Error

**Problem:** Database not running

**Fix:**
```bash
# Start Docker Desktop
# Wait ~30 seconds
docker compose up -d postgres redis
```

### "Module Not Found" Error

**Problem:** Virtual environment not activated

**Fix:**
```bash
source venv/bin/activate
```

### "Port 8000 Already in Use"

**Problem:** Another server is running

**Fix:**
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn api.main:app --port 8001
```

### Agent Has No Tools

**Problem:** Database not running (agent works in conversation-only mode)

**Result:** Agent can chat but can't calculate benefits, recommend species, etc.

**Fix:** Start database (see above)

---

## 📖 Available Endpoints

### Core
- `GET /api/health` - Health check
- `GET /` - API information

### Agent
- `POST /api/agent/chat` - Chat with AI agent
- `WS /api/agent/ws/{id}` - Real-time streaming chat

### Species Database
- `GET /api/species/search` - Search tree species
- `GET /api/species/{id}` - Get species details
- `GET /api/species/` - List all species

### Computer Vision
- `POST /api/cv/analyze` - Analyze an address (requires GEE)
- `GET /api/cv/analysis/{id}` - Get analysis results

### Site Data
- `GET /api/sites/{id}` - Get site details
- `POST /api/sites/{id}/photo` - Upload site photo
- `GET /api/sites/{id}/photos` - List site photos

---

## 📚 Full Documentation

- **API Reference**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Testing Guide**: [TESTING_GUIDE.md](TESTING_GUIDE.md)
- **Project Status**: [PROJECT_STATUS.md](PROJECT_STATUS.md)

---

## 🚀 Next Steps

1. **Test the Agent**: Send chat messages via `/api/agent/chat`
2. **Explore Species**: Search tree database via `/api/species/search`
3. **Run CV Analysis**: Analyze addresses via `/api/cv/analyze` (requires GEE setup)
4. **Build a Web UI**: Use the API endpoints to create a frontend

---

## 💡 Tips

- The API auto-reloads when code changes (in debug mode)
- Check logs for detailed error information
- Use Swagger UI at `/api/docs` to test endpoints interactively
- WebSocket endpoint provides real-time streaming for better UX
- All responses include CORS headers for web UI integration

---

**Ready to build? Start the API and visit http://localhost:8000/api/docs! 🌳**
