"""
Local Transcript App - FastAPI Backend

A local-only transcription service that processes audio/video files
and YouTube URLs without cloud dependencies.

Features:
- File upload with validation
- YouTube caption extraction (Safe Mode)
- YouTube auto-ingest (Auto Mode, opt-in)
- Transcript viewing and editing
- Export to TXT, SRT, VTT, JSON
"""
import logging
import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import database as db
from models import ErrorResponse, HealthResponse
from routes import export, jobs, upload, youtube

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Local Transcript API...")
    await db.init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Local Transcript API...")


# Create FastAPI app
app = FastAPI(
    title="Local Transcript API",
    description=__doc__,
    version="1.5.0",
    lifespan=lifespan,
)

# CORS configuration
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----- Global Exception Handler -----

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# ----- Health Check -----

@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        service="local-transcript-api",
        version="1.5.0",
    )


@app.get("/api/health", response_model=HealthResponse, tags=["system"])
async def api_health_check():
    """API health check endpoint (prefixed)"""
    return await health_check()


# ----- Include Routers -----

app.include_router(upload.router)
app.include_router(jobs.router)
app.include_router(youtube.router)
app.include_router(export.router)


# ----- Root Endpoint -----

@app.get("/", tags=["system"])
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Local Transcript API",
        "version": "1.5.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "upload": "POST /api/upload",
            "youtube": "POST /api/youtube",
            "jobs": "GET /api/jobs",
            "job_detail": "GET /api/jobs/{id}",
            "transcript": "GET /api/jobs/{id}/transcript",
            "save_transcript": "POST /api/jobs/{id}/transcript",
            "export": "GET /api/jobs/{id}/export?fmt=txt|srt|vtt|json",
        },
        "features": {
            "youtube_auto_ingest": os.getenv("YOUTUBE_AUTO_INGEST", "false").lower() == "true",
        },
    }


# ----- Development Server -----

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8765")),
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
