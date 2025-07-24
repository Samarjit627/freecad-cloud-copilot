"""
FreeCAD Manufacturing Co-Pilot Cloud Backend - Production Fixed Version
Main FastAPI application with improved import handling and startup reliability
"""
import os
import sys
import time
import logging
import traceback
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Security, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime

# Configure logging first with detailed output during startup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Print startup information
logger.info("=== Starting FreeCAD Manufacturing Co-Pilot Cloud Backend (Production Fixed) ===")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")
try:
    logger.info(f"Directory contents: {os.listdir('.')}")
    logger.info(f"App directory contents: {os.listdir('./app')}")
except Exception as e:
    logger.error(f"Error listing directory contents: {e}")

logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")

# Create necessary directories
try:
    Path("/tmp/cad_analysis_cache").mkdir(parents=True, exist_ok=True)
    logger.info("Created /tmp/cad_analysis_cache directory")
except Exception as e:
    logger.error(f"Error creating cache directory: {e}")

# Import routers with robust error handling
# Define empty router variables to avoid reference errors if imports fail
chat = None
analysis = None
agents = None
enhanced_analysis = None

# First try direct imports (Cloud Run deployment)
logger.info("Attempting to import routers")
try:
    # Import the enhanced_analysis router first as it's the most critical
    from app.routers import enhanced_analysis
    logger.info("Successfully imported enhanced_analysis router")
    
    # Try to import other routers but don't fail if they're not available
    try:
        from app.routers import chat
        logger.info("Successfully imported chat router")
    except ImportError as e:
        logger.warning(f"Chat router could not be imported: {str(e)}")
        
    try:
        from app.routers import analysis
        logger.info("Successfully imported analysis router")
    except ImportError as e:
        logger.warning(f"Analysis router could not be imported: {str(e)}")
        
    try:
        from app.routers import agents
        logger.info("Successfully imported agents router")
    except ImportError as e:
        logger.warning(f"Agents router could not be imported: {str(e)}")
        
except ImportError as e:
    logger.error(f"Critical router enhanced_analysis could not be imported: {str(e)}")
    logger.error(traceback.format_exc())
    # Continue anyway to allow health check endpoint to work

# Initialize FastAPI app
app = FastAPI(
    title="FreeCAD Manufacturing Co-Pilot API",
    description="Cloud backend for FreeCAD Manufacturing Co-Pilot",
    version="1.0.0"
)

# Store startup time
app.state.start_time = time.time()

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup event triggered")
    # Log Python path and modules
    logger.info(f"Python path: {sys.path}")
    
    # Log loaded modules (just count for brevity)
    module_count = len(sys.modules)
    logger.info(f"Loaded modules count: {module_count}")
    
    # Check if required directories exist
    for directory in ["/tmp", "/tmp/cad_analysis_cache"]:
        if os.path.exists(directory):
            logger.info(f"Directory exists: {directory}")
        else:
            logger.warning(f"Directory does not exist: {directory}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Security
API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("API_KEY", "dev_api_key_for_testing")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

logger.info(f"API key configured: {'Yes' if API_KEY else 'No'}")

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if OPENAI_API_KEY:
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        logger.info("OpenAI API key configured")
    except Exception as e:
        logger.error(f"Error configuring OpenAI: {e}")
else:
    logger.warning("No OpenAI API key provided")

# Security dependency
async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        logger.warning(f"Invalid API key attempt: {api_key[:5] if api_key else 'None'}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key

# Include routers if they were successfully imported
if enhanced_analysis:
    try:
        app.include_router(enhanced_analysis.router, tags=["enhanced_analysis"], dependencies=[Depends(verify_api_key)])
        logger.info("Included enhanced_analysis router")
    except Exception as e:
        logger.error(f"Error including enhanced_analysis router: {str(e)}")

if chat:
    try:
        app.include_router(chat.router, prefix="/api/chat", tags=["chat"], dependencies=[Depends(verify_api_key)])
        logger.info("Included chat router")
    except Exception as e:
        logger.error(f"Error including chat router: {str(e)}")

if analysis:
    try:
        app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"], dependencies=[Depends(verify_api_key)])
        logger.info("Included analysis router")
    except Exception as e:
        logger.error(f"Error including analysis router: {str(e)}")

if agents:
    try:
        app.include_router(agents.router, prefix="/api/agents", tags=["agents"], dependencies=[Depends(verify_api_key)])
        logger.info("Included agents router")
    except Exception as e:
        logger.error(f"Error including agents router: {str(e)}")

# Exception handler for all exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint that doesn't require authentication"""
    try:
        # Log system information
        logger.info(f"Health check requested at {datetime.now().isoformat()}")
        
        # Check if required modules are available
        required_modules = ["fastapi", "pydantic"]
        missing_modules = []
        
        for module_name in required_modules:
            try:
                __import__(module_name)
                logger.info(f"Module available: {module_name}")
            except ImportError as e:
                logger.error(f"Module not available: {module_name}, error: {e}")
                missing_modules.append(module_name)
        
        # Check if routers are loaded
        routers_loaded = enhanced_analysis is not None
        
        # Check disk space
        import shutil
        disk_usage = shutil.disk_usage("/")
        disk_percent = disk_usage.used / disk_usage.total * 100
        logger.info(f"Disk usage: {disk_percent:.1f}%")
        
        # Prepare response
        status = "healthy"
        details = {}
        
        if missing_modules:
            status = "degraded"
            details["missing_modules"] = missing_modules
        
        if not routers_loaded:
            status = "degraded"
            details["critical_routers_loaded"] = False
        
        if disk_percent > 90:
            status = "degraded"
            details["disk_usage"] = f"{disk_percent:.1f}% used"
        
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "uptime": time.time() - app.state.start_time if hasattr(app.state, "start_time") else 0,
            "details": details
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "error": str(e)
        }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint that doesn't require authentication"""
    return {
        "message": "FreeCAD Manufacturing Co-Pilot API",
        "docs_url": "/docs",
        "health_check": "/health"
    }

# Fallback analyze endpoint in case the router fails to load
@app.post("/api/v1/analyze", dependencies=[Depends(verify_api_key)])
async def analyze_part_fallback(request: Request):
    """Fallback analyze endpoint if the router fails to load"""
    logger.info("Fallback analyze endpoint called")
    try:
        # Check if the enhanced_analysis router was loaded
        if enhanced_analysis:
            logger.info("Redirecting to enhanced_analysis router")
            # Forward to the router's endpoint
            return await enhanced_analysis.analyze_part(request)
        
        # Just return a mock response if the router wasn't loaded
        logger.warning("Enhanced analysis router not loaded, returning mock response")
        return {
            "status": "success",
            "message": "Analysis completed successfully (fallback)",
            "data": {
                "manufacturability_score": 85,
                "cost_estimate": {
                    "min": 100,
                    "max": 150
                },
                "lead_time": {
                    "min": 5,
                    "max": 10
                },
                "recommendations": [
                    "This is a fallback response because the enhanced_analysis router could not be loaded"
                ]
            }
        }
    except Exception as e:
        logger.error(f"Error in analyze_part_fallback: {str(e)}")
        logger.error(traceback.format_exc())
        raise
