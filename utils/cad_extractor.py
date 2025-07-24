"""
Enhanced CAD Data Extractor for Cloud Features
Extracts comprehensive CAD data for use with cloud microservices
"""

import os
import sys
import json
import time
import traceback
from typing import Dict, Any, List, Optional

# Try to import FreeCAD modules
try:
    import FreeCAD
    import Part
except ImportError:
    print("Warning: FreeCAD modules not available in this context")

def get_center_of_mass(shape, axis):
    """
    Safely get the center of mass coordinate for a shape
    
    Args:
        shape: FreeCAD shape object
        axis: Coordinate axis ('x', 'y', or 'z')
        
    Returns:
        float: Coordinate value or 0.0 if not available
    """
    try:
        # For Part.Compound objects that don't have CenterOfMass directly
        if not hasattr(shape, 'CenterOfMass'):
            # Use bounding box center as fallback
            bbox = shape.BoundBox
            if axis == 'x':
                return (bbox.XMin + bbox.XMax) / 2.0
            elif axis == 'y':
                return (bbox.YMin + bbox.YMax) / 2.0
            elif axis == 'z':
                return (bbox.ZMin + bbox.ZMax) / 2.0
            return 0.0
        
        # For shapes with CenterOfMass attribute
        if axis == 'x':
            return shape.CenterOfMass.x
        elif axis == 'y':
            return shape.CenterOfMass.y
        elif axis == 'z':
            return shape.CenterOfMass.z
        return 0.0
    except Exception:
        # Return 0.0 as fallback if any error occurs
        return 0.0

def extract_cad_data_for_features():
    """
    Extract comprehensive CAD data for use with microservice features
    
    Returns:
        dict: Structured CAD data suitable for microservices
    """
    try:
        if not FreeCAD.ActiveDocument:
            return {
                "status": "no_document",
                "message": "No active FreeCAD document"
            }
            
        doc = FreeCAD.ActiveDocument
        
        # Initialize data structure
        cad_data = {
            "document": {
                "name": doc.Name,
                "object_count": len(doc.Objects),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            },
            "objects": [],
            "materials": [],
            "manufacturing_features": {},
            "dimensions": {},
            "analysis_metadata": {}
        }
        
        # Process each object
        total_volume = 0
        min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
        max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
        
        for obj in doc.Objects:
            obj_data = {
                "name": obj.Name,
                "label": obj.Label,
                "type": obj.TypeId,
                "visible": True
            }
            
            # Extract shape information if available
            if hasattr(obj, 'Shape') and obj.Shape.isValid():
                shape = obj.Shape
                bbox = shape.BoundBox
                
                # Update overall bounding box
                min_x = min(min_x, bbox.XMin)
                min_y = min(min_y, bbox.YMin)
                min_z = min(min_z, bbox.ZMin)
                max_x = max(max_x, bbox.XMax)
                max_y = max(max_y, bbox.YMax)
                max_z = max(max_z, bbox.ZMax)
                
                # Object-specific data
                obj_data.update({
                    "volume": shape.Volume,
                    "surface_area": shape.Area,
                    "dimensions": {
                        "length": bbox.XLength,
                        "width": bbox.YLength,  
                        "height": bbox.ZLength
                    },
                    "center_of_mass": {
                        "x": get_center_of_mass(shape, 'x'),
                        "y": get_center_of_mass(shape, 'y'),
                        "z": get_center_of_mass(shape, 'z')
                    },
                    "geometry": {
                        "faces": len(shape.Faces) if hasattr(shape, 'Faces') else 0,
                        "edges": len(shape.Edges) if hasattr(shape, 'Edges') else 0,
                        "vertices": len(shape.Vertexes) if hasattr(shape, 'Vertexes') else 0
                    }
                })
                
                total_volume += shape.Volume
                
                # Analyze manufacturing features
                try:
                    # Count holes (simplified detection)
                    holes = []
                    for face in shape.Faces:
                        # Look for circular faces that might be holes
                        if hasattr(face.Surface, 'Radius'):
                            holes.append({
                                "radius": face.Surface.Radius,
                                "area": face.Area
                            })
                    
                    if holes:
                        obj_data["holes"] = holes
                        
                    # Check for fillets (rounded edges)
                    fillets = []
                    for edge in shape.Edges:
                        if hasattr(edge.Curve, 'Radius'):
                            fillets.append({
                                "radius": edge.Curve.Radius,
                                "length": edge.Length
                            })
                    
                    if fillets:
                        obj_data["fillets"] = fillets
                        
                except Exception as e:
                    print(f"Warning: Could not analyze manufacturing features for {obj.Name}: {e}")
                    
            # Extract material information if available
            if hasattr(obj, 'Material'):
                material_data = {
                    "object": obj.Name,
                    "material": str(obj.Material) if obj.Material else "Unknown"
                }
                cad_data["materials"].append(material_data)
                
            cad_data["objects"].append(obj_data)
        
        # Overall document dimensions
        if max_x != float('-inf'):
            cad_data["dimensions"] = {
                "overall_length": max_x - min_x,
                "overall_width": max_y - min_y,
                "overall_height": max_z - min_z,
                "total_volume": total_volume,
                "bounding_box": {
                    "min": {"x": min_x, "y": min_y, "z": min_z},
                    "max": {"x": max_x, "y": max_y, "z": max_z}
                }
            }
            
        # Manufacturing analysis metadata
        cad_data["manufacturing_features"] = {
            "complexity_rating": estimate_complexity(cad_data),
            "estimated_print_time": estimate_print_time(total_volume),
            "material_usage": total_volume,
            "support_required": estimate_support_requirement(cad_data)
        }
        
        # Analysis metadata
        cad_data["analysis_metadata"] = {
            "extraction_method": "freecad_macro",
            "freecad_version": FreeCAD.Version(),
            "extraction_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        return cad_data
        
    except Exception as e:
        print(f"Error extracting CAD data: {str(e)}")
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

def estimate_complexity(cad_data):
    """Estimate the complexity of the model based on features"""
    try:
        # Get total counts
        total_faces = 0
        total_edges = 0
        total_vertices = 0
        total_holes = 0
        total_fillets = 0
        
        for obj in cad_data.get("objects", []):
            if "geometry" in obj:
                total_faces += obj["geometry"].get("faces", 0)
                total_edges += obj["geometry"].get("edges", 0)
                total_vertices += obj["geometry"].get("vertices", 0)
            
            total_holes += len(obj.get("holes", []))
            total_fillets += len(obj.get("fillets", []))
        
        # Simple complexity rating based on counts
        if total_faces > 100 or total_edges > 300 or total_holes > 10 or total_fillets > 20:
            return "high"
        elif total_faces > 30 or total_edges > 100 or total_holes > 5 or total_fillets > 10:
            return "medium"
        else:
            return "low"
    
    except Exception as e:
        print(f"Error estimating complexity: {str(e)}")
        return "medium"  # Default to medium

def estimate_print_time(volume, density=1.0, print_speed=60):
    """Estimate 3D printing time based on volume"""
    try:
        if volume <= 0:
            return "unknown"
            
        # Very rough estimate based on volume
        # Assuming 60mm/min print speed and average extrusion
        hours = (volume / 1000) * 2  # Rough estimate: 2 hours per 1000 cubic mm
        
        if hours < 1:
            return f"{int(hours * 60)} minutes"
        elif hours < 24:
            return f"{int(hours)} hours {int((hours % 1) * 60)} minutes"
        else:
            days = int(hours / 24)
            remaining_hours = int(hours % 24)
            return f"{days} days {remaining_hours} hours"
    
    except Exception as e:
        print(f"Error estimating print time: {str(e)}")
        return "unknown"

def estimate_support_requirement(cad_data):
    """Estimate if the model requires support structures for 3D printing"""
    try:
        # Check for overhangs by analyzing the model's geometry
        # This is a simplified approach - real support analysis is complex
        
        # If there are objects with significant height and small base area, likely needs support
        for obj in cad_data.get("objects", []):
            if "dimensions" in obj:
                dims = obj["dimensions"]
                height = dims.get("height", 0)
                base_area = dims.get("length", 0) * dims.get("width", 0)
                
                # If height is much greater than the base dimensions, might need support
                if height > 0 and base_area > 0:
                    height_to_base_ratio = height / (base_area ** 0.5)  # height to sqrt of base area
                    if height_to_base_ratio > 5:  # Arbitrary threshold
                        return "likely"
        
        # Default to "unknown" as proper support analysis requires more detailed geometry analysis
        return "unknown"
    
    except Exception as e:
        print(f"Error estimating support requirement: {str(e)}")
        return "unknown"

def extract_feature_data(feature_type, doc=None):
    """
    Extract data for a specific feature type
    
    Args:
        feature_type: Type of feature to extract (holes, fillets, etc.)
        doc: FreeCAD document (uses active document if None)
        
    Returns:
        List of extracted features
    """
    try:
        # Get the document
        if doc is None:
            if not FreeCAD.ActiveDocument:
                return []
            doc = FreeCAD.ActiveDocument
            
        features = []
        
        # Process each object
        for obj in doc.Objects:
            if not hasattr(obj, 'Shape') or not obj.Shape.isValid():
                continue
                
            shape = obj.Shape
            
            if feature_type == "holes":
                # Extract holes
                for face in shape.Faces:
                    if hasattr(face.Surface, 'Radius'):
                        # Circular face might be a hole
                        center = face.Surface.Center
                        radius = face.Surface.Radius
                        
                        features.append({
                            "type": "hole",
                            "radius": radius,
                            "diameter": radius * 2,
                            "position": {
                                "x": center.x,
                                "y": center.y,
                                "z": center.z
                            },
                            "object": obj.Name
                        })
                        
            elif feature_type == "fillets":
                # Extract fillets
                for edge in shape.Edges:
                    if hasattr(edge.Curve, 'Radius'):
                        # Get the midpoint of the edge
                        param = edge.FirstParameter + (edge.LastParameter - edge.FirstParameter) / 2
                        point = edge.valueAt(param)
                        
                        features.append({
                            "type": "fillet",
                            "radius": edge.Curve.Radius,
                            "length": edge.Length,
                            "position": {
                                "x": point.x,
                                "y": point.y,
                                "z": point.z
                            },
                            "object": obj.Name
                        })
                        
            elif feature_type == "faces":
                # Extract significant faces
                for i, face in enumerate(shape.Faces):
                    if face.Area > 10:  # Only include significant faces
                        # Get face center
                        center = face.CenterOfMass
                        
                        features.append({
                            "type": "face",
                            "area": face.Area,
                            "position": {
                                "x": center.x,
                                "y": center.y,
                                "z": center.z
                            },
                            "object": obj.Name,
                            "face_index": i
                        })
        
        return features
        
    except Exception as e:
        print(f"Error extracting {feature_type}: {str(e)}")
        traceback.print_exc()
        return []
