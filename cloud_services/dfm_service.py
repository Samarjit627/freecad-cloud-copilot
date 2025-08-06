"""
Design for Manufacturing (DFM) Cloud Service Integration
Provides DFM analysis capabilities through cloud services
"""

import os
import sys
import json
import time
import traceback
from typing import Dict, Any, Optional, List, Tuple

# Try to import FreeCAD modules
try:
    import FreeCAD
    import Part
except ImportError:
    print("Warning: FreeCAD modules not available in this context")

# Import cloud service handler
try:
    from cloud_services.service_handler import CloudServiceHandler
except ImportError:
    # Adjust path for direct execution
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from cloud_services.service_handler import CloudServiceHandler

class DFMService:
    """Design for Manufacturing analysis service"""
    
    def __init__(self, config_path=None):
        """Initialize the DFM service"""
        self.service_handler = CloudServiceHandler(config_path)
        self.last_analysis = None
        self.cost_analysis = None
        
    def analyze_model(self, cad_data=None, manufacturing_process="INJECTION_MOLDING", material="ABS", production_volume=1000, advanced_analysis=True):
        """
        Analyze the current model for manufacturing issues using industry-grade DFM analysis
        
        Args:
            cad_data: Pre-extracted CAD data or None to extract from active document
            manufacturing_process: Target manufacturing process (INJECTION_MOLDING, CNC_MILLING, FDM_PRINTING)
            material: Target material (ABS, PLA, ALUMINUM, etc.)
            production_volume: Production quantity
            advanced_analysis: Whether to use the advanced industry-grade DFM engine
            
        Returns:
            Dict containing DFM analysis results
        """
        try:
            # Get CAD data if not provided
            if cad_data is None:
                from utils.cad_extractor import extract_cad_data_for_features
                cad_data = extract_cad_data_for_features()
            
            # Convert CAD data to the format expected by the DFM engine
            dimensions = cad_data.get("dimensions", {})
            features = cad_data.get("features", {})
            
            # Extract or create holes and walls data
            holes_data = features.get("holes_data", [])
            walls_data = features.get("walls_data", [])
            
            # If no detailed hole data available but we know the count, create placeholder data
            if not holes_data and "holes" in features and features["holes"] > 0:
                # Create placeholder data based on bounding box
                bbox_length = dimensions.get("length", 100)
                bbox_width = dimensions.get("width", 100)
                bbox_height = dimensions.get("height", 50)
                
                for i in range(features["holes"]):
                    # Position holes at reasonable locations within the bounding box
                    x = bbox_length * (0.25 + (i % 3) * 0.25)
                    y = bbox_width * (0.25 + ((i // 3) % 3) * 0.25)
                    z = bbox_height * 0.5
                    
                    holes_data.append({
                        "diameter": 5.0,  # Default 5mm diameter
                        "depth": 10.0,   # Default 10mm depth
                        "location": [x, y, z]
                    })
            
            # If no detailed wall data available, create placeholder data
            if not walls_data and "thin_walls" in features and features["thin_walls"] > 0:
                bbox_length = dimensions.get("length", 100)
                bbox_width = dimensions.get("width", 100)
                bbox_height = dimensions.get("height", 50)
                
                for i in range(features["thin_walls"]):
                    # Position walls at reasonable locations
                    x = bbox_length * (0.25 + (i % 2) * 0.5)
                    y = bbox_width * 0.5
                    z = bbox_height * 0.5
                    
                    walls_data.append({
                        "thickness": 1.5,  # Default 1.5mm thickness
                        "location": [x, y, z]
                    })
            
            # Prepare geometry data for DFM analysis
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
                "holes": holes_data,
                "thin_walls": walls_data
            }
            
            # Convert process and material to lowercase with underscores for API compatibility
            process_mapping = {
                "INJECTION_MOLDING": "injection_molding",
                "CNC_MILLING": "cnc_milling",
                "CNC_TURNING": "cnc_turning",
                "FDM_PRINTING": "fdm_printing",
                "SLA_PRINTING": "sla_printing",
                "SLS_PRINTING": "sls_printing",
                "SHEET_METAL": "sheet_metal"
            }
            
            material_mapping = {
                "ABS": "abs",
                "PLA": "pla",
                "PETG": "petg",
                "NYLON": "nylon",
                "ALUMINUM": "aluminum",
                "STEEL": "steel",
                "BRASS": "brass"
            }
            
            # Map to correct API format
            api_process = process_mapping.get(manufacturing_process, manufacturing_process.lower())
            api_material = material_mapping.get(material, material.lower())
            
            # Prepare the payload for the DFM analysis API
            # When using /api/analysis/cad endpoint, we need to structure the payload differently
            payload = {
                "cad_data": {
                    "dimensions": dimensions,
                    "features": features
                },
                "user_requirements": {
                    "target_process": api_process,
                    "material": api_material,
                    "production_volume": production_volume,
                    "use_advanced_dfm": advanced_analysis,
                    "include_cost_analysis": True,
                    "include_alternative_processes": True
                }
            }
            
            # Call the advanced DFM service
            result = self.service_handler.call_service("dfm", payload)
            
            # Store the analysis results
            if result.get("success", False):
                print("✅ DFM analysis successful, processing results")
                response_data = result.get("data", {})
                
                # Debug: Print the structure of the response
                print(f"DEBUG: Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not a dictionary'}")
                
                # Handle the response from /api/analysis/cad endpoint
                # The response structure is different from the /api/analysis/dfm endpoint
                # We need to transform it to match what our DFM service expects
                
                # Create a compatible structure for our DFM service
                transformed_data = {}
                
                # Extract design issues and convert to manufacturing_issues format
                if "design_issues" in response_data:
                    print(f"\u2705 Found {len(response_data['design_issues'])} design issues")
                    manufacturing_issues = []
                    for issue in response_data["design_issues"]:
                        # Handle both string and dictionary formats for issues
                        if isinstance(issue, str):
                            print(f"DEBUG: Found string issue: {issue}")
                            manufacturing_issues.append({
                                "title": "Design Issue",
                                "severity": "medium",
                                "description": issue,
                                "recommendation": "Review design for manufacturability",
                            })
                        else:
                            # Handle dictionary format
                            manufacturing_issues.append({
                                "title": issue.get("title", "Design Issue"),
                                "severity": issue.get("severity", "medium"),
                                "description": issue.get("description", ""),
                                "recommendation": issue.get("recommendation", ""),
                            })
                    transformed_data["manufacturing_issues"] = manufacturing_issues
                
                # Extract manufacturing features and convert to our format
                if "manufacturing_features" in response_data:
                    features = response_data["manufacturing_features"]
                    print(f"✅ Found manufacturing features data")
                    
                    # Extract manufacturability score
                    if "moldability_score" in features:
                        # Convert from 0-10 scale to 0-100 scale
                        score = features["moldability_score"] * 10
                        transformed_data["overall_manufacturability_score"] = score
                        
                        # Determine overall rating based on score
                        if score < 40:
                            transformed_data["overall_rating"] = "poor"
                        elif score < 60:
                            transformed_data["overall_rating"] = "fair"
                        elif score < 80:
                            transformed_data["overall_rating"] = "good"
                        else:
                            transformed_data["overall_rating"] = "excellent"
                
                # Extract process recommendations
                if "process_recommendations" in response_data:
                    processes = response_data["process_recommendations"]
                    if processes and len(processes) > 0:
                        print(f"✅ Found {len(processes)} process recommendations")
                        print(f"DEBUG: Process recommendations type: {type(processes)}")
                        
                        # Handle different types of process recommendations
                        if isinstance(processes, str):
                            # If it's a single string
                            print(f"DEBUG: Single string process recommendation: {processes}")
                            processes = [processes]  # Convert to list
                        elif isinstance(processes, dict):
                            # If it's a dictionary
                            print(f"DEBUG: Dictionary process recommendation: {processes}")
                            processes = [str(processes)]  # Convert to list with string representation
                        
                        # Create primary process
                        primary_process = {
                            "process": str(processes[0]),  # Ensure it's a string
                            "suitability_score": transformed_data.get("overall_manufacturability_score", 70),
                            "manufacturability": transformed_data.get("overall_rating", "good"),
                            "estimated_unit_cost": 10.0,  # Default value
                            "estimated_lead_time": 14,    # Default value in days
                            "advantages": ["Recommended by analysis"],
                            "limitations": []
                        }
                        transformed_data["primary_process"] = primary_process
                        
                        # Create alternative processes
                        if len(processes) > 1:
                            alternative_processes = []
                            for proc in processes[1:3]:  # Take up to 2 alternatives
                                alt_proc = {
                                    "process": str(proc),  # Ensure it's a string
                                    "suitability_score": max(30, transformed_data.get("overall_manufacturability_score", 70) - 20),
                                    "manufacturability": "fair",
                                    "estimated_unit_cost": 15.0,  # Default value
                                    "estimated_lead_time": 21,    # Default value in days
                                    "advantages": ["Alternative manufacturing method"],
                                    "limitations": ["May require design modifications"]
                                }
                                alternative_processes.append(alt_proc)
                            transformed_data["alternative_processes"] = alternative_processes
                
                # Extract material suggestions
                if "material_suggestions" in response_data and response_data["material_suggestions"]:
                    material_suggestions = response_data["material_suggestions"]
                    print(f"✅ Found material suggestions: {material_suggestions}")
                    
                    # Handle different types of material suggestions
                    recommendations = []
                    if isinstance(material_suggestions, list):
                        # Handle list of materials
                        for material in material_suggestions[:3]:
                            if material:
                                recommendations.append(f"Consider using {material} for optimal results")
                    elif isinstance(material_suggestions, str):
                        # Handle single string material
                        recommendations.append(f"Consider using {material_suggestions} for optimal results")
                    elif isinstance(material_suggestions, dict):
                        # Handle dictionary format
                        for material_name, details in list(material_suggestions.items())[:3]:
                            recommendations.append(f"Consider using {material_name} for optimal results")
                    
                    if recommendations:
                        transformed_data["expert_recommendations"] = recommendations
                    else:
                        # Add a default recommendation if none were created
                        transformed_data["expert_recommendations"] = ["Consider consulting with a manufacturing expert for material selection"]
                
                # Store the transformed data
                self.last_analysis = transformed_data
                print(f"DEBUG: Transformed data keys: {list(self.last_analysis.keys())}")
                
            else:
                print(f"❌ DFM analysis failed: {result.get('error', 'Unknown error')}")
                self.last_analysis = {}
                
            return result
            
        except Exception as e:
            print(f"Error in DFM analysis: {str(e)}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "service": "dfm",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
    
    def get_dfm_issues(self) -> List[Dict[str, Any]]:
        """
        Get list of DFM issues from the last analysis
        
        Returns:
            List of DFM issues with severity, description, and recommendations
        """
        print("DEBUG: get_dfm_issues called")
        if not self.last_analysis:
            print("DEBUG: No last_analysis data available")
            return []
        
        print(f"DEBUG: last_analysis keys: {list(self.last_analysis.keys())}")
        
        # Extract issues from the analysis - handle both old and new formats
        issues = []
        
        # Check for critical issues from advanced DFM engine
        if "critical_issues" in self.last_analysis:
            for issue in self.last_analysis.get("critical_issues", []):
                issues.append({
                    "severity": "high",
                    "title": issue.get("title", "Critical Issue"),
                    "description": issue.get("description", ""),
                    "recommendation": issue.get("recommendation", ""),
                    "position": issue.get("location", {"x": 0, "y": 0, "z": 0})
                })
        
        # Check for regular manufacturing issues from advanced DFM engine
        if "manufacturing_issues" in self.last_analysis:
            for issue in self.last_analysis.get("manufacturing_issues", []):
                severity = "medium"
                if issue.get("severity") == "HIGH":
                    severity = "high"
                elif issue.get("severity") == "LOW":
                    severity = "low"
                
                issues.append({
                    "severity": severity,
                    "title": issue.get("title", "Manufacturing Issue"),
                    "description": issue.get("description", ""),
                    "recommendation": issue.get("recommendation", ""),
                    "position": issue.get("location", {"x": 0, "y": 0, "z": 0})
                })
        
        # Fall back to legacy format if no issues found yet
        if not issues:
            issues = self.last_analysis.get("issues", [])
        
        print(f"DEBUG: Returning {len(issues)} DFM issues")
        if issues:
            print(f"DEBUG: First issue: {issues[0]}")
            
        return issues
    
    def get_manufacturability_score(self) -> float:
        """
        Get the overall manufacturability score from the last analysis
        
        Returns:
            Float score from 0-100 representing manufacturability
        """
        print("DEBUG: get_manufacturability_score called")
        if not self.last_analysis:
            print("DEBUG: No last_analysis data available for score")
            return 0.0
        
        # Check for advanced DFM engine score
        if "overall_manufacturability_score" in self.last_analysis:
            score = self.last_analysis.get("overall_manufacturability_score", 0.0)
            print(f"DEBUG: Found overall_manufacturability_score: {score}")
            return score
        
        # Fall back to legacy format
        score = self.last_analysis.get("manufacturability_score", 0.0)
        print(f"DEBUG: Using legacy manufacturability_score: {score}")
        return score
    
    def get_improvement_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get recommendations for improving manufacturability
        
        Returns:
            List of recommendations with description and impact
        """
        print("DEBUG: get_improvement_recommendations called")
        if not self.last_analysis:
            print("DEBUG: No last_analysis data available for recommendations")
            return []
        
        recommendations = []
        
        # Check for expert recommendations from advanced DFM engine
        if "expert_recommendations" in self.last_analysis:
            print(f"DEBUG: Found {len(self.last_analysis['expert_recommendations'])} expert recommendations")
            for rec in self.last_analysis.get("expert_recommendations", []):
                # Handle both string and dictionary formats
                if isinstance(rec, str):
                    print(f"DEBUG: Found string recommendation: {rec}")
                    recommendations.append({
                        "description": rec,
                        "impact": "medium",
                        "category": "design"
                    })
                else:
                    impact = "medium"
                    if rec.get("impact") == "HIGH":
                        impact = "high"
                    elif rec.get("impact") == "LOW":
                        impact = "low"
                        
                    recommendations.append({
                        "description": rec.get("description", ""),
                        "impact": impact,
                        "category": rec.get("category", "design")
                    })
        
        # Fall back to legacy format if no recommendations found
        if not recommendations:
            recommendations = self.last_analysis.get("recommendations", [])
            
        return recommendations
        
    def get_cost_analysis(self) -> Dict[str, Any]:
        """
        Get detailed cost analysis from the last DFM analysis
        
        Returns:
            Dictionary with cost breakdown including material, labor, tooling, and total costs
        """
        if not self.cost_analysis:
            return {
                "total_cost": 0.0,
                "unit_cost": 0.0,
                "setup_cost": 0.0,
                "material_cost": 0.0,
                "labor_cost": 0.0,
                "tooling_cost": 0.0,
                "overhead_cost": 0.0,
                "currency": "USD"
            }
        
        # Format cost analysis data for client consumption
        result = {
            "total_cost": self.cost_analysis.get("total_cost", 0.0),
            "unit_cost": self.cost_analysis.get("unit_cost", 0.0),
            "setup_cost": self.cost_analysis.get("setup_cost", 0.0),
            "material_cost": self.cost_analysis.get("material_cost", 0.0),
            "labor_cost": self.cost_analysis.get("labor_cost", 0.0),
            "tooling_cost": self.cost_analysis.get("tooling_cost", 0.0),
            "overhead_cost": self.cost_analysis.get("overhead_cost", 0.0),
            "currency": self.cost_analysis.get("currency", "USD"),
            "production_volume": self.cost_analysis.get("production_volume", 0),
            "lead_time_days": self.cost_analysis.get("lead_time_days", 0)
        }
        
        return result
        
    def get_alternative_processes(self) -> List[Dict[str, Any]]:
        """
        Get alternative manufacturing processes from the last DFM analysis
        
        Returns:
            List of alternative processes with suitability scores and cost estimates
        """
        if not self.last_analysis or "alternative_processes" not in self.last_analysis:
            return []
        
        alternatives = []
        for process in self.last_analysis.get("alternative_processes", []):
            alternatives.append({
                "process_name": process.get("process", "UNKNOWN"),
                "suitability_score": process.get("suitability_score", 0.0),
                "estimated_cost": process.get("estimated_cost", 0.0),
                "lead_time_days": process.get("lead_time_days", 0),
                "advantages": process.get("advantages", []),
                "limitations": process.get("limitations", [])
            })
        
        return alternatives
    
    def visualize_issues(self, doc=None):
        """
        Create visual indicators for DFM issues in the 3D view
        
        Args:
            doc: FreeCAD document (uses active document if None)
        """
        try:
            # Get the document
            if doc is None:
                if not FreeCAD.ActiveDocument:
                    print("No active document")
                    return False
                doc = FreeCAD.ActiveDocument
            
            # Get all issues using our helper method
            issues = self.get_dfm_issues()
            
            if not issues:
                print("No DFM analysis results available")
                return False
            
            # Get issues with position data
            positioned_issues = [i for i in issues if "position" in i]
            
            if not positioned_issues:
                print("No positioned issues to visualize")
                return False
            
            # Remove any existing DFM analysis group
            for obj in doc.Objects:
                if obj.Name == "DFM_Analysis":
                    doc.removeObject(obj.Name)
            
            # Create a group for the visualizations
            dfm_group = doc.addObject("App::DocumentObjectGroup", "DFM_Analysis")
            
            # Create visual indicators for each issue
            for i, issue in enumerate(positioned_issues):
                pos = issue.get("position", {})
                x = pos.get("x", 0)
                y = pos.get("y", 0)
                z = pos.get("z", 0)
                
                # Create a small sphere at the issue location
                sphere = doc.addObject("Part::Sphere", f"DFM_Issue_{i+1}")
                sphere.Radius = 0.5  # 0.5mm radius - much smaller marker
                sphere.Placement.Base = FreeCAD.Vector(x, y, z)
                
                # Set color based on severity
                severity = issue.get("severity", "medium")
                if hasattr(sphere, "ViewObject"):
                    if severity == "high":
                        sphere.ViewObject.ShapeColor = (1.0, 0.0, 0.0)  # Red
                    elif severity == "medium":
                        sphere.ViewObject.ShapeColor = (1.0, 0.5, 0.0)  # Orange
                    else:
                        sphere.ViewObject.ShapeColor = (1.0, 1.0, 0.0)  # Yellow
                    
                    # Make it transparent
                    sphere.ViewObject.Transparency = 50
                
                # Add to the group
                dfm_group.addObject(sphere)
                
                # Add a label with the issue title
                if "title" in issue:
                    label = doc.addObject("App::AnnotationLabel", f"DFM_Label_{i+1}")
                    label.BasePosition = FreeCAD.Vector(x, y, z + 5)  # Position above the sphere
                    label.LabelText = issue.get("title", "Issue") 
                    dfm_group.addObject(label)
            
            # Recompute the document
            doc.recompute()
            return True
            
        except Exception as e:
            print(f"Error visualizing DFM issues: {str(e)}")
            traceback.print_exc()
            return False
