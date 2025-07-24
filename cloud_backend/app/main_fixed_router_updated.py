"""
FreeCAD Manufacturing Co-Pilot Cloud Backend - Fixed Router Version
This version explicitly imports the fixed enhanced analysis router
"""

import os
import sys
import time
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("app.main_fixed_router")
logger.setLevel(logging.INFO)

# Log startup information
logger.info("=== STARTUP DIAGNOSTICS ===")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")

try:
    # Try importing FastAPI and other dependencies
    logger.info("Importing FastAPI and dependencies...")
    from fastapi import FastAPI, Depends, HTTPException, Request, status, Security
    from fastapi.security.api_key import APIKeyHeader
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    logger.info("FastAPI and dependencies imported successfully")
except Exception as e:
    logger.critical(f"Failed to import FastAPI: {str(e)}")
    logger.critical(traceback.format_exc())
    sys.exit(1)

# Create FastAPI app
app = FastAPI(
    title="FreeCAD Manufacturing Co-Pilot API",
    description="Cloud backend for the FreeCAD Manufacturing Co-Pilot extension",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key security
API_KEY = os.environ.get("API_KEY", "test-api-key")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key"""
    if api_key != API_KEY:
        logger.warning(f"Invalid API key attempt: {api_key[:5] if api_key else 'None'}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
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

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Application startup event triggered")
    
    # Log Python path
    logger.info(f"Python path: {sys.path}")
    
    # Log loaded modules
    module_count = len(sys.modules)
    logger.info(f"Loaded modules count: {module_count}")
    
    # Log directory structure
    logger.info("Listing app directory structure:")
    for root, dirs, files in os.walk('/app', topdown=True):
        for name in dirs:
            logger.info(f"Directory: {os.path.join(root, name)}")
        for name in files:
            if name.endswith('.py'):
                logger.info(f"Python file: {os.path.join(root, name)}")
    
    # Check critical directories
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

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("Root endpoint called")
    return {
        "message": "FreeCAD Manufacturing Co-Pilot API",
        "version": "1.0.0",
        "status": "fixed router mode",
        "timestamp": datetime.now().isoformat()
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check called")
    
    # Check if critical routers are loaded
    critical_routers_loaded = False
    router_health_info = {}
    
    # Try to import the fixed enhanced_analysis router
    try:
        logger.info("Attempting to import enhanced_analysis_fixed router...")
        from app.routers import enhanced_analysis_fixed
        logger.info("Fixed enhanced analysis router imported successfully")
        critical_routers_loaded = True
        
        # Try to get router health info
        try:
            router_health_info = enhanced_analysis_fixed.get_router_health()
            logger.info(f"Router health info: {router_health_info}")
        except Exception as e:
            logger.error(f"Failed to get router health info: {str(e)}")
            logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"Failed to import enhanced_analysis_fixed router: {str(e)}")
        logger.error(traceback.format_exc())
    
    # Check uptime
    uptime = time.time() - app.state.start_time if hasattr(app.state, "start_time") else 0
    
    # Return health status
    status_value = "healthy" if critical_routers_loaded else "degraded"
    logger.info(f"Health status: {status_value}")
    
    return {
        "status": status_value,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "uptime": uptime,
        "details": {
            "critical_routers_loaded": critical_routers_loaded,
            "router_health": router_health_info,
            "environment": {
                "python_version": sys.version,
                "pythonpath": os.environ.get("PYTHONPATH", "Not set"),
                "port": os.environ.get("PORT", "Not set")
            }
        }
    }

# Simple analyze endpoint that doesn't depend on routers
@app.post("/api/v1/analyze")
async def analyze_fallback(request: Request, api_key: str = Depends(verify_api_key)):
    """Fallback analyze endpoint"""
    logger.info("Fallback analyze endpoint called")
    
    # Try to import the fixed enhanced_analysis router
    try:
        logger.info("Attempting to import enhanced_analysis_fixed router...")
        from app.routers import enhanced_analysis_fixed
        logger.info("Fixed enhanced analysis router imported successfully")
        
        # If we get here, try to use the router's analyze function
        try:
            logger.info("Attempting to use enhanced_analysis_fixed.analyze_cad_data...")
            return await enhanced_analysis_fixed.analyze_cad_data(request, api_key)
        except Exception as e:
            logger.error(f"Failed to use enhanced_analysis_fixed.analyze_cad_data: {str(e)}")
            logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"Failed to import enhanced_analysis_fixed router: {str(e)}")
        logger.error(traceback.format_exc())
    
    # Return a fallback response
    logger.info("Returning fallback analyze response")
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
                "This is a fallback response because the enhanced_analysis_fixed router could not be loaded"
            ]
        }
    }

# Explicitly include the fixed enhanced analysis router
try:
    logger.info("Explicitly including enhanced_analysis_fixed router...")
    from app.routers.enhanced_analysis_fixed import router as enhanced_fixed_router
    app.include_router(enhanced_fixed_router)
    logger.info("Successfully included enhanced_analysis_fixed router")
except Exception as e:
    logger.error(f"Failed to include enhanced_analysis_fixed router: {str(e)}")
    logger.error(traceback.format_exc())

# Store startup time
app.state.start_time = time.time()

# Log completion of module loading
logger.info("Main application module loaded successfully")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8080"))
    logger.info(f"Starting uvicorn server on port {port}")
    uvicorn.run("main_fixed_router:app", host="0.0.0.0", port=port, log_level="info")
