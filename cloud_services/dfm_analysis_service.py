#!/usr/bin/env python3
"""
Cloud DFM Analysis Service
Lightweight, fast DFM analysis service for Google Cloud Run
Extracted from StandaloneCoPilot.FCMacro for better performance
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import time
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cloud DFM Analysis Service",
    description="High-performance DFM analysis for FreeCAD Manufacturing Co-Pilot",
    version="1.0.0"
)

# CORS middleware for FreeCAD macro access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class GeometryData(BaseModel):
    """CAD geometry data from FreeCAD"""
    volume: float
    surface_area: float
    bounding_box: Dict[str, float]
    facet_count: Optional[int] = 0
    object_type: str = "mesh"  # "mesh", "solid", "compound"
    complexity_score: Optional[float] = 0.0

class ProcessData(BaseModel):
    """Manufacturing process parameters"""
    process: str  # "injection_molding", "3d_printing", "cnc_machining"
    material: str
    quantity: int
    min_feature_size: Optional[float] = 1.0
    tolerance: Optional[float] = 0.1

class DFMAnalysisRequest(BaseModel):
    """Complete DFM analysis request"""
    geometry: GeometryData
    process: ProcessData
    analysis_type: str = "comprehensive"  # "basic", "comprehensive", "heatmap_only"

class DFMIssue(BaseModel):
    """Individual DFM issue"""
    issue_type: str
    severity: str  # "critical", "minor"
    location: Dict[str, float]
    description: str
    recommendation: str
    cost_impact: Optional[float] = 0.0

class DFMAnalysisResponse(BaseModel):
    """DFM analysis results"""
    analysis_id: str
    timestamp: str
    geometry_summary: Dict[str, Any]
    detected_issues: List[DFMIssue]
    cost_analysis: Dict[str, float]
    manufacturability_score: float
    recommendations: List[str]
    processing_time_ms: int

class HeatmapData(BaseModel):
    """Heatmap overlay data"""
    issue_locations: List[Dict[str, Any]]
    color_mapping: Dict[str, List[float]]
    severity_zones: List[Dict[str, Any]]

# Core DFM Analysis Functions (Extracted from Macro)
class CloudDFMAnalyzer:
    """High-performance cloud DFM analyzer"""
    
    def __init__(self):
        self.indian_material_costs = {
            "abs_plastic": 120.0,  # ₹ per kg
            "pla_plastic": 80.0,
            "aluminum": 250.0,
            "steel": 180.0,
            "stainless_steel": 350.0
        }
        
        self.process_costs = {
            "injection_molding": {"setup": 15000, "per_part": 8},
            "3d_printing": {"setup": 0, "per_part": 25},
            "cnc_machining": {"setup": 2500, "per_part": 45}
        }
    
    def analyze_geometry(self, geometry: GeometryData) -> Dict[str, Any]:
        """Analyze CAD geometry for manufacturability issues"""
        start_time = time.time()
        
        # Extract key dimensions
        bbox = geometry.bounding_box
        x_size = bbox.get('x_length', 0)
        y_size = bbox.get('y_length', 0) 
        z_size = bbox.get('z_length', 0)
        
        # Calculate complexity metrics
        complexity_score = self._calculate_complexity(geometry)
        
        # Geometry summary
        summary = {
            "dimensions": {"x": x_size, "y": y_size, "z": z_size},
            "volume": geometry.volume,
            "surface_area": geometry.surface_area,
            "complexity_score": complexity_score,
            "facet_count": geometry.facet_count,
            "object_type": geometry.object_type
        }
        
        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Geometry analysis completed in {processing_time:.1f}ms")
        
        return summary
    
    def detect_issues(self, geometry: GeometryData, process: ProcessData) -> List[DFMIssue]:
        """Detect manufacturing issues based on geometry and process"""
        issues = []
        
        # Process-specific issue detection
        if process.process == "injection_molding":
            issues.extend(self._detect_injection_molding_issues(geometry, process))
        elif process.process == "3d_printing":
            issues.extend(self._detect_3d_printing_issues(geometry, process))
        elif process.process == "cnc_machining":
            issues.extend(self._detect_cnc_issues(geometry, process))
        
        return issues
    
    def _detect_injection_molding_issues(self, geometry: GeometryData, process: ProcessData) -> List[DFMIssue]:
        """Detect injection molding specific issues"""
        issues = []
        bbox = geometry.bounding_box
        
        # Thin wall detection (simplified for cloud)
        estimated_wall_thickness = min(
            bbox.get('x_length', 10) / 10,
            bbox.get('y_length', 10) / 10
        )
        
        if estimated_wall_thickness < 2.0:
            issues.append(DFMIssue(
                issue_type="thin_wall",
                severity="critical",
                location={"x": bbox.get('x_center', 0), "y": bbox.get('y_center', 0), "z": bbox.get('z_center', 0)},
                description=f"Wall thickness {estimated_wall_thickness:.1f}mm below 2mm minimum",
                recommendation="Increase wall thickness to 2-3mm for injection molding",
                cost_impact=500.0
            ))
        
        # Sharp corner detection
        if geometry.complexity_score > 0.7:
            issues.append(DFMIssue(
                issue_type="sharp_corner",
                severity="minor",
                location={"x": bbox.get('x_max', 0), "y": bbox.get('y_max', 0), "z": bbox.get('z_min', 0)},
                description="Sharp corners detected - may cause stress concentration",
                recommendation="Add 0.5mm radius to sharp corners",
                cost_impact=200.0
            ))
        
        return issues
    
    def _detect_3d_printing_issues(self, geometry: GeometryData, process: ProcessData) -> List[DFMIssue]:
        """Detect 3D printing specific issues"""
        issues = []
        bbox = geometry.bounding_box
        
        # Overhang detection (simplified)
        z_height = bbox.get('z_length', 0)
        if z_height > 50:
            issues.append(DFMIssue(
                issue_type="overhang",
                severity="minor",
                location={"x": bbox.get('x_center', 0), "y": bbox.get('y_center', 0), "z": bbox.get('z_max', 0)},
                description="Tall geometry may require support structures",
                recommendation="Add support structures or reorient part",
                cost_impact=100.0
            ))
        
        return issues
    
    def _detect_cnc_issues(self, geometry: GeometryData, process: ProcessData) -> List[DFMIssue]:
        """Detect CNC machining specific issues"""
        issues = []
        bbox = geometry.bounding_box
        
        # Tool access issues (simplified)
        if geometry.complexity_score > 0.8:
            issues.append(DFMIssue(
                issue_type="tool_access",
                severity="critical",
                location={"x": bbox.get('x_center', 0), "y": bbox.get('y_center', 0), "z": bbox.get('z_center', 0)},
                description="Complex geometry may limit tool access",
                recommendation="Simplify internal features or use multiple setups",
                cost_impact=800.0
            ))
        
        return issues
    
    def calculate_costs(self, geometry: GeometryData, process: ProcessData, issues: List[DFMIssue]) -> Dict[str, float]:
        """Calculate Indian market manufacturing costs"""
        
        # Material cost calculation
        volume_cm3 = geometry.volume / 1000  # Convert mm³ to cm³
        density = 1.2  # Approximate density for plastics (g/cm³)
        weight_kg = (volume_cm3 * density) / 1000
        
        material_cost_per_kg = self.indian_material_costs.get(process.material, 150.0)
        material_cost = weight_kg * material_cost_per_kg
        
        # Process cost calculation
        process_data = self.process_costs.get(process.process, {"setup": 1000, "per_part": 20})
        setup_cost = process_data["setup"] / process.quantity  # Amortized setup cost
        processing_cost = process_data["per_part"]
        
        # Issue-based cost penalties
        issue_cost = sum(issue.cost_impact or 0 for issue in issues)
        
        total_cost = material_cost + setup_cost + processing_cost + issue_cost
        
        return {
            "material_cost_inr": round(material_cost, 2),
            "setup_cost_inr": round(setup_cost, 2),
            "processing_cost_inr": round(processing_cost, 2),
            "issue_penalty_inr": round(issue_cost, 2),
            "total_cost_inr": round(total_cost, 2),
            "cost_per_unit_inr": round(total_cost, 2)
        }
    
    def generate_heatmap_data(self, issues: List[DFMIssue]) -> HeatmapData:
        """Generate heatmap overlay data for FreeCAD visualization"""
        
        issue_locations = []
        for issue in issues:
            issue_locations.append({
                "location": issue.location,
                "severity": issue.severity,
                "issue_type": issue.issue_type,
                "description": issue.description
            })
        
        color_mapping = {
            "critical": [1.0, 0.2, 0.2, 0.7],  # Bright red with transparency
            "minor": [1.0, 0.8, 0.2, 0.5]      # Yellow with transparency
        }
        
        severity_zones = [
            {
                "severity": "critical",
                "count": len([i for i in issues if i.severity == "critical"]),
                "color": color_mapping["critical"]
            },
            {
                "severity": "minor", 
                "count": len([i for i in issues if i.severity == "minor"]),
                "color": color_mapping["minor"]
            }
        ]
        
        return HeatmapData(
            issue_locations=issue_locations,
            color_mapping=color_mapping,
            severity_zones=severity_zones
        )
    
    def _calculate_complexity(self, geometry: GeometryData) -> float:
        """Calculate geometry complexity score (0.0 to 1.0)"""
        
        # Factors contributing to complexity
        facet_factor = min(geometry.facet_count / 5000, 1.0) if geometry.facet_count else 0.3
        
        bbox = geometry.bounding_box
        aspect_ratio = max(
            bbox.get('x_length', 1) / max(bbox.get('y_length', 1), 0.1),
            bbox.get('y_length', 1) / max(bbox.get('z_length', 1), 0.1)
        )
        aspect_factor = min(aspect_ratio / 10, 1.0)
        
        surface_to_volume = geometry.surface_area / max(geometry.volume, 1.0)
        surface_factor = min(surface_to_volume / 100, 1.0)
        
        # Weighted complexity score
        complexity = (facet_factor * 0.4 + aspect_factor * 0.3 + surface_factor * 0.3)
        return min(complexity, 1.0)

# Initialize analyzer
analyzer = CloudDFMAnalyzer()

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Cloud DFM Analysis Service",
        "version": "1.0.0",
        "timestamp": time.time()
    }

@app.post("/api/dfm/analyze", response_model=DFMAnalysisResponse)
async def analyze_dfm(request: DFMAnalysisRequest):
    """Complete DFM analysis endpoint"""
    start_time = time.time()
    analysis_id = f"dfm_{int(time.time() * 1000)}"
    
    try:
        logger.info(f"Starting DFM analysis {analysis_id}")
        
        # Analyze geometry
        geometry_summary = analyzer.analyze_geometry(request.geometry)
        
        # Detect issues
        detected_issues = analyzer.detect_issues(request.geometry, request.process)
        
        # Calculate costs
        cost_analysis = analyzer.calculate_costs(request.geometry, request.process, detected_issues)
        
        # Calculate manufacturability score
        critical_issues = len([i for i in detected_issues if i.severity == "critical"])
        minor_issues = len([i for i in detected_issues if i.severity == "minor"])
        manufacturability_score = max(0.0, 1.0 - (critical_issues * 0.3 + minor_issues * 0.1))
        
        # Generate recommendations
        recommendations = []
        if critical_issues > 0:
            recommendations.append("Address critical issues before manufacturing")
        if minor_issues > 0:
            recommendations.append("Consider optimizing minor issues for cost reduction")
        if manufacturability_score > 0.8:
            recommendations.append("Geometry is well-suited for selected manufacturing process")
        
        processing_time = int((time.time() - start_time) * 1000)
        
        response = DFMAnalysisResponse(
            analysis_id=analysis_id,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            geometry_summary=geometry_summary,
            detected_issues=detected_issues,
            cost_analysis=cost_analysis,
            manufacturability_score=manufacturability_score,
            recommendations=recommendations,
            processing_time_ms=processing_time
        )
        
        logger.info(f"DFM analysis {analysis_id} completed in {processing_time}ms")
        return response
        
    except Exception as e:
        logger.error(f"DFM analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/dfm/heatmap", response_model=HeatmapData)
async def generate_heatmap(request: DFMAnalysisRequest):
    """Generate heatmap data for visualization"""
    try:
        logger.info("Generating heatmap data")
        
        # Detect issues for heatmap
        detected_issues = analyzer.detect_issues(request.geometry, request.process)
        
        # Generate heatmap data
        heatmap_data = analyzer.generate_heatmap_data(detected_issues)
        
        logger.info(f"Heatmap generated with {len(detected_issues)} issues")
        return heatmap_data
        
    except Exception as e:
        logger.error(f"Heatmap generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Heatmap generation failed: {str(e)}")

@app.get("/api/dfm/costs/{process}/{material}")
async def get_cost_estimates(process: str, material: str, volume: float = 1000, quantity: int = 1):
    """Get cost estimates for specific process and material"""
    try:
        # Create dummy geometry for cost calculation
        dummy_geometry = GeometryData(
            volume=volume,
            surface_area=volume * 0.6,  # Rough estimate
            bounding_box={"x_length": 10, "y_length": 10, "z_length": 10},
            object_type="estimate"
        )
        
        dummy_process = ProcessData(
            process=process,
            material=material,
            quantity=quantity
        )
        
        costs = analyzer.calculate_costs(dummy_geometry, dummy_process, [])
        
        return {
            "process": process,
            "material": material,
            "volume_mm3": volume,
            "quantity": quantity,
            "costs": costs
        }
        
    except Exception as e:
        logger.error(f"Cost estimation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cost estimation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
