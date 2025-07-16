"""
Local CAD Analyzer for FreeCAD Manufacturing Co-Pilot
Provides basic CAD analysis functionality when cloud service is unavailable
"""

import time
import math
from typing import Dict, Any, List, Tuple, Optional

class LocalCADAnalyzer:
    """Provides local CAD analysis when cloud service is unavailable"""
    
    def __init__(self):
        """Initialize the local analyzer"""
        self.last_error = None
    
    def analyze_document(self, doc) -> Dict[str, Any]:
        """Analyze a FreeCAD document locally
        
        Args:
            doc: FreeCAD document
            
        Returns:
            Analysis results
        """
        try:
            print("Cloud service unavailable. Performing local CAD analysis...")
            
            # Extract basic metadata
            metadata = self._extract_metadata(doc)
            
            # Extract geometry data
            geometry_data = self._extract_geometry(doc)
            
            # Perform basic feature detection
            features = self._detect_features(doc, geometry_data)
            
            # Return analysis results
            return {
                "metadata": metadata,
                "geometry": geometry_data,
                "features": features,
                "analysis_type": "local",  # Indicate this was analyzed locally
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
            
        except Exception as e:
            self.last_error = str(e)
            print(f"Error in local CAD analysis: {str(e)}")
            
            # Return basic structure with error
            return {
                "error": str(e),
                "analysis_type": "local_error",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
    
    def _extract_metadata(self, doc) -> Dict[str, Any]:
        """Extract metadata from document"""
        metadata = {
            "name": doc.Name,
            "label": doc.Label if hasattr(doc, "Label") else doc.Name,
            "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "modified": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "units": "mm",  # Assume mm as default
            "object_count": len(doc.Objects)
        }
        
        # Count objects by type
        type_counts = {}
        for obj in doc.Objects:
            obj_type = obj.TypeId.split(":")[-1] if ":" in obj.TypeId else obj.TypeId
            if obj_type in type_counts:
                type_counts[obj_type] += 1
            else:
                type_counts[obj_type] = 1
        
        metadata["object_types"] = type_counts
        
        return metadata
    
    def _extract_geometry(self, doc) -> Dict[str, Any]:
        """Extract basic geometry data from document"""
        geometry = {
            "faces": [],
            "edges": [],
            "vertices": [],
            "bounding_box": {"min": [0, 0, 0], "max": [0, 0, 0]},
            "volume": 0,
            "surface_area": 0
        }
        
        # Process each object
        for obj in doc.Objects:
            # Skip non-shape objects
            if not hasattr(obj, "Shape"):
                continue
                
            shape = obj.Shape
            
            # Count basic geometry elements
            geometry["faces"].append(len(shape.Faces))
            geometry["edges"].append(len(shape.Edges))
            geometry["vertices"].append(len(shape.Vertexes))
            
            # Get bounding box if available
            if hasattr(shape, "BoundBox"):
                bb = shape.BoundBox
                geometry["bounding_box"] = {
                    "min": [bb.XMin, bb.YMin, bb.ZMin],
                    "max": [bb.XMax, bb.YMax, bb.ZMax]
                }
            
            # Get volume and surface area if available
            if hasattr(shape, "Volume"):
                geometry["volume"] += shape.Volume
            
            if hasattr(shape, "Area"):
                geometry["surface_area"] += shape.Area
        
        return geometry
    
    def _detect_features(self, doc, geometry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform basic feature detection"""
        features = {
            "holes": [],
            "fillets": [],
            "chamfers": [],
            "ribs": [],
            "detected_features": []
        }
        
        try:
            # Process each object
            for obj in doc.Objects:
                # Skip non-shape objects
                if not hasattr(obj, "Shape"):
                    continue
                
                shape = obj.Shape
                
                # Basic feature detection based on object name/label
                obj_name = obj.Label.lower() if hasattr(obj, "Label") else ""
                obj_type = obj.TypeId.lower() if hasattr(obj, "TypeId") else ""
                
                # Look for common feature names in object labels
                if "hole" in obj_name or "drill" in obj_name or "bore" in obj_name:
                    features["detected_features"].append({
                        "type": "hole",
                        "name": obj.Label,
                        "confidence": 0.8
                    })
                    
                if "fillet" in obj_name or "round" in obj_name:
                    features["detected_features"].append({
                        "type": "fillet",
                        "name": obj.Label,
                        "confidence": 0.8
                    })
                    
                if "chamfer" in obj_name or "bevel" in obj_name:
                    features["detected_features"].append({
                        "type": "chamfer",
                        "name": obj.Label,
                        "confidence": 0.8
                    })
                    
                if "rib" in obj_name or "web" in obj_name:
                    features["detected_features"].append({
                        "type": "rib",
                        "name": obj.Label,
                        "confidence": 0.8
                    })
                
                # Look for cylindrical faces (potential holes)
                for face_idx, face in enumerate(shape.Faces):
                    if hasattr(face, "Surface") and hasattr(face.Surface, "Radius"):
                        # This is a cylindrical face, likely a hole
                        features["holes"].append({
                            "object": obj.Label,
                            "face_index": face_idx,
                            "radius": face.Surface.Radius,
                            "confidence": 0.7
                        })
                
                # Detect simple holes (circular edges)
                for edge in shape.Edges:
                    if hasattr(edge, "Curve") and hasattr(edge.Curve, "Radius"):
                        # This is likely a circular edge
                        features["holes"].append({
                            "radius": edge.Curve.Radius,
                            "center": [edge.Curve.Center.x, edge.Curve.Center.y, edge.Curve.Center.z]
                        })
                
                # Detect fillets (edges with constant curvature)
                for edge in shape.Edges:
                    if hasattr(edge, "Curve") and hasattr(edge.Curve, "Radius"):
                        if edge.Curve.Radius < 10:  # Arbitrary threshold for fillets
                            features["fillets"].append({
                                "radius": edge.Curve.Radius,
                                "length": edge.Length
                            })
                
                # Add to detected features
                features["detected_features"].append({
                    "name": obj.Name,
                    "type": obj.TypeId,
                    "face_count": len(shape.Faces),
                    "edge_count": len(shape.Edges)
                })
                
        except Exception as e:
            print(f"Warning: Error in feature detection: {str(e)}")
            
        return features

# Singleton instance
_local_analyzer_instance = None

def get_analyzer() -> LocalCADAnalyzer:
    """Get the singleton local CAD analyzer instance"""
    global _local_analyzer_instance
    if _local_analyzer_instance is None:
        _local_analyzer_instance = LocalCADAnalyzer()
    return _local_analyzer_instance
