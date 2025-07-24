"""
Enhanced API Format Converter for Production CAD Analysis
Provides conversion between different API formats for industry-grade DFM analysis
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
import math
import json
import hashlib
import concurrent.futures
from datetime import datetime

from ..models.dfm_models import (
    ProcessType, MaterialType, CADGeometry, BoundingBox, Point3D,
    DFMAnalysisRequest, DFMAnalysisResponse, ManufacturingIssue,
    CostAnalysis, ProcessSuitability
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedAPIFormatConverter:
    """Converts between different API formats for CAD analysis and provides advanced manufacturing intelligence"""
    
    def __init__(self):
        """Initialize the API format converter"""
        self.version = "1.0.0"
        logger.info(f"Initializing Enhanced API Format Converter v{self.version}")
        
        # Initialize manufacturing constants
        self._init_manufacturing_constants()
    
    def _init_manufacturing_constants(self):
        """Initialize manufacturing constants and reference data"""
        # Machining speeds and feeds by material
        self.machining_constants = {
            MaterialType.ALUMINUM: {
                "cutting_speed": 500,  # m/min
                "feed_rate": 0.1,      # mm/rev
                "tool_life": 120       # minutes
            },
            MaterialType.STEEL: {
                "cutting_speed": 150,
                "feed_rate": 0.08,
                "tool_life": 90
            },
            MaterialType.STAINLESS_STEEL: {
                "cutting_speed": 100,
                "feed_rate": 0.05,
                "tool_life": 60
            },
            MaterialType.BRASS: {
                "cutting_speed": 300,
                "feed_rate": 0.15,
                "tool_life": 180
            },
            MaterialType.ABS: {
                "cutting_speed": 200,
                "feed_rate": 0.2,
                "tool_life": 240
            },
            MaterialType.PLA: {
                "cutting_speed": 180,
                "feed_rate": 0.25,
                "tool_life": 300
            }
        }
        
        # Minimum wall thickness by process
        self.min_wall_thickness = {
            ProcessType.INJECTION_MOLDING: 0.8,  # mm
            ProcessType.CNC_MILLING: 0.5,
            ProcessType.FDM_PRINTING: 1.0,
            ProcessType.SLA_PRINTING: 0.5,
            ProcessType.SLS_PRINTING: 0.8,
            ProcessType.SHEET_METAL: 0.5
        }
        
        # Draft angle requirements by process
        self.draft_angle_requirements = {
            ProcessType.INJECTION_MOLDING: 1.0,  # degrees
            ProcessType.CASTING: 2.0,
            ProcessType.FORGING: 3.0
        }
        
        # Process volume thresholds
        self.volume_thresholds = {
            ProcessType.INJECTION_MOLDING: 1000,
            ProcessType.CNC_MILLING: 500,
            ProcessType.FDM_PRINTING: 50,
            ProcessType.SHEET_METAL: 200,
            ProcessType.CASTING: 500,
            ProcessType.FORGING: 2000
        }
    
    def legacy_to_enhanced_format(self, legacy_data: Dict[str, Any]) -> CADGeometry:
        """
        Convert legacy CAD data format to enhanced CADGeometry format
        
        Args:
            legacy_data: Legacy CAD data dictionary
            
        Returns:
            Enhanced CADGeometry object
        """
        try:
            logger.info("Converting legacy data to enhanced format")
            
            # Extract dimensions
            dimensions = legacy_data.get("dimensions", {})
            length = float(dimensions.get("length", 0))
            width = float(dimensions.get("width", 0))
            height = float(dimensions.get("height", 0))
            
            # Create bounding box
            bounding_box = BoundingBox(
                length=length,
                width=width,
                height=height
            )
            
            # Extract or calculate center of mass
            com = legacy_data.get("center_of_mass", {"x": 0, "y": 0, "z": 0})
            center_of_mass = Point3D(
                x=float(com.get("x", 0)),
                y=float(com.get("y", 0)),
                z=float(com.get("z", 0))
            )
            
            # Extract volume and surface area
            volume = float(legacy_data.get("volume", length * width * height))
            surface_area = float(legacy_data.get("surface_area", 
                2 * (length * width + length * height + width * height)))
            
            # Extract part name
            part_name = legacy_data.get("name", "Unknown Part")
            
            # Create CADGeometry object
            cad_geometry = CADGeometry(
                part_name=part_name,
                volume=volume,
                surface_area=surface_area,
                bounding_box=bounding_box,
                center_of_mass=center_of_mass,
                faces=legacy_data.get("face_count", None)
            )
            
            # Add holes if available
            if "holes" in legacy_data:
                for hole_data in legacy_data["holes"]:
                    hole_location = hole_data.get("position", [0, 0, 0])
                    cad_geometry.holes.append({
                        "diameter": float(hole_data.get("diameter", 0)),
                        "depth": float(hole_data.get("depth", 0)),
                        "location": hole_location
                    })
            
            # Add thin walls if available
            if "thin_walls" in legacy_data:
                for wall_data in legacy_data["thin_walls"]:
                    wall_location = wall_data.get("position", [0, 0, 0])
                    cad_geometry.thin_walls.append({
                        "thickness": float(wall_data.get("thickness", 0)),
                        "location": wall_location
                    })
            
            logger.info(f"Successfully converted legacy data for part: {part_name}")
            return cad_geometry
            
        except Exception as e:
            logger.error(f"Error converting legacy data: {e}")
            raise ValueError(f"Failed to convert legacy data: {e}")
    
    def enhanced_to_legacy_format(self, cad_geometry: CADGeometry) -> Dict[str, Any]:
        """
        Convert enhanced CADGeometry to legacy format
        
        Args:
            cad_geometry: Enhanced CADGeometry object
            
        Returns:
            Legacy CAD data dictionary
        """
        try:
            logger.info(f"Converting enhanced data to legacy format for part: {cad_geometry.part_name}")
            
            # Create legacy format dictionary
            legacy_data = {
                "name": cad_geometry.part_name,
                "dimensions": {
                    "length": cad_geometry.bounding_box.length,
                    "width": cad_geometry.bounding_box.width,
                    "height": cad_geometry.bounding_box.height
                },
                "volume": cad_geometry.volume,
                "surface_area": cad_geometry.surface_area,
                "center_of_mass": {
                    "x": cad_geometry.center_of_mass.x,
                    "y": cad_geometry.center_of_mass.y,
                    "z": cad_geometry.center_of_mass.z
                }
            }
            
            # Add face count if available
            if cad_geometry.faces is not None:
                legacy_data["face_count"] = cad_geometry.faces
            
            # Add holes if available
            if cad_geometry.holes:
                legacy_data["holes"] = []
                for hole in cad_geometry.holes:
                    legacy_data["holes"].append({
                        "diameter": hole.diameter,
                        "depth": hole.depth,
                        "position": hole.location
                    })
            
            # Add thin walls if available
            if cad_geometry.thin_walls:
                legacy_data["thin_walls"] = []
                for wall in cad_geometry.thin_walls:
                    legacy_data["thin_walls"].append({
                        "thickness": wall.thickness,
                        "position": wall.location
                    })
            
            logger.info("Successfully converted to legacy format")
            return legacy_data
            
        except Exception as e:
            logger.error(f"Error converting to legacy format: {e}")
            raise ValueError(f"Failed to convert to legacy format: {e}")
    
    def estimate_machining_time(self, cad_geometry: CADGeometry, material: MaterialType) -> Dict[str, Any]:
        """
        Estimate machining time based on geometry and material
        
        Args:
            cad_geometry: CAD geometry object
            material: Material type
            
        Returns:
            Dictionary with machining time estimates
        """
        try:
            logger.info(f"Estimating machining time for {cad_geometry.part_name} in {material.value}")
            
            # Get material constants
            material_constants = self.machining_constants.get(
                material, 
                self.machining_constants.get(MaterialType.ALUMINUM)  # Default to aluminum if not found
            )
            
            # Calculate volume to be removed (estimate as 25% of bounding box volume)
            bb_volume = (
                cad_geometry.bounding_box.length * 
                cad_geometry.bounding_box.width * 
                cad_geometry.bounding_box.height
            )
            volume_to_remove = bb_volume * 0.25  # Assumption: 25% material removal
            
            # Calculate surface area to be machined (estimate as 80% of total surface area)
            surface_area_to_machine = cad_geometry.surface_area * 0.8
            
            # Calculate rough machining time based on volume removal rate
            cutting_speed = material_constants["cutting_speed"]  # m/min
            feed_rate = material_constants["feed_rate"]  # mm/rev
            
            # Rough calculation for volume removal (simplified)
            rough_machining_minutes = volume_to_remove / (cutting_speed * feed_rate * 10)  # Simplified formula
            
            # Finishing time based on surface area
            finishing_minutes = surface_area_to_machine / (cutting_speed * 5)  # Simplified formula
            
            # Setup time (fixed + variable based on complexity)
            complexity_factor = 1.0
            if cad_geometry.faces and cad_geometry.faces > 50:
                complexity_factor = 1.5
            if len(cad_geometry.holes) > 5:
                complexity_factor += 0.5
                
            setup_minutes = 30 * complexity_factor  # Base setup time
            
            # Calculate total time
            total_minutes = rough_machining_minutes + finishing_minutes + setup_minutes
            
            # Add time for each hole (drilling operations)
            hole_minutes = sum(hole.depth * 0.5 for hole in cad_geometry.holes)
            total_minutes += hole_minutes
            
            # Return time estimates
            return {
                "total_machining_time_minutes": round(total_minutes, 1),
                "rough_machining_minutes": round(rough_machining_minutes, 1),
                "finishing_minutes": round(finishing_minutes, 1),
                "setup_minutes": round(setup_minutes, 1),
                "hole_operations_minutes": round(hole_minutes, 1),
                "complexity_factor": round(complexity_factor, 2)
            }
            
        except Exception as e:
            logger.error(f"Error estimating machining time: {e}")
            return {
                "total_machining_time_minutes": 60.0,  # Default fallback
                "error": str(e)
            }
    
    def assess_manufacturability(self, cad_geometry: CADGeometry, process: ProcessType) -> Dict[str, Any]:
        """
        Assess manufacturability of the part for a specific process
        
        Args:
            cad_geometry: CAD geometry object
            process: Manufacturing process
            
        Returns:
            Dictionary with manufacturability assessment
        """
        try:
            logger.info(f"Assessing manufacturability for {cad_geometry.part_name} using {process.value}")
            
            issues = []
            warnings = []
            recommendations = []
            score = 100.0  # Start with perfect score
            
            # Get process-specific constraints
            min_wall = self.min_wall_thickness.get(process, 1.0)  # Default to 1.0mm
            
            # Check part dimensions against process constraints
            bb = cad_geometry.bounding_box
            max_dim = max(bb.length, bb.width, bb.height)
            
            # Process-specific checks
            if process == ProcessType.INJECTION_MOLDING:
                # Check for thin walls
                for wall in cad_geometry.thin_walls:
                    if wall.thickness < min_wall:
                        issues.append(f"Wall thickness of {wall.thickness}mm is below minimum {min_wall}mm for injection molding")
                        score -= 15
                
                # Check for large parts
                if max_dim > 1000:
                    warnings.append(f"Part dimension {max_dim}mm exceeds typical injection molding size")
                    score -= 10
                    
                # Check for draft angles (simplified check)
                if not hasattr(cad_geometry, "draft_angles") or not cad_geometry.draft_angles:
                    warnings.append("No draft angle information available. Recommend minimum 1° draft")
                    
                # Recommend design improvements
                recommendations.append("Ensure uniform wall thickness to prevent sink marks and warping")
                recommendations.append("Add draft angles of at least 1° to all vertical faces")
                
            elif process == ProcessType.CNC_MILLING:
                # Check for deep pockets
                aspect_ratio = max_dim / min(bb.length, bb.width, bb.height)
                if aspect_ratio > 10:
                    warnings.append(f"High aspect ratio of {aspect_ratio:.1f} may require special tooling")
                    score -= 5
                
                # Check for internal features
                if len(cad_geometry.holes) > 0:
                    deep_holes = [h for h in cad_geometry.holes if h.depth > h.diameter * 5]
                    if deep_holes:
                        issues.append(f"Found {len(deep_holes)} deep holes that may be difficult to machine")
                        score -= len(deep_holes) * 3
                
                # Recommend design improvements
                recommendations.append("Design with standard tool sizes in mind (prefer common radii)")
                recommendations.append("Avoid deep pockets with small corner radii")
                
            elif process in [ProcessType.FDM_PRINTING, ProcessType.SLA_PRINTING, ProcessType.SLS_PRINTING]:
                # Check for support structures needed
                if hasattr(cad_geometry, "overhangs") and cad_geometry.overhangs:
                    warnings.append(f"Part has {len(cad_geometry.overhangs)} overhangs that will require support structures")
                    score -= len(cad_geometry.overhangs) * 2
                
                # Check for thin features
                if any(wall.thickness < min_wall for wall in cad_geometry.thin_walls):
                    issues.append(f"Some walls are thinner than minimum {min_wall}mm for {process.value}")
                    score -= 10
                
                # Recommend design improvements
                recommendations.append("Orient the part to minimize overhangs and support structures")
                recommendations.append("Consider the layer orientation for optimal strength")
            
            # Calculate final score and rating
            score = max(0, min(score, 100))  # Clamp between 0-100
            
            if score >= 90:
                rating = "excellent"
            elif score >= 75:
                rating = "good"
            elif score >= 50:
                rating = "fair"
            else:
                rating = "poor"
            
            return {
                "manufacturability_score": round(score, 1),
                "manufacturability_rating": rating,
                "issues": issues,
                "warnings": warnings,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error assessing manufacturability: {e}")
            return {
                "manufacturability_score": 50.0,
                "manufacturability_rating": "fair",
                "issues": [f"Error during assessment: {str(e)}"],
                "warnings": [],
                "recommendations": ["Perform manual review due to assessment error"]
            }
    
    def analyze_complexity(self, cad_geometry: CADGeometry) -> Dict[str, Any]:
        """
        Analyze geometric complexity of the part
        
        Args:
            cad_geometry: CAD geometry object
            
        Returns:
            Dictionary with complexity metrics
        """
        try:
            logger.info(f"Analyzing complexity for {cad_geometry.part_name}")
            
            # Calculate surface-to-volume ratio (higher = more complex)
            sv_ratio = cad_geometry.surface_area / max(0.001, cad_geometry.volume)
            
            # Calculate feature density
            feature_count = len(cad_geometry.holes) + len(cad_geometry.thin_walls)
            if hasattr(cad_geometry, "faces") and cad_geometry.faces:
                feature_density = feature_count / max(1, cad_geometry.faces)
            else:
                # Estimate based on surface area
                feature_density = feature_count / max(1, cad_geometry.surface_area / 100)
            
            # Calculate aspect ratio complexity
            bb = cad_geometry.bounding_box
            dimensions = [bb.length, bb.width, bb.height]
            dimensions.sort()
            aspect_ratio = dimensions[2] / max(0.001, dimensions[0])  # max/min
            aspect_complexity = min(10, aspect_ratio / 3)  # Normalize to 0-10 scale
            
            # Calculate overall complexity score (0-100)
            complexity_score = min(100, (
                sv_ratio * 5 +                # Surface-volume contribution
                feature_density * 30 +        # Feature density contribution
                aspect_complexity * 3 +       # Aspect ratio contribution
                feature_count * 2             # Raw feature count contribution
            ))
            
            # Determine complexity rating
            if complexity_score >= 80:
                complexity_rating = "Very High"
            elif complexity_score >= 60:
                complexity_rating = "High"
            elif complexity_score >= 40:
                complexity_rating = "Medium"
            elif complexity_score >= 20:
                complexity_rating = "Low"
            else:
                complexity_rating = "Very Low"
            
            # Generate complexity factors breakdown
            complexity_factors = {
                "surface_volume_ratio": round(sv_ratio, 2),
                "feature_density": round(feature_density, 2),
                "aspect_ratio": round(aspect_ratio, 2),
                "feature_count": feature_count
            }
            
            return {
                "complexity_score": round(complexity_score, 1),
                "complexity_rating": complexity_rating,
                "complexity_factors": complexity_factors,
                "manufacturing_implications": self._get_complexity_implications(complexity_rating)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing complexity: {e}")
            return {
                "complexity_score": 50.0,
                "complexity_rating": "Medium",
                "complexity_factors": {},
                "manufacturing_implications": ["Unable to determine complexity implications due to error"]
            }
    
    def _get_complexity_implications(self, complexity_rating: str) -> List[str]:
        """
        Get manufacturing implications based on complexity rating
        
        Args:
            complexity_rating: Complexity rating string
            
        Returns:
            List of manufacturing implications
        """
        implications = {
            "Very High": [
                "Likely to require advanced manufacturing techniques",
                "Higher tooling and setup costs expected",
                "May require multiple manufacturing operations",
                "Consider design simplification to reduce costs",
                "Detailed quality control procedures recommended"
            ],
            "High": [
                "May require specialized tooling",
                "Higher than average setup time",
                "Consider design optimization for manufacturing",
                "Multiple machining operations likely required"
            ],
            "Medium": [
                "Standard manufacturing processes applicable",
                "Moderate tooling requirements",
                "Average setup and production time expected"
            ],
            "Low": [
                "Simple manufacturing processes sufficient",
                "Minimal tooling requirements",
                "Quick setup and production time",
                "Good candidate for high-volume production"
            ],
            "Very Low": [
                "Extremely simple to manufacture",
                "Minimal processing required",
                "Excellent candidate for high-volume production",
                "Low production costs expected"
            ]
        }
        
        return implications.get(complexity_rating, ["Standard manufacturing considerations apply"])
    
    def recommend_processes(self, cad_geometry: CADGeometry, material: MaterialType, 
                           production_volume: int) -> List[ProcessSuitability]:
        """
        Recommend suitable manufacturing processes based on geometry, material and volume
        
        Args:
            cad_geometry: CAD geometry object
            material: Material type
            production_volume: Production quantity
            
        Returns:
            List of process suitability objects
        """
        try:
            logger.info(f"Recommending processes for {cad_geometry.part_name} in {material.value}, volume: {production_volume}")
            
            # Get complexity metrics
            complexity = self.analyze_complexity(cad_geometry)
            complexity_score = complexity["complexity_score"]
            
            # Initialize process suitability list
            process_suitability = []
            
            # Check each manufacturing process
            for process in ProcessType:
                # Skip processes that are clearly not suitable for the material
                if not self._is_material_compatible_with_process(material, process):
                    continue
                
                # Calculate base suitability score (0-100)
                base_score = 100.0
                
                # Adjust for complexity
                if complexity_score > 70 and process in [ProcessType.INJECTION_MOLDING, ProcessType.CASTING]:
                    base_score -= (complexity_score - 70) * 1.5
                elif complexity_score > 80 and process == ProcessType.CNC_MILLING:
                    base_score -= (complexity_score - 80) * 2
                elif complexity_score < 30 and process in [ProcessType.FDM_PRINTING, ProcessType.SLA_PRINTING]:
                    base_score -= (30 - complexity_score) * 1.5  # 3D printing is good for complex parts
                
                # Adjust for production volume
                volume_threshold = self.volume_thresholds.get(process, 500)
                if production_volume < volume_threshold * 0.2 and process in [ProcessType.INJECTION_MOLDING, ProcessType.FORGING]:
                    base_score -= 30  # High tooling cost processes are less suitable for low volumes
                elif production_volume > volume_threshold * 5 and process in [ProcessType.CNC_MILLING, ProcessType.FDM_PRINTING]:
                    base_score -= 20  # Low throughput processes are less suitable for high volumes
                
                # Adjust for part size
                bb = cad_geometry.bounding_box
                max_dim = max(bb.length, bb.width, bb.height)
                if max_dim > 500 and process in [ProcessType.SLA_PRINTING, ProcessType.SLS_PRINTING]:
                    base_score -= 30  # Size limitations for some processes
                elif max_dim < 50 and process in [ProcessType.FORGING, ProcessType.CASTING]:
                    base_score -= 15  # Too small for some processes
                
                # Calculate final score and determine rating
                final_score = max(0, min(100, base_score))
                
                if final_score >= 85:
                    rating = "excellent"
                elif final_score >= 70:
                    rating = "good"
                elif final_score >= 50:
                    rating = "fair"
                else:
                    rating = "poor"
                
                # Estimate unit cost (simplified model)
                unit_cost = self._estimate_unit_cost(process, material, production_volume, complexity_score)
                
                # Estimate lead time in days
                lead_time = self._estimate_lead_time(process, production_volume)
                
                # Get process advantages and limitations
                advantages, limitations = self._get_process_characteristics(process)
                
                # Create process suitability object
                suitability = ProcessSuitability(
                    process=process,
                    suitability_score=round(final_score, 1),
                    manufacturability=rating,
                    estimated_unit_cost=round(unit_cost, 2),
                    estimated_lead_time=lead_time,
                    advantages=advantages,
                    limitations=limitations
                )
                
                process_suitability.append(suitability)
            
            # Sort by suitability score (descending)
            process_suitability.sort(key=lambda x: x.suitability_score, reverse=True)
            
            return process_suitability
            
        except Exception as e:
            logger.error(f"Error recommending processes: {e}")
            # Return a default recommendation
            return [ProcessSuitability(
                process=ProcessType.CNC_MILLING,
                suitability_score=70.0,
                manufacturability="good",
                estimated_unit_cost=100.0,
                estimated_lead_time=10,
                advantages=["Versatile process", "Good for prototypes"],
                limitations=["Higher cost for high volumes"]
            )]
    
    def _is_material_compatible_with_process(self, material: MaterialType, process: ProcessType) -> bool:
        """
        Check if material is compatible with manufacturing process
        
        Args:
            material: Material type
            process: Manufacturing process
            
        Returns:
            True if compatible, False otherwise
        """
        # Define material-process compatibility matrix
        compatibility = {
            MaterialType.ABS: [
                ProcessType.INJECTION_MOLDING, 
                ProcessType.FDM_PRINTING,
                ProcessType.CNC_MILLING
            ],
            MaterialType.PLA: [
                ProcessType.FDM_PRINTING,
                ProcessType.CNC_MILLING
            ],
            MaterialType.PETG: [
                ProcessType.INJECTION_MOLDING,
                ProcessType.FDM_PRINTING
            ],
            MaterialType.NYLON: [
                ProcessType.INJECTION_MOLDING,
                ProcessType.SLS_PRINTING,
                ProcessType.CNC_MILLING
            ],
            MaterialType.POLYCARBONATE: [
                ProcessType.INJECTION_MOLDING,
                ProcessType.FDM_PRINTING,
                ProcessType.CNC_MILLING
            ],
            MaterialType.ALUMINUM: [
                ProcessType.CNC_MILLING,
                ProcessType.CNC_TURNING,
                ProcessType.CASTING,
                ProcessType.FORGING,
                ProcessType.SHEET_METAL,
                ProcessType.EXTRUSION
            ],
            MaterialType.STEEL: [
                ProcessType.CNC_MILLING,
                ProcessType.CNC_TURNING,
                ProcessType.FORGING,
                ProcessType.SHEET_METAL
            ],
            MaterialType.STAINLESS_STEEL: [
                ProcessType.CNC_MILLING,
                ProcessType.CNC_TURNING,
                ProcessType.SHEET_METAL
            ]
        }
        
        # Check compatibility
        compatible_processes = compatibility.get(material, [])
        return process in compatible_processes
    
    def _estimate_unit_cost(self, process: ProcessType, material: MaterialType, 
                           production_volume: int, complexity_score: float) -> float:
        """
        Estimate unit cost for a given process, material and volume
        
        Args:
            process: Manufacturing process
            material: Material type
            production_volume: Production quantity
            complexity_score: Complexity score (0-100)
            
        Returns:
            Estimated unit cost
        """
        # Base material costs per cubic cm (simplified)
        material_cost_per_cc = {
            MaterialType.ABS: 0.05,
            MaterialType.PLA: 0.04,
            MaterialType.PETG: 0.06,
            MaterialType.NYLON: 0.08,
            MaterialType.POLYCARBONATE: 0.09,
            MaterialType.ALUMINUM: 0.15,
            MaterialType.STEEL: 0.12,
            MaterialType.STAINLESS_STEEL: 0.18,
            MaterialType.BRASS: 0.25,
            MaterialType.COPPER: 0.30,
            MaterialType.TITANIUM: 0.90
        }
        
        # Base process costs
        process_cost_factor = {
            ProcessType.INJECTION_MOLDING: 0.8,
            ProcessType.CNC_MILLING: 2.5,
            ProcessType.CNC_TURNING: 2.0,
            ProcessType.FDM_PRINTING: 1.8,
            ProcessType.SLA_PRINTING: 2.2,
            ProcessType.SLS_PRINTING: 2.5,
            ProcessType.SHEET_METAL: 1.5,
            ProcessType.CASTING: 1.2,
            ProcessType.FORGING: 1.0,
            ProcessType.EXTRUSION: 0.7
        }
        
        # Tooling costs amortized over production volume
        tooling_cost = {
            ProcessType.INJECTION_MOLDING: 15000,
            ProcessType.CNC_MILLING: 500,
            ProcessType.CNC_TURNING: 300,
            ProcessType.FDM_PRINTING: 0,
            ProcessType.SLA_PRINTING: 0,
            ProcessType.SLS_PRINTING: 0,
            ProcessType.SHEET_METAL: 1000,
            ProcessType.CASTING: 5000,
            ProcessType.FORGING: 8000,
            ProcessType.EXTRUSION: 4000
        }
        
        # Get base costs
        material_cost = material_cost_per_cc.get(material, 0.1) * 100  # Assume 100cc average volume
        process_factor = process_cost_factor.get(process, 1.0)
        tooling = tooling_cost.get(process, 0)
        
        # Calculate amortized tooling cost
        amortized_tooling = tooling / max(1, production_volume)
        
        # Calculate complexity factor (1.0 - 3.0)
        complexity_factor = 1.0 + (complexity_score / 50.0)
        
        # Calculate volume discount factor (0.5 - 1.0)
        volume_discount = max(0.5, min(1.0, 1.0 - (math.log10(max(1, production_volume)) / 10)))
        
        # Calculate unit cost
        unit_cost = (material_cost + (process_factor * 50 * complexity_factor)) * volume_discount + amortized_tooling
        
        return max(1.0, unit_cost)  # Minimum $1.00 cost
    
    def _estimate_lead_time(self, process: ProcessType, production_volume: int) -> int:
        """
        Estimate lead time in days for a given process and volume
        
        Args:
            process: Manufacturing process
            production_volume: Production quantity
            
        Returns:
            Estimated lead time in days
        """
        # Base lead times (days)
        base_lead_time = {
            ProcessType.INJECTION_MOLDING: 21,  # Includes tooling time
            ProcessType.CNC_MILLING: 5,
            ProcessType.CNC_TURNING: 4,
            ProcessType.FDM_PRINTING: 2,
            ProcessType.SLA_PRINTING: 3,
            ProcessType.SLS_PRINTING: 4,
            ProcessType.SHEET_METAL: 7,
            ProcessType.CASTING: 14,
            ProcessType.FORGING: 21,
            ProcessType.EXTRUSION: 14
        }
        
        # Production rate (units per day)
        production_rate = {
            ProcessType.INJECTION_MOLDING: 5000,
            ProcessType.CNC_MILLING: 20,
            ProcessType.CNC_TURNING: 30,
            ProcessType.FDM_PRINTING: 5,
            ProcessType.SLA_PRINTING: 8,
            ProcessType.SLS_PRINTING: 15,
            ProcessType.SHEET_METAL: 100,
            ProcessType.CASTING: 200,
            ProcessType.FORGING: 300,
            ProcessType.EXTRUSION: 500
        }
        
        # Get base lead time and production rate
        base_time = base_lead_time.get(process, 7)
        rate = production_rate.get(process, 10)
        
        # Calculate production time based on volume and rate
        production_time = math.ceil(production_volume / rate)
        
        # Calculate total lead time (base + production)
        total_lead_time = base_time + production_time
        
        return max(1, total_lead_time)  # Minimum 1 day
    
    def _get_process_characteristics(self, process: ProcessType) -> Tuple[List[str], List[str]]:
        """
        Get advantages and limitations for a manufacturing process
        
        Args:
            process: Manufacturing process
            
        Returns:
            Tuple of (advantages, limitations)
        """
        characteristics = {
            ProcessType.INJECTION_MOLDING: (
                ["High production rates", "Low unit cost at high volumes", "Excellent repeatability", "Complex geometries possible"],
                ["High initial tooling cost", "Long lead time for tooling", "Design constraints for moldability", "Minimum wall thickness requirements"]
            ),
            ProcessType.CNC_MILLING: (
                ["Excellent accuracy and precision", "Wide material compatibility", "No tooling required", "Good for prototypes and low volumes"],
                ["Higher unit cost", "Limited geometric complexity", "Slower production rate", "Material waste"]
            ),
            ProcessType.CNC_TURNING: (
                ["Excellent for cylindrical parts", "Good surface finish", "High precision", "Cost-effective for appropriate geometries"],
                ["Limited to rotationally symmetric parts", "Material waste", "Size limitations"]
            ),
            ProcessType.FDM_PRINTING: (
                ["No tooling required", "Fast prototyping", "Complex geometries possible", "Low startup cost"],
                ["Lower strength", "Visible layer lines", "Slow production rate", "Limited material options"]
            ),
            ProcessType.SLA_PRINTING: (
                ["Excellent surface finish", "High detail resolution", "Complex geometries possible", "No tooling required"],
                ["Limited material properties", "Post-processing required", "Slow production rate", "Size limitations"]
            ),
            ProcessType.SLS_PRINTING: (
                ["No support structures needed", "Complex geometries possible", "Good mechanical properties", "No tooling required"],
                ["Rough surface finish", "Limited material options", "Slower production rate", "Higher cost than FDM"]
            ),
            ProcessType.SHEET_METAL: (
                ["Fast production", "Low tooling cost", "Good strength-to-weight ratio", "Suitable for large parts"],
                ["Limited to sheet-based geometries", "Minimum bend radius constraints", "Limited material thickness range"]
            ),
            ProcessType.CASTING: (
                ["Complex internal geometries possible", "Good for large parts", "Wide material options", "Good for high volumes"],
                ["Tooling required", "Longer lead times", "Draft angles required", "Surface finish limitations"]
            ),
            ProcessType.FORGING: (
                ["Excellent strength properties", "Good material grain structure", "Good for high-stress parts", "Cost-effective at high volumes"],
                ["High tooling costs", "Limited to certain geometries", "Draft angles required", "Size limitations"]
            ),
            ProcessType.EXTRUSION: (
                ["Very cost-effective for high volumes", "Consistent cross-section", "Long continuous parts possible", "Good surface finish"],
                ["Limited to constant cross-section", "Tooling required", "Size and shape limitations"]
            )
        }
        
        return characteristics.get(process, (["Standard manufacturing process"], ["Process-specific limitations apply"]))
    
    def extract_production_cad_data(self, cad_geometry: CADGeometry, material: MaterialType, 
                                   production_volume: int) -> Dict[str, Any]:
        """
        Extract comprehensive production CAD data with manufacturing intelligence
        
        Args:
            cad_geometry: CAD geometry object
            material: Material type
            production_volume: Production quantity
            
        Returns:
            Dictionary with comprehensive production data
        """
        try:
            logger.info(f"Extracting production CAD data for {cad_geometry.part_name}")
            
            # Generate unique analysis ID
            analysis_id = hashlib.md5(f"{cad_geometry.part_name}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
            
            # Perform complexity analysis
            complexity_data = self.analyze_complexity(cad_geometry)
            
            # Get manufacturability assessment for multiple processes
            manufacturability = {}
            for process in [ProcessType.INJECTION_MOLDING, ProcessType.CNC_MILLING, ProcessType.FDM_PRINTING]:
                if self._is_material_compatible_with_process(material, process):
                    manufacturability[process.value] = self.assess_manufacturability(cad_geometry, process)
            
            # Get machining time estimate
            machining_time = self.estimate_machining_time(cad_geometry, material)
            
            # Get process recommendations
            process_recommendations = self.recommend_processes(cad_geometry, material, production_volume)
            
            # Extract top recommended process
            top_process = process_recommendations[0] if process_recommendations else None
            
            # Compile comprehensive production data
            production_data = {
                "analysis_id": analysis_id,
                "part_info": {
                    "name": cad_geometry.part_name,
                    "volume_cm3": round(cad_geometry.volume, 2),
                    "surface_area_cm2": round(cad_geometry.surface_area, 2),
                    "dimensions_mm": {
                        "length": round(cad_geometry.bounding_box.length, 1),
                        "width": round(cad_geometry.bounding_box.width, 1),
                        "height": round(cad_geometry.bounding_box.height, 1)
                    },
                    "material": material.value,
                    "production_volume": production_volume
                },
                "complexity_analysis": complexity_data,
                "manufacturability": manufacturability,
                "machining_estimates": machining_time,
                "process_recommendations": [
                    {
                        "process": p.process.value,
                        "suitability_score": p.suitability_score,
                        "manufacturability": p.manufacturability,
                        "estimated_unit_cost": p.estimated_unit_cost,
                        "estimated_lead_time_days": p.estimated_lead_time,
                        "advantages": p.advantages,
                        "limitations": p.limitations
                    } for p in process_recommendations[:3]  # Top 3 recommendations
                ],
                "features": {
                    "hole_count": len(cad_geometry.holes),
                    "thin_wall_count": len(cad_geometry.thin_walls),
                    "face_count": cad_geometry.faces if cad_geometry.faces else "Unknown"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Add recommended manufacturing approach
            if top_process:
                production_data["recommended_approach"] = {
                    "process": top_process.process.value,
                    "estimated_unit_cost": top_process.estimated_unit_cost,
                    "estimated_lead_time_days": top_process.estimated_lead_time,
                    "key_considerations": top_process.advantages[:2]  # Top 2 advantages
                }
            
            logger.info(f"Successfully extracted production data for {cad_geometry.part_name}")
            return production_data
            
        except Exception as e:
            logger.error(f"Error extracting production CAD data: {e}")
            return {
                "analysis_id": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
