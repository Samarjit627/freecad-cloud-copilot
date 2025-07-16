"""
Analysis router for FreeCAD Manufacturing Co-Pilot API
Handles CAD analysis and manufacturing recommendations
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

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
async def analyze_cad(request: AnalysisRequest):
    """
    Analyze CAD data and provide manufacturing recommendations
    """
    try:
        # Generate analysis ID
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Extract CAD data
        cad_data = request.cad_data
        user_requirements = request.user_requirements or {}
        
        # Perform analysis
        analysis_result = perform_cad_analysis(cad_data, user_requirements)
        
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
            timestamp=datetime.now().isoformat()
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
    
    This is a simplified version that would normally contain complex analysis logic.
    In a real implementation, this would analyze the CAD geometry in detail.
    """
    # Extract basic dimensions
    dimensions = cad_data.get("dimensions", {})
    
    # Calculate complexity based on features
    features = cad_data.get("features", {})
    complexity_rating = calculate_complexity_rating(features)
    
    # Calculate moldability score
    moldability_score = calculate_moldability_score(features, dimensions)
    
    # Prepare manufacturing features
    manufacturing_features = {
        "holes": features.get("holes", 0),
        "ribs": features.get("ribs", 0),
        "undercuts": features.get("undercuts", 0),
        "thin_walls": features.get("thin_walls", 0),
        "sharp_corners": features.get("sharp_corners", 0),
        "complexity_rating": complexity_rating,
        "moldability_score": moldability_score,
        "manufacturability_index": int(moldability_score * 10),
    }
    
    # Generate material suggestions
    material_suggestions = suggest_materials(dimensions, manufacturing_features, user_requirements)
    
    # Generate process recommendations
    process_recommendations = recommend_processes(dimensions, manufacturing_features, user_requirements)
    
    # Identify design issues
    design_issues = identify_design_issues(dimensions, manufacturing_features)
    
    return {
        "dimensions": dimensions,
        "manufacturing_features": manufacturing_features,
        "material_suggestions": material_suggestions,
        "process_recommendations": process_recommendations,
        "design_issues": design_issues,
        "timestamp": datetime.now().isoformat()
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
