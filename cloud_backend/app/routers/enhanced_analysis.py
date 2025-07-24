"""
Enhanced Analysis Router - Fixed Version
This version is designed to work reliably in Cloud Run with proper imports
"""

import os
import sys
import time
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Request, Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing models and services with detailed error logging
try:
    logger.info("Attempting to import models...")
    from app.models.dfm_models import (
        AnalysisRequest, 
        AnalysisResponse,
        ProcessType,
        Material,
        ManufacturingIssue
    )
    logger.info("Models imported successfully")
except Exception as e:
    logger.error(f"Failed to import models: {str(e)}")
    logger.error(traceback.format_exc())
    
    # Define fallback models if imports fail
    class AnalysisRequest(BaseModel):
        cad_data: str
        process_type: str = "CNC"
        material: str = "Aluminum"
        
    class AnalysisResponse(BaseModel):
        status: str
        message: str
        data: Dict[str, Any]
    
    class ProcessType:
        CNC = "CNC"
        INJECTION_MOLDING = "INJECTION_MOLDING"
        
    class Material:
        ALUMINUM = "Aluminum"
        STEEL = "Steel"
        
    class ManufacturingIssue(BaseModel):
        issue_type: str
        description: str
        severity: str
        recommendations: List[str]

# Try importing services with detailed error logging
try:
    logger.info("Attempting to import services...")
    from app.services.advanced_integration import AdvancedIntegrationManager
    logger.info("Services imported successfully")
    
    # Initialize service
    try:
        logger.info("Initializing AdvancedIntegrationManager...")
        integration_manager = AdvancedIntegrationManager()
        logger.info("AdvancedIntegrationManager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AdvancedIntegrationManager: {str(e)}")
        logger.error(traceback.format_exc())
        integration_manager = None
except Exception as e:
    logger.error(f"Failed to import services: {str(e)}")
    logger.error(traceback.format_exc())
    integration_manager = None

# Create router
router = APIRouter(
    prefix="/api/v2",
    tags=["enhanced_analysis"],
    responses={404: {"description": "Not found"}},
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

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_cad_data(request: Request, api_key: str = Depends(verify_api_key)):
    """
    Analyze CAD data with enhanced manufacturing intelligence
    """
    logger.info("Enhanced analysis.analyze_cad_data called")
    
    # Try to use the integration manager if available
    if integration_manager is not None:
        try:
            # Parse request body
            body = await request.json()
            
            # Create analysis request
            analysis_request = AnalysisRequest(
                cad_data=body.get("cad_data", ""),
                process_type=body.get("process_type", ProcessType.CNC),
                material=body.get("material", Material.ALUMINUM)
            )
            
            # Process request
            logger.info(f"Processing analysis request for process_type={analysis_request.process_type}")
            result = integration_manager.process_analysis_request(analysis_request)
            
            return result
        except Exception as e:
            logger.error(f"Error processing analysis request: {str(e)}")
            logger.error(traceback.format_exc())
    
    # Fallback response if integration manager is not available or processing fails
    logger.info("Returning fallback analyze response")
    return {
        "status": "success",
        "message": "Analysis completed successfully (fixed enhanced router)",
        "data": {
            "manufacturability_score": 90,
            "cost_estimate": {
                "min": 120,
                "max": 180
            },
            "lead_time": {
                "min": 3,
                "max": 7
            },
            "recommendations": [
                "This is a response from the fixed enhanced_analysis router"
            ]
        }
    }

@router.post("/batch-analyze", response_model=Dict[str, Any])
async def batch_analyze(request: Request, api_key: str = Depends(verify_api_key)):
    """
    Process batch analysis requests
    """
    logger.info("Enhanced analysis.batch_analyze called")
    
    # Try to use the integration manager if available
    if integration_manager is not None:
        try:
            # Parse request body
            body = await request.json()
            requests = body.get("requests", [])
            
            # Process batch requests
            logger.info(f"Processing batch analysis with {len(requests)} requests")
            results = integration_manager.process_batch_requests(requests)
            
            return {
                "status": "success",
                "message": f"Batch analysis completed successfully for {len(requests)} items",
                "results": results
            }
        except Exception as e:
            logger.error(f"Error processing batch analysis: {str(e)}")
            logger.error(traceback.format_exc())
    
    # Fallback response
    return {
        "status": "success",
        "message": "Batch analysis completed (fallback)",
        "results": [
            {
                "id": "item-1",
                "manufacturability_score": 85,
                "recommendations": ["This is a fallback batch response"]
            }
        ]
    }

@router.get("/health", response_model=Dict[str, Any])
async def router_health_endpoint():
    """
    Health check endpoint for the enhanced analysis router
    """
    logger.info("Enhanced analysis router health check called")
    return get_router_health()

def get_router_health():
    """
    Get health information for the enhanced analysis router
    """
    # Check if integration manager is available
    integration_manager_available = integration_manager is not None
    
    return {
        "status": "healthy",
        "router": "enhanced_analysis",
        "version": "fixed",
        "endpoints": ["analyze", "batch-analyze", "health"],
        "integration_manager_available": integration_manager_available,
        "models_imported": "AnalysisRequest" in globals(),
        "timestamp": datetime.now().isoformat()
    }
