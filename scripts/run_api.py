#!/usr/bin/env python3
"""
Run SmartCanopy FastAPI Server
Convenience script to start the API with proper settings
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if __name__ == "__main__":
    import uvicorn
    from agent.config import settings

    print("\n" + "="*80)
    print("🌳 SmartCanopy API Server")
    print("="*80)
    print(f"\nEnvironment: {'Development' if settings.debug else 'Production'}")
    print(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")
    print(f"Redis: {settings.redis_url}")
    print(f"Log Level: {settings.log_level}")
    print("\nStarting server...")
    print("="*80)
    print("\n📖 API Documentation:")
    print("  • Swagger UI: http://localhost:8000/api/docs")
    print("  • ReDoc: http://localhost:8000/api/redoc")
    print("  • Health Check: http://localhost:8000/api/health")
    print("\n🔌 Endpoints:")
    print("  • POST /api/agent/chat - Chat with AI agent")
    print("  • WS /api/agent/ws/{id} - Real-time streaming chat")
    print("  • GET /api/species/search - Search tree species")
    print("  • POST /api/cv/analyze - Run CV model analysis")
    print("  • GET /api/sites/{id} - Get planting site details")
    print("\n⌨️  Press CTRL+C to stop the server")
    print("="*80 + "\n")

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
