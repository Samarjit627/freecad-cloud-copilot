"""
DFM Engine Service
Handles Design for Manufacturability analysis
"""

import logging
import time
import random
from typing import Dict, Any, List

# Configure logging
logger = logging.getLogger(__name__)

class DFMEngine:
    """Design for Manufacturability analysis engine"""
    
    def __init__(self):
        """Initialize the DFM engine"""
        logger.info("Initializing DFM Engine")
        self.materials_db = {
            "PLA": {"cost_per_kg": 25, "density": 1.24, "min_wall_thickness": 1.0},
            "ABS": {"cost_per_kg": 30, "density": 1.05, "min_wall_thickness": 1.2},
            "PETG": {"cost_per_kg": 35, "density": 1.27, "min_wall_thickness": 1.0},
            "NYLON": {"cost_per_kg": 60, "density": 1.14, "min_wall_thickness": 1.5},
            "TPU": {"cost_per_kg": 50, "density": 1.21, "min_wall_thickness": 1.5},
            "ALUMINUM": {"cost_per_kg": 15, "density": 2.7, "min_wall_thickness": 0.8},
            "STEEL": {"cost_per_kg": 10, "density": 7.85, "min_wall_thickness": 0.5},
        }
        
        self.processes_db = {
            "FDM_PRINTING": {"setup_cost": 50, "hourly_rate": 25, "min_feature_size": 0.4},
            "SLA_PRINTING": {"setup_cost": 75, "hourly_rate": 35, "min_feature_size": 0.1},
            "SLS_PRINTING": {"setup_cost": 100, "hourly_rate": 45, "min_feature_size": 0.1},
            "CNC_MACHINING": {"setup_cost": 150, "hourly_rate": 75, "min_feature_size": 0.1},
            "INJECTION_MOLDING": {"setup_cost": 5000, "hourly_rate": 100, "min_feature_size": 0.2},
        }
    
    def analyze(self, cad_data: Dict[str, Any], material: str, process: str, 
                production_volume: int, use_advanced: bool = True) -> Dict[str, Any]:
        """
        Analyze a design for manufacturability
        
        Args:
            cad_data: CAD data including geometry, features, and metadata
            material: Material to use for manufacturing
            process: Manufacturing process to use
            production_volume: Number of units to produce
            use_advanced: Whether to use advanced analysis
            
        Returns:
            Dictionary with manufacturability score, issues, recommendations, cost, and lead time
        """
        logger.info(f"Analyzing design for material={material}, process={process}, volume={production_volume}")
        
        # Normalize inputs
        material = material.upper()
        process = process.upper()
        
        # Get material and process data
        material_data = self.materials_db.get(material, self.materials_db["PLA"])
        process_data = self.processes_db.get(process, self.processes_db["FDM_PRINTING"])
        
        # Extract geometry data
        geometry = cad_data.get("geometry", {})
        features = cad_data.get("features", [])
        metadata = cad_data.get("metadata", {})
        
        # Calculate volume and weight
        volume_cm3 = metadata.get("volume_cm3", random.uniform(10, 500))
        weight_g = volume_cm3 * material_data["density"]
        
        # Perform manufacturability analysis
        issues = self._analyze_issues(geometry, features, material_data, process_data)
        recommendations = self._generate_recommendations(issues, material, process)
        
        # Calculate manufacturability score
        base_score = 85  # Start with a good score
        penalty = min(len(issues) * 5, 40)  # Each issue reduces score, max 40 point reduction
        manufacturability_score = max(base_score - penalty, 0)
        
        # Calculate cost estimate
        cost_estimate = self._calculate_cost(
            volume_cm3, weight_g, material_data, process_data, production_volume
        )
        
        # Calculate lead time
        lead_time = self._calculate_lead_time(process, production_volume)
        
        return {
            "manufacturability_score": manufacturability_score,
            "issues": issues,
            "recommendations": recommendations,
            "cost_estimate": cost_estimate,
            "lead_time": lead_time
        }
    
    def _analyze_issues(self, geometry: Dict[str, Any], features: List[Dict[str, Any]], 
                       material_data: Dict[str, Any], process_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze design issues"""
        issues = []
        
        # Check for thin walls
        min_wall = material_data["min_wall_thickness"]
        if geometry.get("min_wall_thickness", 0) < min_wall:
            issues.append({
                "type": "thin_walls",
                "severity": "high",
                "description": f"Wall thickness below minimum ({min_wall}mm) for selected material"
            })
        
        # Check for small features
        min_feature = process_data["min_feature_size"]
        if geometry.get("min_feature_size", 0) < min_feature:
            issues.append({
                "type": "small_features",
                "severity": "medium",
                "description": f"Features smaller than minimum ({min_feature}mm) for selected process"
            })
        
        # Check for support structures needed
        # We'll check if this is an FDM printing process based on min_feature_size
        is_fdm = process_data.get("min_feature_size", 0) >= 0.3
        if geometry.get("overhangs", False) and is_fdm:
            issues.append({
                "type": "overhangs",
                "severity": "medium",
                "description": "Design has overhangs that will require support structures"
            })
        
        # Add some random issues for demonstration
        if random.random() < 0.3:
            issues.append({
                "type": "sharp_corners",
                "severity": "low",
                "description": "Sharp internal corners may cause stress concentration"
            })
            
        if random.random() < 0.3:
            issues.append({
                "type": "complex_geometry",
                "severity": "medium",
                "description": "Complex geometry may increase manufacturing time and cost"
            })
        
        return issues
    
    def _generate_recommendations(self, issues: List[Dict[str, Any]], material: str, 
                                process: str) -> List[Dict[str, Any]]:
        """Generate recommendations based on issues"""
        recommendations = []
        
        for issue in issues:
            if issue["type"] == "thin_walls":
                recommendations.append({
                    "type": "design_change",
                    "description": "Increase wall thickness to improve structural integrity"
                })
                
            elif issue["type"] == "small_features":
                recommendations.append({
                    "type": "design_change",
                    "description": "Increase size of small features or remove if non-functional"
                })
                
            elif issue["type"] == "overhangs":
                recommendations.append({
                    "type": "process_adjustment",
                    "description": "Orient the part to minimize overhangs or add chamfers to reduce support needs"
                })
                
            elif issue["type"] == "sharp_corners":
                recommendations.append({
                    "type": "design_change",
                    "description": "Add fillets to internal corners to reduce stress concentration"
                })
                
            elif issue["type"] == "complex_geometry":
                recommendations.append({
                    "type": "design_change",
                    "description": "Simplify geometry where possible to reduce manufacturing complexity"
                })
        
        # Add material or process recommendations if appropriate
        if material.upper() == "PLA" and random.random() < 0.5:
            recommendations.append({
                "type": "material_change",
                "description": "Consider PETG for better mechanical properties if the part needs durability"
            })
            
        if process.upper() == "INJECTION_MOLDING" and random.random() < 0.5:
            recommendations.append({
                "type": "design_for_process",
                "description": "Add draft angles to vertical walls to facilitate part ejection"
            })
        
        return recommendations
    
    def _calculate_cost(self, volume_cm3: float, weight_g: float, material_data: Dict[str, Any],
                      process_data: Dict[str, Any], production_volume: int) -> Dict[str, Any]:
        """Calculate manufacturing cost estimate"""
        # Material cost
        material_cost_per_part = (weight_g / 1000) * material_data["cost_per_kg"]
        
        # Setup cost amortized over production volume
        setup_cost_per_part = process_data["setup_cost"] / production_volume
        
        # Processing cost based on volume and complexity
        # Simplified calculation - in reality would depend on many factors
        processing_time_hours = (volume_cm3 / 100) * 0.5  # Simplified time calculation
        processing_cost_per_part = processing_time_hours * process_data["hourly_rate"]
        
        # Total cost per part
        unit_cost = material_cost_per_part + setup_cost_per_part + processing_cost_per_part
        
        # Apply volume discount for larger quantities
        if production_volume >= 1000:
            discount = 0.2  # 20% discount for 1000+ units
        elif production_volume >= 100:
            discount = 0.1  # 10% discount for 100+ units
        else:
            discount = 0
            
        discounted_unit_cost = unit_cost * (1 - discount)
        total_cost = discounted_unit_cost * production_volume
        
        return {
            "unit_cost": round(discounted_unit_cost, 2),
            "total_cost": round(total_cost, 2),
            "breakdown": {
                "material_cost": round(material_cost_per_part, 2),
                "setup_cost": round(setup_cost_per_part, 2),
                "processing_cost": round(processing_cost_per_part, 2),
                "discount_percentage": int(discount * 100)
            }
        }
    
    def _calculate_lead_time(self, process: str, production_volume: int) -> Dict[str, Any]:
        """Calculate manufacturing lead time"""
        # Base lead time in days
        process_upper = process.upper()
        if process_upper == "INJECTION_MOLDING":
            base_lead_time = 30  # Longer for tooling creation
        elif process_upper in ["CNC_MACHINING"]:
            base_lead_time = 10
        else:  # 3D printing processes
            base_lead_time = 5
            
        # Production time based on volume
        if production_volume <= 10:
            production_time = 1
        elif production_volume <= 100:
            production_time = 3
        elif production_volume <= 1000:
            production_time = 7
        else:
            production_time = 14
            
        # Total lead time
        total_days = base_lead_time + production_time
        
        # Add some randomness for realistic variation
        min_days = max(total_days - 2, 1)
        max_days = total_days + 3
        
        return {
            "min_days": min_days,
            "max_days": max_days,
            "typical_days": total_days
        }
