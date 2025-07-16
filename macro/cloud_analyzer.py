"""
Cloud-based CAD Analyzer Client for the FreeCAD Manufacturing Co-Pilot
Handles sending CAD data to Google Cloud Run for analysis
"""

import os
import json
import time
import tempfile
import base64
from typing import Dict, Any, Optional, List, Tuple

import FreeCAD
import Part

# Import local modules
try:
    import config
    import cloud_client
except ImportError:
    import config
    import cloud_client

class CloudCADAnalyzer:
    """Client for cloud-based CAD analysis using Google Cloud Run"""
    
    def __init__(self):
        """Initialize the cloud CAD analyzer client"""
        self.cloud_client = cloud_client.get_client()
        self.last_error = None
        self.last_analysis = None
        self.is_analyzing = False
    
    def analyze_document(self, document) -> Dict[str, Any]:
        """
        Analyze a FreeCAD document using cloud-based analysis
        
        Args:
            document: FreeCAD document to analyze
            
        Returns:
            Dict containing analysis results
        """
        try:
            self.is_analyzing = True
            
            # Extract basic metadata locally (lightweight operation)
            basic_metadata = self._extract_basic_metadata(document)
            
            # Prepare geometry data for cloud processing
            geometry_data = self._prepare_geometry_data(document)
            
            # Send to cloud for analysis
            print("Sending CAD data to cloud for analysis...")
            analysis_result = self._send_to_cloud_for_analysis(basic_metadata, geometry_data)
            
            # Store the result
            self.last_analysis = analysis_result
            self.is_analyzing = False
            
            return analysis_result
            
        except Exception as e:
            self.last_error = str(e)
            self.is_analyzing = False
            print(f"Error in cloud CAD analysis: {str(e)}")
            return {
                "error": str(e),
                "metadata": basic_metadata if 'basic_metadata' in locals() else {},
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
    
    def _extract_basic_metadata(self, document) -> Dict[str, Any]:
        """
        Extract basic metadata from the document (lightweight local operation)
        
        Args:
            document: FreeCAD document
            
        Returns:
            Dict containing basic metadata
        """
        metadata = {
            "name": document.Name,
            "label": document.Label,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "object_count": len(document.Objects)
        }
        
        # Get bounding box for basic dimensions (lightweight operation)
        try:
            shapes = []
            for obj in document.Objects:
                if hasattr(obj, "Shape"):
                    shapes.append(obj.Shape)
            
            if shapes:
                # Create a compound shape
                compound = Part.makeCompound(shapes)
                bbox = compound.BoundBox
                
                # Add bounding box dimensions
                metadata["dimensions"] = [
                    bbox.XLength,
                    bbox.YLength,
                    bbox.ZLength
                ]
                
                # Add bounding box volume (approximate)
                metadata["bounding_volume"] = bbox.XLength * bbox.YLength * bbox.ZLength
        except Exception as e:
            print(f"Warning: Could not calculate bounding box: {str(e)}")
        
        return metadata
    
    def _prepare_geometry_data(self, document) -> Dict[str, Any]:
        """
        Prepare geometry data for cloud processing
        This extracts essential geometry information without sending the full CAD model
        
        Args:
            document: FreeCAD document
            
        Returns:
            Dict containing geometry data for cloud processing
        """
        geometry_data = {
            "faces": [],
            "edges": [],
            "vertices": []
        }
        
        try:
            # Process each object with a shape
            for obj in document.Objects:
                if not hasattr(obj, "Shape"):
                    continue
                    
                shape = obj.Shape
                obj_data = {
                    "name": obj.Name,
                    "label": obj.Label if hasattr(obj, "Label") else obj.Name,
                    "type": obj.TypeId,
                    "faces": [],
                    "edges": [],
                    "vertices": []
                }
                
                # Extract face data
                for i, face in enumerate(shape.Faces):
                    face_data = {
                        "index": i,
                        "area": face.Area,
                        "type": self._detect_face_type(face),
                        "center": [p for p in face.CenterOfMass],
                        "normal": [n for n in face.normalAt(0, 0)]
                    }
                    obj_data["faces"].append(face_data)
                
                # Extract edge data (simplified)
                for i, edge in enumerate(shape.Edges):
                    edge_data = {
                        "index": i,
                        "length": edge.Length,
                        "type": edge.Curve.TypeId,
                        "points": [
                            [p for p in edge.Vertexes[0].Point],
                            [p for p in edge.Vertexes[-1].Point]
                        ]
                    }
                    obj_data["edges"].append(edge_data)
                
                # Add to overall geometry data
                geometry_data["faces"].extend(obj_data["faces"])
                geometry_data["edges"].extend(obj_data["edges"])
            
            return geometry_data
            
        except Exception as e:
            print(f"Error preparing geometry data: {str(e)}")
            return geometry_data
    
    def _detect_face_type(self, face) -> str:
        """
        Detect the type of a face
        
        Args:
            face: FreeCAD face
            
        Returns:
            String describing the face type
        """
        try:
            surface = face.Surface
            surface_type = surface.TypeId
            
            # Map common surface types
            if "Plane" in surface_type:
                return "planar"
            elif "Cylinder" in surface_type:
                return "cylindrical"
            elif "Cone" in surface_type:
                return "conical"
            elif "Sphere" in surface_type:
                return "spherical"
            elif "Torus" in surface_type:
                return "toroidal"
            elif "BSpline" in surface_type:
                return "bspline"
            else:
                return surface_type
        except:
            return "unknown"
    
    def _send_to_cloud_for_analysis(self, metadata: Dict[str, Any], 
                                   geometry_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send data to cloud for analysis
        
        Args:
            metadata: Basic metadata extracted locally
            geometry_data: Geometry data for cloud processing
            
        Returns:
            Dict containing analysis results from the cloud
        """
        try:
            # Prepare payload
            payload = {
                "metadata": metadata,
                "geometry": geometry_data
            }
            
            # Use the cloud client to send the data
            response = self.cloud_client._make_request("/api/analysis", payload=payload)
            
            # If the cloud returns enhanced metadata, merge it with our basic metadata
            if "metadata" in response:
                metadata.update(response["metadata"])
                response["metadata"] = metadata
            
            return response
            
        except Exception as e:
            print(f"Error sending data to cloud: {str(e)}")
            # Return basic metadata if cloud analysis fails
            return {
                "error": str(e),
                "metadata": metadata,
                "features": {
                    "holes": [],
                    "fillets": [],
                    "chamfers": [],
                    "ribs": []
                },
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }

# Singleton instance
_analyzer_instance = None

def get_analyzer() -> CloudCADAnalyzer:
    """Get the singleton cloud CAD analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = CloudCADAnalyzer()
    return _analyzer_instance
