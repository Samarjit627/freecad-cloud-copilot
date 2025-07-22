"""
Manufacturing Tool Recommendation Cloud Service Integration
Provides tool selection and optimization capabilities through cloud services
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

class ToolService:
    """Manufacturing tool recommendation service"""
    
    def __init__(self, config_path=None):
        """Initialize the tool recommendation service"""
        self.service_handler = CloudServiceHandler(config_path)
        self.last_recommendations = None
        
    def recommend_tools(self, cad_data=None, manufacturing_process="cnc_machining", 
                       material="aluminum", machine_type=None):
        """
        Get tool recommendations for manufacturing the current model
        
        Args:
            cad_data: Pre-extracted CAD data or None to extract from active document
            manufacturing_process: Target manufacturing process
            material: Material to be machined
            machine_type: Specific machine type if applicable
            
        Returns:
            Dict containing tool recommendations
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
                "material": material,
                "machine_type": machine_type,
                "analysis_type": "tool_recommendation",
                "detail_level": "comprehensive"
            }
            
            # Call the tool recommendation service
            result = self.service_handler.call_service("tool_recommendation", payload)
            
            # Store the recommendations
            if result.get("success", False):
                self.last_recommendations = result.get("data", {})
                
            return result
            
        except Exception as e:
            print(f"Error in tool recommendation: {str(e)}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "service": "tool_recommendation",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
    
    def get_recommended_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of recommended tools from the last analysis
        
        Returns:
            List of tool recommendations with details
        """
        if not self.last_recommendations:
            return []
            
        return self.last_recommendations.get("recommended_tools", [])
    
    def get_tool_paths(self) -> List[Dict[str, Any]]:
        """
        Get suggested tool paths from the last analysis
        
        Returns:
            List of tool paths with details
        """
        if not self.last_recommendations:
            return []
            
        return self.last_recommendations.get("tool_paths", [])
    
    def get_machining_parameters(self) -> Dict[str, Any]:
        """
        Get recommended machining parameters from the last analysis
        
        Returns:
            Dict with machining parameters
        """
        if not self.last_recommendations:
            return {}
            
        return self.last_recommendations.get("machining_parameters", {})
    
    def optimize_tool_selection(self, cad_data=None, optimization_goal="time"):
        """
        Optimize tool selection based on specific goals
        
        Args:
            cad_data: Pre-extracted CAD data or None to extract from active document
            optimization_goal: Goal for optimization (time, quality, cost)
            
        Returns:
            Dict containing optimized tool recommendations
        """
        try:
            # Get CAD data if not provided
            if cad_data is None:
                from utils.cad_extractor import extract_cad_data_for_features
                cad_data = extract_cad_data_for_features()
            
            # Prepare payload
            payload = {
                "cad_data": cad_data,
                "optimization_goal": optimization_goal,
                "analysis_type": "tool_optimization",
                "detail_level": "comprehensive"
            }
            
            # Call the tool optimization service
            result = self.service_handler.call_service("tool_recommendation", payload)
            
            # Store the recommendations
            if result.get("success", False):
                self.last_recommendations = result.get("data", {})
                
            return result
            
        except Exception as e:
            print(f"Error in tool optimization: {str(e)}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "service": "tool_optimization",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
    
    def visualize_tool_paths(self, doc=None):
        """
        Create visual representation of tool paths in the 3D view
        
        Args:
            doc: FreeCAD document (uses active document if None)
            
        Returns:
            Boolean indicating success
        """
        try:
            # Get the document
            if doc is None:
                if not FreeCAD.ActiveDocument:
                    print("No active document")
                    return False
                doc = FreeCAD.ActiveDocument
            
            # Check if we have tool paths
            tool_paths = self.get_tool_paths()
            if not tool_paths:
                print("No tool paths available")
                return False
            
            # Create a group for the tool paths
            path_group = doc.addObject("App::DocumentObjectGroup", "Tool_Paths")
            
            # Create visual representation for each tool path
            for i, path in enumerate(tool_paths):
                if "points" not in path:
                    continue
                    
                points = path.get("points", [])
                if not points or len(points) < 2:
                    continue
                
                # Create a polyline for the path
                polyline = []
                for point in points:
                    x = point.get("x", 0)
                    y = point.get("y", 0)
                    z = point.get("z", 0)
                    polyline.append(FreeCAD.Vector(x, y, z))
                
                # Create a wire from the points
                wire = Part.makePolygon(polyline)
                path_obj = doc.addObject("Part::Feature", f"Path_{i+1}")
                path_obj.Shape = wire
                
                # Set color based on tool type
                tool_type = path.get("tool_type", "")
                if hasattr(path_obj, "ViewObject"):
                    if "roughing" in tool_type.lower():
                        path_obj.ViewObject.LineColor = (1.0, 0.0, 0.0)  # Red
                    elif "finishing" in tool_type.lower():
                        path_obj.ViewObject.LineColor = (0.0, 0.0, 1.0)  # Blue
                    else:
                        path_obj.ViewObject.LineColor = (0.0, 1.0, 0.0)  # Green
                    
                    # Make the line thicker
                    if hasattr(path_obj.ViewObject, "LineWidth"):
                        path_obj.ViewObject.LineWidth = 2.0
                
                # Add to the group
                path_group.addObject(path_obj)
            
            # Recompute the document
            doc.recompute()
            return True
            
        except Exception as e:
            print(f"Error visualizing tool paths: {str(e)}")
            traceback.print_exc()
            return False
    
    def export_tool_paths(self, file_path=None, format="gcode"):
        """
        Export tool paths to a file
        
        Args:
            file_path: Path to save the file (if None, uses desktop)
            format: Export format (gcode, step, etc.)
            
        Returns:
            Boolean indicating success and path to the exported file
        """
        try:
            # Check if we have tool paths
            tool_paths = self.get_tool_paths()
            if not tool_paths:
                print("No tool paths available")
                return False, None
            
            # Generate default file path if not provided
            if file_path is None:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                file_path = os.path.join(desktop, f"tool_paths_{timestamp}.{format}")
            
            # Prepare the export data
            export_data = {
                "tool_paths": tool_paths,
                "machining_parameters": self.get_machining_parameters(),
                "recommended_tools": self.get_recommended_tools(),
                "export_format": format,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            # Write to file
            with open(file_path, 'w') as f:
                if format.lower() == "json":
                    json.dump(export_data, f, indent=2)
                else:
                    # For gcode and other formats, we'd need to convert the data
                    # This is a simplified version that just writes a basic representation
                    f.write(f"; Tool path export generated by FreeCAD CoPilot\n")
                    f.write(f"; Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    for i, tool in enumerate(self.get_recommended_tools()):
                        f.write(f"; Tool {i+1}: {tool.get('name', 'Unknown')}\n")
                        f.write(f"; Diameter: {tool.get('diameter', 0)}mm\n")
                        f.write(f"; Type: {tool.get('type', 'Unknown')}\n\n")
                    
                    for i, path in enumerate(tool_paths):
                        f.write(f"; Path {i+1}: {path.get('name', f'Path {i+1}')}\n")
                        f.write(f"; Tool: {path.get('tool_name', 'Unknown')}\n")
                        f.write(f"G0 Z10 ; Safe height\n")
                        
                        points = path.get("points", [])
                        for j, point in enumerate(points):
                            x = point.get("x", 0)
                            y = point.get("y", 0)
                            z = point.get("z", 0)
                            
                            if j == 0:
                                # Rapid move to first point
                                f.write(f"G0 X{x:.3f} Y{y:.3f}\n")
                                f.write(f"G1 Z{z:.3f} F100\n")
                            else:
                                # Linear move to subsequent points
                                f.write(f"G1 X{x:.3f} Y{y:.3f} Z{z:.3f} F200\n")
                        
                        f.write(f"G0 Z10 ; Return to safe height\n\n")
                    
                    f.write("M30 ; End of program\n")
            
            print(f"Tool paths exported to: {file_path}")
            return True, file_path
            
        except Exception as e:
            print(f"Error exporting tool paths: {str(e)}")
            traceback.print_exc()
            return False, None
