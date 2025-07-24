"""
Analysis router for FreeCAD Manufacturing Co-Pilot API
Handles CAD analysis and manufacturing recommendations
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import random
import uuid

# Import required components
from ..auth.api_key import get_api_key
from ..services.dfm_engine import DFMEngine
from ..models.dfm_models import (
    DFMAnalysisRequest, DFMAnalysisResponse, 
    CADGeometry, ProcessType, MaterialType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize DFM engine
dfm_engine = DFMEngine()

# Initialize router
router = APIRouter()

@router.post("/dfm", response_model=DFMAnalysisResponse)
async def analyze_dfm(request: DFMAnalysisRequest, api_key: str = Depends(get_api_key)):
    """
    Perform advanced industry-grade DFM analysis
    
    This endpoint provides comprehensive Design for Manufacturing analysis including:
    - Geometric analysis for manufacturability
    - Manufacturing process suitability evaluation
    - Cost analysis breakdown
    - Expert recommendations
    """
    try:
        # Log analysis request
        logger.info(f"Received DFM analysis request for process: {request.target_process}")
        
        # Perform DFM analysis using the industry-grade engine
        analysis_result = dfm_engine.analyze(request)
        
        # Return the analysis response
        return analysis_result
        
    except Exception as e:
        logger.error(f"DFM analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Models
class AnalysisRequest(BaseModel):
    cad_data: Dict[str, Any]
    user_requirements: Optional[Dict[str, Any]] = None

class AnalysisResponse(BaseModel):
    analysis_id: str
    dimensions: Dict[str, Any]
    manufacturing_features: Dict[str, Any]
    material_suggestions: List[str]
    process_recommendations: List[str]
    design_issues: List[str]
    timestamp: str

# In-memory analysis store (replace with database in production)
analysis_results = {}

@router.post("/cad", response_model=AnalysisResponse)
async def analyze_cad(request: AnalysisRequest, api_key: str = Depends(get_api_key)):
    """
    Analyze CAD data and provide manufacturing recommendations
    
    This endpoint now leverages the industry-grade DFM engine for enhanced analysis
    while maintaining backward compatibility with existing clients.
    """
    try:
        # Generate analysis ID
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Extract CAD data
        cad_data = request.cad_data
        user_requirements = request.user_requirements or {}
        
        # Log analysis request
        logger.info(f"Received CAD analysis request with {len(cad_data)} data points")
        
        # Perform analysis
        analysis_result = perform_cad_analysis(cad_data, user_requirements)
        
        # Add timestamp
        analysis_result["timestamp"] = datetime.now().isoformat()
        
        # Store analysis
        analysis_results[analysis_id] = analysis_result
        
        # Return response
        return AnalysisResponse(
            analysis_id=analysis_id,
            dimensions=analysis_result["dimensions"],
            manufacturing_features=analysis_result["manufacturing_features"],
            material_suggestions=analysis_result["material_suggestions"],
            process_recommendations=analysis_result["process_recommendations"],
            design_issues=analysis_result["design_issues"],
            timestamp=analysis_result["timestamp"]
        )
    
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_result(analysis_id: str):
    """
    Get analysis result by ID
    """
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = analysis_results[analysis_id]
    
    return AnalysisResponse(
        analysis_id=analysis_id,
        dimensions=result["dimensions"],
        manufacturing_features=result["manufacturing_features"],
        material_suggestions=result["material_suggestions"],
        process_recommendations=result["process_recommendations"],
        design_issues=result["design_issues"],
        timestamp=result.get("timestamp", datetime.now().isoformat())
    )

def perform_cad_analysis(cad_data: Dict[str, Any], user_requirements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform CAD analysis and generate manufacturing recommendations
    
    This function now uses the industry-grade DFM engine for enhanced analysis,
    while maintaining backward compatibility with the existing API.
    """
    try:
        # Extract basic dimensions
        dimensions = cad_data.get("dimensions", {})
        
        # Extract features
        features = cad_data.get("features", {})
        
        # Determine if we should use the advanced DFM engine
        use_advanced_dfm = user_requirements.get("use_advanced_dfm", True)
        
        if use_advanced_dfm:
            # Convert the CAD data to the format expected by the DFM engine
            cad_geometry = {
                "volume": dimensions.get("volume", 0),
                "surface_area": dimensions.get("surface_area", 0),
                "bounding_box": {
                    "length": dimensions.get("length", 0),
                    "width": dimensions.get("width", 0),
                    "height": dimensions.get("height", 0)
                },
                "faces": features.get("faces", 0),
                "edges": features.get("edges", 0),
                "vertices": features.get("vertices", 0),
                "holes": [
                    {"diameter": h.get("diameter", 0), 
                     "depth": h.get("depth", 0), 
                     "location": h.get("location", [0, 0, 0])}
                    for h in features.get("holes_data", [])
                ],
                "thin_walls": [
                    {"thickness": w.get("thickness", 0), 
                     "location": w.get("location", [0, 0, 0])}
                    for w in features.get("walls_data", [])
                ]
            }
            
            # Determine target process and material
            target_process_str = user_requirements.get("target_process", "INJECTION_MOLDING")
            material_str = user_requirements.get("material", "ABS")
            
            # Convert string to enum
            try:
                target_process = ProcessType(target_process_str)
            except ValueError:
                target_process = ProcessType.INJECTION_MOLDING
                
            try:
                material = MaterialType(material_str)
            except ValueError:
                material = MaterialType.ABS
            
            # Create DFM analysis request
            dfm_request = DFMAnalysisRequest(
                cad_geometry=cad_geometry,
                target_process=target_process,
                material=material,
                production_volume=user_requirements.get("production_volume", 1000),
                include_cost_analysis=True,
                include_alternative_processes=True
            )
            
            # Perform advanced DFM analysis
            dfm_result = dfm_engine.analyze(dfm_request)
            
            # Convert DFM result to the format expected by the existing API
            complexity_rating = "Medium"
            if dfm_result.overall_manufacturability_score < 50:
                complexity_rating = "High"
            elif dfm_result.overall_manufacturability_score > 75:
                complexity_rating = "Low"
            
            # Prepare manufacturing features
            manufacturing_features = {
                "holes": features.get("holes", 0),
                "ribs": features.get("ribs", 0),
                "bosses": features.get("bosses", 0),
                "undercuts": features.get("undercuts", 0),
                "sharp_corners": features.get("sharp_corners", 0),
                "complexity_rating": complexity_rating,
                "moldability_score": dfm_result.overall_manufacturability_score / 10,  # Convert to 0-10 scale
                "dfm_analysis_id": dfm_result.analysis_id  # Store reference to full DFM analysis
            }
            
            # Extract material suggestions from DFM result
            material_suggestions = []
            if dfm_result.alternative_processes:
                # Get materials compatible with recommended processes
                for process in dfm_result.alternative_processes:
                    if process.process == ProcessType.INJECTION_MOLDING:
                        material_suggestions.extend(["ABS", "Polypropylene", "Nylon"])
                    elif process.process == ProcessType.CNC_MILLING:
                        material_suggestions.extend(["Aluminum", "Steel", "Brass"])
                    elif process.process == ProcessType.FDM_PRINTING:
                        material_suggestions.extend(["PLA", "ABS", "PETG"])
            
            # Deduplicate material suggestions
            material_suggestions = list(dict.fromkeys(material_suggestions))[:3]
            
            # Extract process recommendations from DFM result
            process_recommendations = []
            if dfm_result.primary_process:
                process_recommendations.append(dfm_result.primary_process.process.value)
            if dfm_result.alternative_processes:
                for process in dfm_result.alternative_processes:
                    process_recommendations.append(process.process.value)
            
            # Extract design issues from DFM result
            design_issues = []
            for issue in dfm_result.critical_issues:
                design_issues.append(f"{issue.title}: {issue.description}")
            for issue in dfm_result.manufacturing_issues[:5]:  # Limit to top 5 non-critical issues
                design_issues.append(f"{issue.title}: {issue.description}")
            
        else:
            # Fall back to the original simplified analysis
            complexity_rating = calculate_complexity_rating(features)
            moldability_score = calculate_moldability_score(features, dimensions)
            
            # Prepare manufacturing features
            manufacturing_features = {
                "holes": features.get("holes", 0),
                "ribs": features.get("ribs", 0),
                "bosses": features.get("bosses", 0),
                "undercuts": features.get("undercuts", 0),
                "sharp_corners": features.get("sharp_corners", 0),
                "complexity_rating": complexity_rating,
                "moldability_score": moldability_score
            }
            
            # Generate material suggestions
            material_suggestions = suggest_materials(dimensions, manufacturing_features, user_requirements)
            
            # Generate process recommendations
            process_recommendations = recommend_processes(dimensions, manufacturing_features, user_requirements)
            
            # Identify design issues
            design_issues = identify_design_issues(dimensions, manufacturing_features)
        
        # Prepare analysis result
        result = {
            "dimensions": dimensions,
            "manufacturing_features": manufacturing_features,
            "material_suggestions": material_suggestions,
            "process_recommendations": process_recommendations,
            "design_issues": design_issues
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in perform_cad_analysis: {e}")
        # Fall back to simplified analysis on error
        return {
            "dimensions": cad_data.get("dimensions", {}),
            "manufacturing_features": {
                "complexity_rating": "Medium",
                "moldability_score": 5.0
            },
            "material_suggestions": ["ABS", "PLA", "Aluminum"],
            "process_recommendations": ["3D Printing", "CNC Machining"],
            "design_issues": ["Unable to perform detailed analysis"]
        }

def calculate_complexity_rating(features: Dict[str, Any]) -> str:
    """Calculate complexity rating based on features"""
    # Calculate complexity score
    score = 0
    score += features.get("holes", 0) * 3
    score += features.get("ribs", 0) * 1
    score += features.get("undercuts", 0) * 5
    score += features.get("thin_walls", 0) * 4
    score += features.get("sharp_corners", 0) * 0.5
    
    # Convert score to rating
    if score < 15:
        return "Low"
    elif score < 35:
        return "Medium"
    elif score < 60:
        return "High"
    else:
        return "Very High"

def calculate_moldability_score(features: Dict[str, Any], dimensions: Dict[str, Any]) -> float:
    """Calculate moldability score (1-10, 10 = most moldable)"""
    score = 10.0
    
    # Deduct for problematic features
    score -= features.get("undercuts", 0) * 1.5
    score -= features.get("thin_walls", 0) * 0.8
    score -= features.get("sharp_corners", 0) * 0.02
    score -= features.get("holes", 0) * 0.3
    
    # Check wall thickness
    if dimensions.get("thickness", 5) < 1.5:
        score -= 2.0
    
    # Check aspect ratio
    aspect_ratio = max(dimensions.get("length", 1), dimensions.get("width", 1)) / max(1, min(dimensions.get("length", 1), dimensions.get("width", 1)))
    if aspect_ratio > 10:
        score -= 1.5
    
    return max(1.0, round(score, 1))

def suggest_materials(dimensions: Dict[str, Any], features: Dict[str, Any], requirements: Dict[str, Any]) -> List[str]:
    """Suggest appropriate materials"""
    suggestions = []
    
    # Based on size
    max_dim = max(dimensions.get("length", 0), dimensions.get("width", 0), dimensions.get("height", 0))
    
    if max_dim > 500:
        suggestions.extend(["Steel", "Aluminum", "Glass Fiber Reinforced Plastic"])
    elif max_dim > 100:
        suggestions.extend(["ABS", "Polypropylene", "Nylon", "Aluminum"])
    else:
        suggestions.extend(["ABS", "PLA", "Polypropylene"])
    
    # Based on complexity
    if features.get("complexity_rating") == "Very High":
        suggestions = ["ABS", "Polypropylene"]  # More forgiving materials
    
    # Based on application
    application = requirements.get("application", "")
    if "Automotive" in application:
        suggestions.extend(["Nylon", "ABS", "Steel"])
    elif "Electronics" in application:
        suggestions.extend(["ABS", "Polypropylene", "Aluminum"])
    elif "Medical" in application:
        suggestions.extend(["Nylon", "Steel", "ABS"])
    
    # Remove duplicates and limit to top 3
    return list(dict.fromkeys(suggestions))[:3]

def recommend_processes(dimensions: Dict[str, Any], features: Dict[str, Any], requirements: Dict[str, Any]) -> List[str]:
    """Recommend manufacturing processes"""
    recommendations = []
    
    # Extract key parameters
    complexity = features.get("complexity_rating", "Low")
    max_dim = max(dimensions.get("length", 0), dimensions.get("width", 0), dimensions.get("height", 0))
    volume = requirements.get("production_volume", "Prototype (1-10 pieces)")
    
    # Map volume string to approximate number
    volume_mapping = {
        "Prototype (1-10 pieces)": 5,
        "Pilot Production (10-100 pieces)": 50,
        "Small Batch (100-1,000 pieces)": 500,
        "Production (1,000-10,000 pieces)": 5000,
        "High Volume (10,000+ pieces)": 50000
    }
    volume_num = volume_mapping.get(volume, 5)
    
    # Process selection logic
    if volume_num < 50 and max_dim < 200:
        recommendations.append("3D Printing")
    
    if complexity in ["Low", "Medium"]:
        recommendations.append("CNC Machining")
    
    if volume_num > 1000 and features.get("moldability_score", 0) > 6:
        recommendations.append("Injection Molding")
    
    if dimensions.get("thickness", 0) < 5 and max_dim > 100:
        recommendations.append("Sheet Metal Forming")
    
    # Ensure we have at least one recommendation
    if not recommendations:
        recommendations.append("CNC Machining")
    
    return recommendations[:3]  # Return top 3

def identify_design_issues(dimensions: Dict[str, Any], features: Dict[str, Any]) -> List[str]:
    """Identify potential design issues"""
    issues = []
    
    # Check wall thickness
    if dimensions.get("thickness", 0) < 1.5:
        issues.append("Wall thickness too thin - minimum 1.5mm recommended")
    
    # Check aspect ratio
    aspect_ratio = max(dimensions.get("length", 1), dimensions.get("width", 1)) / max(1, min(dimensions.get("length", 1), dimensions.get("width", 1)))
    if aspect_ratio > 10:
        issues.append("High aspect ratio may cause warping")
    
    # Check undercuts
    if features.get("undercuts", 0) > 3:
        issues.append("Multiple undercuts detected - will increase tooling cost")
    
    # Check sharp corners
    if features.get("sharp_corners", 0) > 20:
        issues.append("Many sharp corners - consider adding fillets")
    
    # Check moldability
    if features.get("moldability_score", 10) < 6:
        issues.append("Low moldability score - design may be difficult to manufacture")
    
    return issues
