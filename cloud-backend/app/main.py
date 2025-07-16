"""
FreeCAD Manufacturing Co-Pilot Cloud Backend
Main FastAPI application
"""
import os
import logging
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import openai
from datetime import datetime

from app.routers import chat, analysis, agents

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FreeCAD Manufacturing Co-Pilot API",
    description="Cloud backend for FreeCAD Manufacturing Co-Pilot",
    version="1.0.0"
)

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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint that doesn't require authentication"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
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
