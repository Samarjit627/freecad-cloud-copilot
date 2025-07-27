"""
Text-to-CAD Router
Handles text-to-CAD requests for generating FreeCAD models from text descriptions
"""

import logging
import time
import traceback
from fastapi import APIRouter, Depends, HTTPException, Security, Request
from fastapi.security import APIKeyHeader
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Import Text-to-CAD services
from services.text_to_cad_engine import TextToCADEngine

# Configure logging
logger = logging.getLogger(__name__)

# API Key security
API_KEY = "test-api-key"  # In production, use environment variables
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Create router
router = APIRouter(
    prefix="/api/v1",
    tags=["text_to_cad"],
    responses={404: {"description": "Not found"}},
)

# Authentication dependency
async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key",
        )
    return api_key

# Initialize Text-to-CAD engine
text_to_cad_engine = TextToCADEngine()

# Request and response models
class TextToCADParameters(BaseModel):
    detail_level: str = "medium"
    output_format: str = "freecad_python"

class TextToCADRequest(BaseModel):
    prompt: str
    parameters: Optional[TextToCADParameters] = TextToCADParameters()

class TextToCADResponse(BaseModel):
    prompt: str
    engineering_analysis: str
    freecad_code: str
    metadata: Dict[str, Any]

# Text-to-CAD endpoint
@router.post("/text-to-cad", response_model=TextToCADResponse)
async def text_to_cad(request: TextToCADRequest, api_key: str = Depends(verify_api_key)):
    """
    Convert text description to FreeCAD model
    """
    try:
        logger.info(f"Received text-to-CAD request: {request.prompt[:50]}...")
        
        # Extract request data
        prompt = request.prompt
        parameters = request.parameters
        
        # Log request details
        logger.info(f"Detail level: {parameters.detail_level}")
        logger.info(f"Output format: {parameters.output_format}")
        
        # Generate engineering analysis
        start_time = time.time()
        engineering_analysis = text_to_cad_engine.generate_engineering_analysis(
            prompt=prompt,
            detail_level=parameters.detail_level
        )
        analysis_time = time.time() - start_time
        logger.info(f"Engineering analysis generated in {analysis_time:.2f}s")
        
        # Generate FreeCAD code
        start_time = time.time()
        freecad_code = text_to_cad_engine.generate_freecad_code(
            prompt=prompt,
            engineering_analysis=engineering_analysis
        )
        code_time = time.time() - start_time
        logger.info(f"FreeCAD code generated in {code_time:.2f}s")
        
        return {
            "prompt": prompt,
            "engineering_analysis": engineering_analysis,
            "freecad_code": freecad_code,
            "metadata": {
                "analysis_time_seconds": analysis_time,
                "code_generation_time_seconds": code_time,
                "total_time_seconds": analysis_time + code_time,
                "detail_level": parameters.detail_level
            }
        }
    except Exception as e:
        logger.error(f"Error in text-to-CAD: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
