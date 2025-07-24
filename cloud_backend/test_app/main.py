import os
import sys
import time
import logging
import platform
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize app
app = FastAPI(
    title="FreeCAD Manufacturing Co-Pilot Test App",
    description="Minimal test app for Cloud Run deployment",
    version="1.0.0"
)

# Store startup time
app.state.start_time = time.time()

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Test application startup complete")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Current directory: {os.getcwd()}")

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "FreeCAD Manufacturing Co-Pilot Test App",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "uptime_seconds": time.time() - app.state.start_time,
        "environment": "cloud" if os.environ.get("K_SERVICE") else "local"
    }

@app.get("/debug")
async def debug_info():
    logger.info("Debug endpoint accessed")
    
    # Collect system information
    env_vars = {k: v for k, v in os.environ.items() 
               if not any(sensitive in k.lower() for sensitive in ["key", "secret", "password", "token"])}
    
    return {
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "environment": env_vars,
        "working_directory": os.getcwd(),
        "directory_contents": os.listdir('.')
    }

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )
