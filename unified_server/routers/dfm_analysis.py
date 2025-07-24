"""
DFM Analysis Router
Handles Design for Manufacturability analysis requests
"""

import logging
import time
import traceback
from fastapi import APIRouter, Depends, HTTPException, Security, Request
from fastapi.security import APIKeyHeader
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# Import DFM services
from services.dfm_engine import DFMEngine

# Configure logging
logger = logging.getLogger(__name__)

# API Key security
API_KEY = "test-api-key"  # In production, use environment variables
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Create router
router = APIRouter(
    prefix="/api/v2",
    tags=["dfm_analysis"],
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

# Initialize DFM engine
dfm_engine = DFMEngine()

# Request and response models
class UserRequirements(BaseModel):
    material: str = "PLA"
    target_process: str = "fdm_printing"
    production_volume: int = 100
    use_advanced_dfm: bool = True

class CADData(BaseModel):
    geometry: Dict[str, Any]
    features: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class DFMRequest(BaseModel):
    user_requirements: UserRequirements
    cad_data: CADData

class DFMResponse(BaseModel):
    manufacturability_score: float
    issues: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    cost_estimate: Dict[str, Any]
    lead_time: Dict[str, Any]

# DFM Analysis endpoint
@router.post("/analyze", response_model=DFMResponse)
async def analyze_design(request: DFMRequest, api_key: str = Depends(verify_api_key)):
    """
    Analyze a design for manufacturability
    """
    try:
        logger.info(f"Received DFM analysis request")
        
        # Extract request data
        user_requirements = request.user_requirements
        cad_data = request.cad_data
        
        # Log request details
        logger.info(f"Material: {user_requirements.material}")
        logger.info(f"Process: {user_requirements.target_process}")
        logger.info(f"Production volume: {user_requirements.production_volume}")
        logger.info(f"Use advanced DFM: {user_requirements.use_advanced_dfm}")
        
        # Perform DFM analysis
        start_time = time.time()
        result = dfm_engine.analyze(
            cad_data=cad_data.dict(),
            material=user_requirements.material,
            process=user_requirements.target_process,
            production_volume=user_requirements.production_volume,
            use_advanced=user_requirements.use_advanced_dfm
        )
        elapsed_time = time.time() - start_time
        
        logger.info(f"DFM analysis completed in {elapsed_time:.2f} seconds")
        logger.info(f"Manufacturability score: {result['manufacturability_score']}")
        
        return result
    except Exception as e:
        logger.error(f"Error in DFM analysis: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
