"""
FreeCAD Manufacturing Co-Pilot Cloud Backend
Main FastAPI application
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
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import openai
from datetime import datetime

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Print startup information
logger.info("Starting FreeCAD Manufacturing Co-Pilot Cloud Backend")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")
logger.info(f"Directory contents: {os.listdir('.')}")

# Create necessary directories
Path("/tmp/cad_analysis_cache").mkdir(parents=True, exist_ok=True)
Path("/tmp").mkdir(parents=True, exist_ok=True)

# Import routers with fallback mechanisms
# In Cloud Run, we should use direct imports
logger.info("Attempting to import routers")

# Define empty router variables to avoid reference errors if imports fail
chat = None
analysis = None
agents = None
enhanced_analysis = None

# First try direct imports (Cloud Run deployment)
try:
    # Import the enhanced_analysis router first as it's the most critical
    from app.routers import enhanced_analysis
    logger.info("Successfully imported enhanced_analysis router")
    
    # Try to import other routers but don't fail if they're not available
    try:
        from app.routers import chat, analysis, agents
        logger.info("Successfully imported all routers directly from app")
    except ImportError as e:
        logger.warning(f"Some routers could not be imported: {str(e)}")
        
# If direct imports fail, try with cloud_backend prefix (local development)
except ImportError:
    try:
        # Import the enhanced_analysis router first
        from cloud_backend.app.routers import enhanced_analysis
        logger.info("Successfully imported enhanced_analysis router with cloud_backend prefix")
        
        # Try to import other routers
        try:
            from cloud_backend.app.routers import chat, analysis, agents
            logger.info("Successfully imported all routers with cloud_backend prefix")
        except ImportError as e:
            logger.warning(f"Some routers could not be imported: {str(e)}")
            
    # Last resort - try relative imports
    except ImportError:
        try:
            from .routers import enhanced_analysis
            logger.info("Successfully imported enhanced_analysis router with relative imports")
            
            try:
                from .routers import chat, analysis, agents
                logger.info("Successfully imported all routers with relative imports")
            except ImportError as e:
                logger.warning(f"Some routers could not be imported: {str(e)}")
                
        except ImportError as e:
            logger.error(f"Failed to import any routers: {str(e)}")
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
    logger.info("Application startup complete")
    # Log Python path and modules
    logger.info(f"Python path: {sys.path}")
    logger.info(f"Loaded modules: {list(sys.modules.keys())}")
    
    # Check if required directories exist
    for directory in ["/tmp", "/tmp/cad_analysis_cache"]:
        if os.path.exists(directory):
            logger.info(f"Directory exists: {directory}")
        else:
            logger.warning(f"Directory does not exist: {directory}")
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {str(e)}")
                
    # Log environment variables (excluding sensitive info)
    safe_env = {k: v for k, v in os.environ.items() 
                if not any(sensitive in k.lower() for sensitive in ["key", "secret", "password", "token"])}
    logger.info(f"Environment: {safe_env}")
    
    # Check if OpenAI API key is configured
    if os.getenv("OPENAI_API_KEY"):
        logger.info("OpenAI API key is configured")
    else:
        logger.warning("OpenAI API key is not configured")
        
    # Check if API key is configured
    if os.getenv("API_KEY"):
        logger.info("API key is configured")
    else:
        logger.warning("API key is not configured, using default")
        
    # Check if routers are loaded
    if hasattr(app, "routes"):
        logger.info(f"Loaded {len(app.routes)} routes")
    else:
        logger.warning("No routes loaded")
        
    logger.info("Startup checks completed successfully")

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

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if OPENAI_API_KEY:
    try:
        openai.api_key = OPENAI_API_KEY
        logger.info("OpenAI API key configured")
    except Exception as e:
        logger.error(f"Error configuring OpenAI: {e}")
else:
    logger.warning("No OpenAI API key provided")

# Security dependency
async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"], dependencies=[Depends(verify_api_key)])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"], dependencies=[Depends(verify_api_key)])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"], dependencies=[Depends(verify_api_key)])
app.include_router(enhanced_analysis.router, tags=["enhanced_analysis"], dependencies=[Depends(verify_api_key)])

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
        # Check if critical services are available
        import importlib
        import sys
        
        # Log system information
        logger.info(f"Health check requested at {datetime.now().isoformat()}")
        
        # Check if required modules are available
        required_modules = ["fastapi", "pydantic", "openai"]
        missing_modules = []
        
        for module_name in required_modules:
            if module_name not in sys.modules:
                try:
                    importlib.import_module(module_name)
                except ImportError:
                    missing_modules.append(module_name)
        
        # Check if routers are loaded
        routers_loaded = hasattr(app, "routes") and len(app.routes) > 0
        
        # Check disk space
        import shutil
        disk_usage = shutil.disk_usage("/")
        disk_percent = disk_usage.used / disk_usage.total * 100
        
        # Prepare response
        status = "healthy"
        details = {}
        
        if missing_modules:
            status = "degraded"
            details["missing_modules"] = missing_modules
        
        if not routers_loaded:
            status = "degraded"
            details["routers_loaded"] = False
        
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
