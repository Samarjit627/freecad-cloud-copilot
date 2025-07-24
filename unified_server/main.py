"""
FreeCAD Manufacturing Co-Pilot Unified Cloud Server
Combines DFM Analysis and Text-to-CAD features in a single server

This unified server:
- Provides DFM analysis capabilities from the original cloud backend
- Adds Text-to-CAD functionality for generating FreeCAD models from text descriptions
- Uses a common authentication mechanism
- Shares resources and dependencies
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FreeCAD Manufacturing Co-Pilot Unified API",
    description="Unified API for DFM Analysis and Text-to-CAD services",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key security
API_KEY = "test-api-key"  # In production, use environment variables
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Import routers
try:
    # Import DFM Analysis router
    from routers.dfm_analysis import router as dfm_router
    app.include_router(dfm_router)
    logger.info("DFM Analysis router loaded successfully")
except Exception as e:
    logger.error(f"Failed to load DFM Analysis router: {e}")
    logger.error(traceback.format_exc())

try:
    # Import Text-to-CAD router
    from routers.text_to_cad import router as text_to_cad_router
    app.include_router(text_to_cad_router)
    logger.info("Text-to-CAD router loaded successfully")
except Exception as e:
    logger.error(f"Failed to load Text-to-CAD router: {e}")
    logger.error(traceback.format_exc())

# Authentication dependency
async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "dfm_analysis": True,
            "text_to_cad": True
        }
    }

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "FreeCAD Manufacturing Co-Pilot Unified API",
        "version": "1.0.0",
        "services": [
            {
                "name": "DFM Analysis",
                "endpoint": "/api/v2/analyze",
                "description": "Design for Manufacturability Analysis"
            },
            {
                "name": "Text-to-CAD",
                "endpoint": "/api/v1/text-to-cad",
                "description": "Generate FreeCAD models from text descriptions"
            }
        ],
        "documentation": "/docs"
    }

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"Starting unified server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
