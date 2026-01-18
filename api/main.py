"""
SmartCanopy FastAPI Application
Main entry point for the API server
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from agent.config import settings
from api.routes import agent_routes, species_routes, site_routes, cv_routes

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 SmartCanopy API starting up...")
    logger.info(f"Environment: {'Development' if settings.debug else 'Production'}")
    logger.info(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")
    logger.info(f"Redis: {settings.redis_url}")

    yield

    logger.info("👋 SmartCanopy API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="SmartCanopy AI API",
    description="AI-powered urban tree planting recommendations using satellite imagery and environmental data",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS Middleware
allowed_origins = settings.allowed_origins.split(',') if settings.allowed_origins else [
    "http://localhost:3000",  # React dev server
    "http://localhost:8000",  # API docs
    "http://localhost:5173",  # Vite dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "status_code": exc.status_code
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error" if not settings.debug else str(exc),
                "status_code": 500
            }
        }
    )


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": "development" if settings.debug else "production"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "SmartCanopy AI API",
        "version": "1.0.0",
        "description": "AI-powered urban tree planting recommendations",
        "documentation": "/api/docs",
        "health_check": "/api/health"
    }


# Include routers
app.include_router(agent_routes.router, prefix="/api/agent", tags=["Agent"])
app.include_router(species_routes.router, prefix="/api/species", tags=["Species"])
app.include_router(site_routes.router, prefix="/api/sites", tags=["Sites"])
app.include_router(cv_routes.router, prefix="/api/cv", tags=["Computer Vision"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
