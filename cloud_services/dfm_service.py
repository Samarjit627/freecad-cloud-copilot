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
        
    def analyze_model(self, cad_data=None, manufacturing_process="3d_printing"):
        """
        Analyze the current model for manufacturing issues
        
        Args:
            cad_data: Pre-extracted CAD data or None to extract from active document
            manufacturing_process: Target manufacturing process
            
        Returns:
            Dict containing DFM analysis results
        """
        try:
            # Get CAD data if not provided
            if cad_data is None:
                from utils.cad_extractor import extract_cad_data_for_features
                cad_data = extract_cad_data_for_features()
            
            # Prepare payload
            payload = {
                "cad_data": cad_data,
                "manufacturing_process": manufacturing_process,
                "analysis_type": "dfm",
                "detail_level": "comprehensive"
            }
            
            # Call the DFM service
            result = self.service_handler.call_service("dfm", payload)
            
            # Store the analysis results
            if result.get("success", False):
                self.last_analysis = result.get("data", {})
                
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
        if not self.last_analysis:
            return []
            
        # Extract issues from the analysis
        issues = self.last_analysis.get("issues", [])
        return issues
    
    def get_manufacturability_score(self) -> float:
        """
        Get the overall manufacturability score from the last analysis
        
        Returns:
            Float score from 0-100 representing manufacturability
        """
        if not self.last_analysis:
            return 0.0
            
        return self.last_analysis.get("manufacturability_score", 0.0)
    
    def get_improvement_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get recommendations for improving manufacturability
        
        Returns:
            List of recommendations with description and impact
        """
        if not self.last_analysis:
            return []
            
        return self.last_analysis.get("recommendations", [])
    
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
            
            # Check if we have analysis results
            if not self.last_analysis or "issues" not in self.last_analysis:
                print("No DFM analysis results available")
                return False
            
            # Get issues with position data
            issues = [i for i in self.last_analysis.get("issues", []) 
                     if "position" in i]
            
            if not issues:
                print("No positioned issues to visualize")
                return False
            
            # Create a group for the visualizations
            dfm_group = doc.addObject("App::DocumentObjectGroup", "DFM_Analysis")
            
            # Create visual indicators for each issue
            for i, issue in enumerate(issues):
                pos = issue.get("position", {})
                x = pos.get("x", 0)
                y = pos.get("y", 0)
                z = pos.get("z", 0)
                
                # Create a small sphere at the issue location
                sphere = doc.addObject("Part::Sphere", f"DFM_Issue_{i+1}")
                sphere.Radius = 2.0  # 2mm radius
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
                
                # Add to the group
                dfm_group.addObject(sphere)
            
            # Recompute the document
            doc.recompute()
            return True
            
        except Exception as e:
            print(f"Error visualizing DFM issues: {str(e)}")
            traceback.print_exc()
            return False
