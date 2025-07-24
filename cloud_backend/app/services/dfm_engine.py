"""
Industry-Grade DFM Analysis Engine
Provides advanced Design for Manufacturing analysis capabilities
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from ..models.dfm_models import (
    ProcessType, MaterialType, DFMAnalysisRequest, DFMAnalysisResponse,
    ManufacturingIssue, CostAnalysis, ProcessSuitability, Point3D
)

# Import analysis methods
from .dfm_analysis_methods import (
    analyze_geometry, calculate_manufacturability_score, score_to_rating
)

# Import cost methods
from .dfm_cost_methods import perform_cost_analysis

# Import process methods
from .dfm_process_methods import (
    evaluate_process_suitability, evaluate_alternative_processes
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DFMEngine:
    """Industry-grade DFM analysis engine"""
    
    def __init__(self):
        """Initialize the DFM engine"""
        # Load manufacturing rules and constraints
        self.process_rules = self._load_process_rules()
        self.material_properties = self._load_material_properties()
        self.cost_models = self._load_cost_models()
    
    def analyze(self, request: DFMAnalysisRequest) -> DFMAnalysisResponse:
        """
        Perform comprehensive DFM analysis
        
        Args:
            request: DFM analysis request containing CAD geometry and analysis parameters
            
        Returns:
            Detailed DFM analysis response
        """
        try:
            # Generate analysis ID
            analysis_id = f"dfm_{uuid.uuid4().hex[:8]}"
            
            # Extract request data
            cad_geometry = request.cad_geometry
            target_process = request.target_process
            material = request.material
            production_volume = request.production_volume
            advanced_analysis = request.advanced_analysis
            
            # Perform geometric analysis
            manufacturing_issues = analyze_geometry(cad_geometry, target_process, material, self.process_rules, advanced_analysis)
            
            # Separate critical issues
            critical_issues = [issue for issue in manufacturing_issues if issue.severity == "critical"]
            non_critical_issues = [issue for issue in manufacturing_issues if issue.severity != "critical"]
            
            # Calculate manufacturability score
            overall_score = calculate_manufacturability_score(manufacturing_issues, target_process)
            overall_rating = score_to_rating(overall_score)
            
            # Generate process suitability
            primary_process = evaluate_process_suitability(
                cad_geometry, target_process, material, production_volume,
                overall_score, self.cost_models, self.material_properties
            )
            
            # Generate cost analysis if requested
            cost_analysis = None
            if request.include_cost_analysis:
                cost_analysis = perform_cost_analysis(
                    cad_geometry, target_process, material, production_volume,
                    self.cost_models
                )
            
            # Generate alternative processes if requested
            alternative_processes = None
            if request.include_alternative_processes:
                alternative_processes = evaluate_alternative_processes(
                    cad_geometry, target_process, material, production_volume,
                    self.cost_models, self.material_properties
                )
            
            # Generate expert recommendations
            expert_recommendations = self._generate_recommendations(
                manufacturing_issues, cad_geometry, target_process, material, production_volume
            )
            
            # Create response
            response = DFMAnalysisResponse(
                analysis_id=analysis_id,
                overall_manufacturability_score=overall_score,
                overall_rating=overall_rating,
                primary_process=primary_process,
                critical_issues=critical_issues,
                manufacturing_issues=non_critical_issues,
                cost_analysis=cost_analysis,
                alternative_processes=alternative_processes,
                expert_recommendations=expert_recommendations
            )
            
            return response
            
        except Exception as e:
            logger.error(f"DFM analysis error: {e}")
            raise
    
    def _load_process_rules(self) -> Dict[str, Any]:
        """Load manufacturing process rules and constraints"""
        # In a production system, these would be loaded from a database
        return {
            ProcessType.INJECTION_MOLDING: {
                "min_wall_thickness": 0.5,  # mm
                "max_wall_thickness": 4.0,  # mm
                "max_aspect_ratio": 5.0,
                "draft_angle": 1.0,  # degrees
                "min_corner_radius": 0.5,  # mm
                "max_undercut_depth": 0.0,  # mm (0 = not allowed)
                "tolerance": 0.1,  # mm
                "surface_finish": 0.8,  # Ra (μm)
                "max_part_size": 1000,  # mm
                "min_part_size": 5,  # mm
            },
            ProcessType.CNC_MILLING: {
                "min_wall_thickness": 0.8,  # mm
                "max_aspect_ratio": 8.0,
                "min_corner_radius": 0.8,  # mm (based on tool diameter)
                "min_hole_diameter": 1.0,  # mm
                "max_depth_to_diameter": 5.0,
                "tolerance": 0.05,  # mm
                "surface_finish": 1.6,  # Ra (μm)
                "max_part_size": 2000,  # mm
                "min_part_size": 10,  # mm
            },
            ProcessType.FDM_PRINTING: {
                "min_wall_thickness": 1.0,  # mm
                "max_overhang_angle": 45.0,  # degrees
                "min_feature_size": 1.0,  # mm
                "tolerance": 0.2,  # mm
                "surface_finish": 12.5,  # Ra (μm)
                "max_part_size": 300,  # mm
                "min_part_size": 2,  # mm
            },
            # Additional processes would be defined here
        }
    
    def _load_material_properties(self) -> Dict[str, Any]:
        """Load material properties"""
        # In a production system, these would be loaded from a database
        return {
            MaterialType.ABS: {
                "density": 1.05,  # g/cm³
                "shrinkage": 0.007,  # 0.7%
                "min_wall_thickness": 1.2,  # mm
                "thermal_expansion": 90e-6,  # 1/K
                "elastic_modulus": 2200,  # MPa
                "compatible_processes": [
                    ProcessType.INJECTION_MOLDING,
                    ProcessType.FDM_PRINTING
                ]
            },
            MaterialType.ALUMINUM: {
                "density": 2.7,  # g/cm³
                "thermal_expansion": 23e-6,  # 1/K
                "elastic_modulus": 69000,  # MPa
                "min_wall_thickness": 0.8,  # mm
                "compatible_processes": [
                    ProcessType.CNC_MILLING,
                    ProcessType.CNC_TURNING,
                    ProcessType.CASTING,
                    ProcessType.EXTRUSION
                ]
            },
            # Additional materials would be defined here
        }
    
    def _load_cost_models(self) -> Dict[str, Any]:
        """Load cost models for different processes"""
        # In a production system, these would be loaded from a database
        return {
            ProcessType.INJECTION_MOLDING: {
                "tooling_base": 5000.0,  # USD
                "tooling_complexity_factor": 1.0,
                "material_cost_factor": 1.0,
                "cycle_time_base": 30.0,  # seconds
                "machine_rate": 75.0,  # USD/hour
                "setup_cost": 500.0,  # USD
                "volume_discounts": {
                    1000: 1.0,
                    5000: 0.8,
                    10000: 0.6,
                    50000: 0.4,
                    100000: 0.3
                }
            },
            ProcessType.CNC_MILLING: {
                "setup_cost": 150.0,  # USD
                "machine_rate": 85.0,  # USD/hour
                "material_cost_factor": 1.2,
                "tooling_cost": 50.0,  # USD
                "programming_cost": 200.0,  # USD
                "volume_discounts": {
                    10: 1.0,
                    50: 0.9,
                    100: 0.8,
                    500: 0.7,
                    1000: 0.6
                }
            },
            # Additional cost models would be defined here
        }
        
    def _generate_recommendations(self, issues: List[ManufacturingIssue], 
                                 cad_geometry: CADGeometry, process: ProcessType,
                                 material: MaterialType, production_volume: int) -> List[str]:
        """
        Generate expert recommendations based on analysis results
        
        Args:
            issues: List of manufacturing issues
            cad_geometry: CAD geometry data
            process: Target manufacturing process
            material: Target material
            production_volume: Production quantity
            
        Returns:
            List of expert recommendations
        """
        recommendations = []
        
        # Get process constraints
        process_constraints = self.process_rules.get(process, {})
        material_props = self.material_properties.get(material, {})
        
        # Group issues by severity
        critical_issues = [issue for issue in issues if issue.severity == "critical"]
        high_issues = [issue for issue in issues if issue.severity == "high"]
        medium_issues = [issue for issue in issues if issue.severity == "medium"]
        
        # Generate recommendations based on issues
        if critical_issues:
            recommendations.append("Address all critical issues before proceeding with manufacturing.")
        
        # Wall thickness recommendations
        wall_issues = [i for i in issues if "Wall Thickness" in i.title]
        if wall_issues:
            min_thickness = process_constraints.get("min_wall_thickness", 0.8)
            recommendations.append(
                f"Maintain wall thickness of at least {min_thickness}mm for {process.value}. "
                f"Consider using ribs instead of increasing overall thickness."
            )
        
        # Draft angle recommendations for injection molding
        if process == ProcessType.INJECTION_MOLDING:
            draft_angle = process_constraints.get("draft_angle", 1.0)
            recommendations.append(
                f"Ensure all vertical faces have at least {draft_angle}° draft angle for proper ejection from the mold."
            )
        
        # Material recommendations
        if material in self.material_properties and process not in material_props.get("compatible_processes", []):
            compatible = material_props.get("compatible_processes", [])
            if compatible:
                compatible_str = ", ".join([p.value for p in compatible])
                recommendations.append(
                    f"{material.value} is not ideal for {process.value}. "
                    f"Consider using this material with {compatible_str} instead."
                )
        
        # Volume recommendations
        if process == ProcessType.INJECTION_MOLDING and production_volume < 1000:
            recommendations.append(
                "Injection molding is typically cost-effective for volumes over 1,000 units. "
                "Consider 3D printing or CNC machining for lower volumes."
            )
        elif process == ProcessType.CNC_MILLING and production_volume > 1000:
            recommendations.append(
                "CNC machining becomes less cost-effective for volumes over 1,000 units. "
                "Consider injection molding for higher volumes."
            )
        
        # General design recommendations
        if process == ProcessType.INJECTION_MOLDING:
            recommendations.append(
                "Design with uniform wall thickness and avoid sharp corners to prevent sink marks and improve material flow."
            )
        elif process == ProcessType.CNC_MILLING:
            recommendations.append(
                "Design with standard tool sizes in mind and avoid deep pockets with small corner radii."
            )
        elif process == ProcessType.FDM_PRINTING:
            recommendations.append(
                "Orient the part to minimize overhangs and support structures. Consider the layer orientation for optimal strength."
            )
        
        # Cost optimization recommendations
        if len(issues) > 5:
            recommendations.append(
                "Consider design simplification to reduce manufacturing complexity and cost."
            )
        
        # Add general recommendation if list is empty
        if not recommendations:
            recommendations.append(
                "The design appears suitable for the selected manufacturing process and material."
            )
        
        return recommendations
