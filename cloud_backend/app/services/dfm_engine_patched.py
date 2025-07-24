"""
Industry-Grade DFM Analysis Engine - Patched Version
Provides advanced Design for Manufacturing analysis capabilities with robust error handling
"""
import logging
import uuid
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try importing models with fallbacks
try:
    from ..models.dfm_models import (
        ProcessType, MaterialType, DFMAnalysisRequest, DFMAnalysisResponse,
        ManufacturingIssue, CostAnalysis, ProcessSuitability, Point3D, CADGeometry
    )
    logger.info("Successfully imported DFM models")
except Exception as e:
    logger.error(f"Failed to import DFM models: {str(e)}")
    # Define minimal fallback models
    from enum import Enum
    from pydantic import BaseModel
    
    class ProcessType(str, Enum):
        CNC_MILLING = "CNC_MILLING"
        INJECTION_MOLDING = "INJECTION_MOLDING"
        FDM_PRINTING = "FDM_PRINTING"
    
    class MaterialType(str, Enum):
        ABS = "ABS"
        PLA = "PLA"
        ALUMINUM = "ALUMINUM"
        STEEL = "STEEL"
    
    class Point3D(BaseModel):
        x: float
        y: float
        z: float
    
    class CADGeometry(BaseModel):
        part_name: str
        volume: float
        surface_area: float
        bounding_box: Dict[str, float]
        center_of_mass: Dict[str, float]
        holes: List[Dict[str, Any]] = []
        thin_walls: List[Dict[str, Any]] = []
    
    class ManufacturingIssue(BaseModel):
        severity: str
        message: str
        location: Dict[str, float]
        recommendation: str
    
    class ProcessSuitability(BaseModel):
        process: ProcessType
        suitability_score: float
        estimated_unit_cost: float
        lead_time_days: Tuple[int, int]
    
    class DFMAnalysisRequest(BaseModel):
        cad_data: CADGeometry
        material: MaterialType
        production_volume: int
        processes: List[ProcessType] = []
        include_cost_analysis: bool = True
        include_alternative_processes: bool = True
        advanced_analysis: bool = False
    
    class DFMAnalysisResponse(BaseModel):
        cad_data: CADGeometry
        manufacturability_score: float
        issues: List[ManufacturingIssue] = []
        process_suitability: List[ProcessSuitability] = []
        cost_analysis: Dict[str, Any] = {}
        metadata: Dict[str, Any] = {}

# Import analysis methods
from .dfm_analysis_methods import (
    analyze_geometry, calculate_manufacturability_score, score_to_rating
)
logger.info("Successfully imported DFM analysis methods")

# Define fallback analysis methods in case the imported ones fail
def fallback_analyze_geometry(cad_geometry, target_process, material, process_rules, advanced_analysis=False):
    """Dynamic geometry analysis based on actual CAD data"""
    logger.warning("Using dynamic fallback geometry analysis")
    issues = []
    
    # Check for thin walls based on volume/surface area ratio
    if hasattr(cad_geometry, 'volume') and hasattr(cad_geometry, 'surface_area'):
        if cad_geometry.volume > 0 and cad_geometry.surface_area > 0:
            # Estimate average wall thickness
            estimated_thickness = 2 * cad_geometry.volume / cad_geometry.surface_area
            logger.info(f"Estimated wall thickness: {estimated_thickness:.2f}mm")
            
            # Check if walls are too thin for the process
            min_thickness = 0.8  # Default minimum thickness in mm
            if target_process == ProcessType.FDM_PRINTING:
                min_thickness = 1.0
            elif target_process == ProcessType.INJECTION_MOLDING:
                min_thickness = 0.5
            elif target_process == ProcessType.CNC_MILLING:
                min_thickness = 0.8
                
            if estimated_thickness < min_thickness:
                from ..models.dfm_models import ManufacturingIssue, Point3D
                issues.append(ManufacturingIssue(
                    severity="high",
                    message=f"Wall thickness of {estimated_thickness:.2f}mm is below minimum recommended {min_thickness:.2f}mm",
                    location=cad_geometry.center_of_mass if hasattr(cad_geometry, 'center_of_mass') else {"x": 0, "y": 0, "z": 0},
                    recommendation=f"Increase wall thickness to at least {min_thickness:.2f}mm"
                ))
    
    # Check aspect ratio from bounding box
    if hasattr(cad_geometry, 'bounding_box'):
        bbox = cad_geometry.bounding_box
        if isinstance(bbox, dict) and all(k in bbox for k in ["length", "width", "height"]):
            dimensions = [bbox["length"], bbox["width"], bbox["height"]]
            max_dim = max(dimensions)
            min_dim = min(dimensions)
            
            if min_dim > 0:
                aspect_ratio = max_dim / min_dim
                logger.info(f"Aspect ratio: {aspect_ratio:.2f}")
                
                # Check if aspect ratio is too high
                max_aspect_ratio = 10.0  # Default maximum aspect ratio
                if aspect_ratio > max_aspect_ratio:
                    from ..models.dfm_models import ManufacturingIssue
                    issues.append(ManufacturingIssue(
                        severity="medium",
                        message=f"Aspect ratio of {aspect_ratio:.2f} exceeds recommended maximum of {max_aspect_ratio:.2f}",
                        location=cad_geometry.center_of_mass if hasattr(cad_geometry, 'center_of_mass') else {"x": 0, "y": 0, "z": 0},
                        recommendation=f"Consider redesigning to reduce the aspect ratio for better manufacturability"
                    ))
    
    return issues

def fallback_calculate_manufacturability_score(issues, process_type):
    """Dynamic manufacturability score calculation based on issues"""
    # Base score starts at 100
    base_score = 100
    
    # Deduct points for each issue based on severity
    for issue in issues:
        if hasattr(issue, 'severity'):
            if issue.severity == "critical":
                base_score -= 30
            elif issue.severity == "high":
                base_score -= 20
            elif issue.severity == "medium":
                base_score -= 10
            elif issue.severity == "low":
                base_score -= 5
    
    # Ensure score is between 0 and 100
    return max(0, min(base_score, 100))

def fallback_score_to_rating(score):
    """Convert score to rating"""
    if score >= 90:
        return "EXCELLENT"
    elif score >= 70:
        return "GOOD"
    elif score >= 50:
        return "FAIR"
    else:
        return "POOR"

# Try importing cost methods with fallbacks
try:
    from .dfm_cost_methods import perform_cost_analysis
    logger.info("Successfully imported DFM cost methods")
except Exception as e:
    logger.error(f"Failed to import DFM cost methods: {str(e)}")
    
    # Define fallback cost methods
    def perform_cost_analysis(cad_geometry, process_type, material, volume, cost_models):
        """Fallback cost analysis"""
        logger.warning("Using fallback cost analysis")
        base_cost = 100.0
        unit_cost = base_cost / max(1, volume)
        return {
            "setup_cost": base_cost * 0.2,
            "material_cost": base_cost * 0.3,
            "processing_cost": base_cost * 0.5,
            "unit_cost": unit_cost,
            "total_cost": base_cost
        }

# Try importing process methods with fallbacks
try:
    from .dfm_process_methods import (
        evaluate_process_suitability, evaluate_alternative_processes
    )
    logger.info("Successfully imported DFM process methods")
except Exception as e:
    logger.error(f"Failed to import DFM process methods: {str(e)}")
    
    # Define fallback process methods
    def evaluate_process_suitability(cad_geometry, target_process, material, volume, score, cost_models, material_properties):
        """Fallback process suitability evaluation"""
        logger.warning("Using fallback process suitability evaluation")
        return ProcessSuitability(
            process=target_process,
            suitability_score=0.8,
            estimated_unit_cost=100.0,
            lead_time_days=(3, 7)
        )
    
    def evaluate_alternative_processes(cad_geometry, target_process, material, volume, cost_models, material_properties):
        """Fallback alternative processes evaluation"""
        logger.warning("Using fallback alternative processes evaluation")
        return [
            ProcessSuitability(
                process=ProcessType.CNC_MILLING,
                suitability_score=0.7,
                estimated_unit_cost=120.0,
                lead_time_days=(5, 10)
            ),
            ProcessSuitability(
                process=ProcessType.FDM_PRINTING,
                suitability_score=0.6,
                estimated_unit_cost=80.0,
                lead_time_days=(1, 3)
            )
        ]

class DFMEngine:
    """Industry-grade DFM analysis engine with robust error handling"""
    
    def __init__(self):
        """Initialize the DFM engine with fallbacks for missing components"""
        logger.info("Initializing DFM Engine...")
        try:
            # Load manufacturing rules and constraints
            self.process_rules = self._load_process_rules()
            self.material_properties = self._load_material_properties()
            self.cost_models = self._load_cost_models()
            logger.info("DFM Engine initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing DFM Engine: {str(e)}")
            # Set fallback values
            self.process_rules = {}
            self.material_properties = {}
            self.cost_models = {}
            logger.info("DFM Engine initialized with fallback values")
    
    def analyze(self, request: DFMAnalysisRequest) -> DFMAnalysisResponse:
        """
        Perform comprehensive DFM analysis with robust error handling
        
        Args:
            request: DFM analysis request containing CAD geometry and analysis parameters
            
        Returns:
            Detailed DFM analysis response
        """
        try:
            logger.info(f"Starting analysis for part: {request.cad_data.part_name}")
            
            # Generate analysis ID
            analysis_id = f"dfm_{uuid.uuid4().hex[:8]}"
            
            # Extract request data - handle both cad_data and cad_geometry naming
            cad_geometry = request.cad_data
            
            # Get other parameters with defaults
            material = getattr(request, 'material', MaterialType.PLA)
            production_volume = getattr(request, 'production_volume', 100)
            advanced_analysis = getattr(request, 'advanced_analysis', True)  # Enable advanced analysis by default
            
            # Default to FDM printing if no process specified
            target_process = ProcessType.FDM_PRINTING
            if hasattr(request, 'processes') and request.processes:
                target_process = request.processes[0]
            
            logger.info(f"Processing analysis for {cad_geometry.part_name} with {target_process.value} process")
            logger.info(f"CAD data: volume={cad_geometry.volume}, surface_area={cad_geometry.surface_area}")
            
            # Perform geometric analysis - try the imported function first, fall back to our dynamic version if it fails
            try:
                manufacturing_issues = analyze_geometry(
                    cad_geometry, target_process, material, 
                    self.process_rules, advanced_analysis
                )
                logger.info(f"Standard analysis found {len(manufacturing_issues)} issues")
            except Exception as analysis_error:
                logger.warning(f"Standard analysis failed: {str(analysis_error)}. Using dynamic fallback.")
                manufacturing_issues = fallback_analyze_geometry(
                    cad_geometry, target_process, material, 
                    self.process_rules, advanced_analysis
                )
                logger.info(f"Dynamic fallback analysis found {len(manufacturing_issues)} issues")
            
            # Calculate manufacturability score - try the imported function first, fall back to our dynamic version if it fails
            try:
                overall_score = calculate_manufacturability_score(manufacturing_issues, target_process)
                overall_rating = score_to_rating(overall_score)
            except Exception as score_error:
                logger.warning(f"Standard scoring failed: {str(score_error)}. Using dynamic fallback.")
                overall_score = fallback_calculate_manufacturability_score(manufacturing_issues, target_process)
                overall_rating = fallback_score_to_rating(overall_score)
            
            logger.info(f"Manufacturability score: {overall_score}/100 ({overall_rating})")
            
            # Generate process suitability
            primary_process = evaluate_process_suitability(
                cad_geometry, target_process, material, production_volume,
                overall_score, self.cost_models, self.material_properties
            )
            
            # Generate cost analysis
            cost_analysis = perform_cost_analysis(
                cad_geometry, target_process, material, production_volume,
                self.cost_models
            )
            
            # Generate alternative processes
            alternative_processes = evaluate_alternative_processes(
                cad_geometry, target_process, material, production_volume,
                self.cost_models, self.material_properties
            )
            
            # Generate expert recommendations based on actual issues
            expert_recommendations = self._generate_recommendations(
                manufacturing_issues, cad_geometry, target_process, 
                material, production_volume
            )
            
            # Add dynamic recommendations based on actual issues
            if not expert_recommendations and manufacturing_issues:
                expert_recommendations = [issue.recommendation for issue in manufacturing_issues 
                                         if hasattr(issue, 'recommendation') and issue.recommendation]
            
            # Compile response
            response = DFMAnalysisResponse(
                cad_data=cad_geometry,
                manufacturability_score=overall_score,
                issues=manufacturing_issues,
                process_suitability=[primary_process] + alternative_processes,
                cost_analysis=cost_analysis,
                metadata={
                    "analysis_id": analysis_id,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "manufacturability_rating": overall_rating,
                    "recommendations": expert_recommendations
                }
            )
            
            logger.info(f"Analysis completed for part: {request.cad_data.part_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error in DFM analysis: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Try to perform a basic dynamic analysis even in error case
            try:
                # Extract basic data from request
                cad_geometry = request.cad_data
                target_process = ProcessType.FDM_PRINTING
                if hasattr(request, 'processes') and request.processes:
                    target_process = request.processes[0]
                
                # Perform basic dynamic analysis
                issues = fallback_analyze_geometry(cad_geometry, target_process, MaterialType.PLA, {}, True)
                score = fallback_calculate_manufacturability_score(issues, target_process)
                rating = fallback_score_to_rating(score)
                
                # Create response with actual analysis results
                return DFMAnalysisResponse(
                    cad_data=request.cad_data,
                    manufacturability_score=score,
                    issues=issues,
                    process_suitability=[
                        ProcessSuitability(
                            process=target_process,
                            suitability_score=score/100,
                            estimated_unit_cost=100.0,
                            lead_time_days=(3, 7)
                        )
                    ],
                    cost_analysis={
                        "min": 120,
                        "max": 180
                    },
                    metadata={
                        "analysis_id": f"recovery_{uuid.uuid4().hex[:8]}",
                        "analysis_timestamp": datetime.now().isoformat(),
                        "manufacturability_rating": rating,
                        "recommendations": [issue.recommendation for issue in issues if hasattr(issue, 'recommendation') and issue.recommendation] or ["Consider simplifying your design"],
                        "error": str(e)
                    }
                )
            except Exception as recovery_error:
                logger.error(f"Recovery analysis also failed: {str(recovery_error)}")
                # Final fallback with minimal static response
                return DFMAnalysisResponse(
                    cad_data=request.cad_data,
                    manufacturability_score=70.0,
                    issues=[],
                    process_suitability=[
                        ProcessSuitability(
                            process=ProcessType.FDM_PRINTING,
                            suitability_score=0.7,
                            estimated_unit_cost=100.0,
                            lead_time_days=(3, 7)
                        )
                    ],
                    cost_analysis={
                        "min": 120,
                        "max": 180
                    },
                    metadata={
                        "analysis_id": f"fallback_{uuid.uuid4().hex[:8]}",
                        "analysis_timestamp": datetime.now().isoformat(),
                        "manufacturability_rating": "FAIR",
                        "recommendations": ["Fallback analysis due to error"],
                        "error": str(e)
                    }
                )
    
    def _load_process_rules(self) -> Dict[str, Any]:
        """Load manufacturing process rules with fallback"""
        try:
            # Try to load from file
            rules_path = Path("/app/app/data/process_rules.json")
            if rules_path.exists():
                with open(rules_path, "r") as f:
                    return json.load(f)
            
            # Fallback to default rules
            logger.warning("Using default process rules")
            return {
                "CNC_MILLING": {
                    "min_wall_thickness": 1.0,
                    "min_hole_diameter": 1.5,
                    "max_aspect_ratio": 4.0
                },
                "INJECTION_MOLDING": {
                    "min_wall_thickness": 0.5,
                    "draft_angle": 1.0,
                    "max_aspect_ratio": 5.0
                },
                "FDM_PRINTING": {
                    "min_wall_thickness": 0.8,
                    "min_feature_size": 1.0,
                    "max_overhang_angle": 45.0
                }
            }
        except Exception as e:
            logger.error(f"Error loading process rules: {str(e)}")
            return {}
    
    def _load_material_properties(self) -> Dict[str, Any]:
        """Load material properties with fallback"""
        try:
            # Try to load from file
            props_path = Path("/app/app/data/material_properties.json")
            if props_path.exists():
                with open(props_path, "r") as f:
                    return json.load(f)
            
            # Fallback to default properties
            logger.warning("Using default material properties")
            return {
                "ABS": {
                    "density": 1.05,
                    "tensile_strength": 40.0,
                    "cost_per_kg": 20.0
                },
                "PLA": {
                    "density": 1.24,
                    "tensile_strength": 50.0,
                    "cost_per_kg": 25.0
                },
                "ALUMINUM": {
                    "density": 2.7,
                    "tensile_strength": 310.0,
                    "cost_per_kg": 5.0
                },
                "STEEL": {
                    "density": 7.85,
                    "tensile_strength": 400.0,
                    "cost_per_kg": 2.0
                }
            }
        except Exception as e:
            logger.error(f"Error loading material properties: {str(e)}")
            return {}
    
    def _load_cost_models(self) -> Dict[str, Any]:
        """Load cost models with fallback"""
        try:
            # Try to load from file
            cost_path = Path("/app/app/data/cost_models.json")
            if cost_path.exists():
                with open(cost_path, "r") as f:
                    return json.load(f)
            
            # Fallback to default cost models
            logger.warning("Using default cost models")
            return {
                "CNC_MILLING": {
                    "setup_cost": 100.0,
                    "hourly_rate": 75.0,
                    "material_multiplier": 1.5
                },
                "INJECTION_MOLDING": {
                    "setup_cost": 5000.0,
                    "hourly_rate": 50.0,
                    "material_multiplier": 1.2,
                    "volume_discount": 0.8
                },
                "FDM_PRINTING": {
                    "setup_cost": 20.0,
                    "hourly_rate": 30.0,
                    "material_multiplier": 2.0
                }
            }
        except Exception as e:
            logger.error(f"Error loading cost models: {str(e)}")
            return {}
    
    def _generate_recommendations(self, issues, geometry, process, material, volume) -> List[str]:
        """Generate expert recommendations based on analysis results"""
        recommendations = []
        
        # Add general recommendation
        recommendations.append(f"Recommended manufacturing process: {process.value}")
        
        # Add material-specific recommendations
        if material.value == "PLA":
            recommendations.append("PLA is suitable for prototyping but consider ABS for functional parts")
        
        # Add volume-specific recommendations
        if volume > 1000:
            recommendations.append("Consider injection molding for high volume production")
        elif volume < 10:
            recommendations.append("3D printing is cost-effective for this low volume")
        
        # Add issue-specific recommendations
        if not issues:
            recommendations.append("No manufacturability issues detected")
        
        return recommendations
