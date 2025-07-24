"""
API Key authentication for FreeCAD Manufacturing Co-Pilot Cloud Backend
"""
import os
from typing import Optional
from fastapi import Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

# API key header name
API_KEY_NAME = "X-API-Key"
API_KEY_HEADER = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Get API key from environment variable
API_KEY = os.environ.get("API_KEY", "")

async def get_api_key(api_key_header: str = Security(API_KEY_HEADER)) -> str:
    """
    Validate API key from request header
    
    Args:
        api_key_header: API key from request header
        
    Returns:
        API key if valid
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not API_KEY:
        # If no API key is set in environment, don't enforce authentication
        # This is useful for local development
        return "dev_mode"
        
    if api_key_header and api_key_header == API_KEY:
        return api_key_header
    
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail="Invalid or missing API key",
    )
