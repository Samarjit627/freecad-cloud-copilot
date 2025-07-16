#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CAD Analyzer Module for Manufacturing Co-Pilot

This module provides comprehensive CAD analysis capabilities including:
- Basic metadata extraction (dimensions, volume, surface area)
- Feature detection (holes, ribs, fillets, chamfers)
- Wall thickness analysis
- Manufacturing rule checking
"""

import FreeCAD
import Part
import math
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any

class CADAnalyzer:
    """
    Main CAD analysis class that extracts manufacturing-relevant information
    from FreeCAD models.
    """
    
    def __init__(self, doc=None, shape=None):
        """
        Initialize the CAD analyzer with either a FreeCAD document or a shape.
        
        Args:
            doc: FreeCAD document to analyze
            shape: Part.Shape to analyze (alternative to doc)
        """
        self.doc = doc
        self.shape = shape
        self.metadata = {}
        self.features = {
            "holes": [],
            "ribs": [],
            "fillets": [],
            "chamfers": [],
            "walls": []
        }
        self.analysis_complete = False
        
        # If a document is provided, get the active shape
        if self.doc and not self.shape:
            self._get_active_shape()
    
    def _get_active_shape(self):
        """Extract the active shape from the FreeCAD document."""
        if not self.doc:
            return
            
        # Try to get the active object's shape
        active_obj = self.doc.ActiveObject
        if active_obj and hasattr(active_obj, "Shape"):
            self.shape = active_obj.Shape
        # If no active object, try to find any object with a shape
        else:
            for obj in self.doc.Objects:
                if hasattr(obj, "Shape"):
                    self.shape = obj.Shape
                    break
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform complete analysis of the CAD model.
        
        Returns:
            Dict containing all analysis results
        """
        if not self.shape:
            if not self.doc:
                raise ValueError("No document or shape provided for analysis")
            self._get_active_shape()
            if not self.shape:
                raise ValueError("No valid shape found in the document")
        
        # Extract basic metadata
        self._extract_basic_metadata()
        
        # Detect features
        self._detect_holes()
        self._detect_fillets_and_chamfers()
        self._analyze_wall_thickness()
        self._detect_ribs()
        
        self.analysis_complete = True
        return self.get_results()
    
    def get_results(self) -> Dict[str, Any]:
        """
        Get the complete analysis results.
        
        Returns:
            Dict containing metadata and features
        """
        return {
            "metadata": self.metadata,
            "features": self.features
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the analysis results suitable for display.
        
        Returns:
            Dict containing summary information
        """
        if not self.analysis_complete:
            self.analyze()
            
        return {
            "part_name": self.metadata.get("name", "Unknown Part"),
            "type": "Assembly" if self.metadata.get("is_assembly", False) else "Single Part",
            "volume": f"{self.metadata.get('volume', 0):.1f} cm³",
            "dimensions": f"{self.metadata.get('dimensions', [0,0,0])[0]:.1f}mm × {self.metadata.get('dimensions', [0,0,0])[1]:.1f}mm × {self.metadata.get('dimensions', [0,0,0])[2]:.1f}mm",
            "surface_area": f"{self.metadata.get('surface_area', 0):.1f} cm²",
            "center_of_mass": f"({self.metadata.get('center_of_mass', [0,0,0])[0]:.1f}, {self.metadata.get('center_of_mass', [0,0,0])[1]:.1f}, {self.metadata.get('center_of_mass', [0,0,0])[2]:.1f}) mm",
            "feature_counts": {
                "holes": len(self.features["holes"]),
                "ribs": len(self.features["ribs"]),
                "fillets": len(self.features["fillets"]),
                "chamfers": len(self.features["chamfers"])
            }
        }
    
    def _extract_basic_metadata(self):
        """Extract basic metadata from the shape."""
        if not self.shape:
            return
            
        # Get name from document if available
        if self.doc and self.doc.ActiveObject:
            self.metadata["name"] = self.doc.ActiveObject.Label
        else:
            self.metadata["name"] = "Unknown Part"
        
        # Basic properties
        try:
            self.metadata["volume"] = self.shape.Volume / 1000  # Convert to cm³
            self.metadata["surface_area"] = self.shape.Area / 100  # Convert to cm²
        except Exception as e:
            print(f"Error calculating volume/area: {e}")
            self.metadata["volume"] = 0
            self.metadata["surface_area"] = 0
        
        # Bounding box and dimensions
        bbox = self.shape.BoundBox
        self.metadata["bounding_box"] = {
            "xmin": bbox.XMin,
            "ymin": bbox.YMin,
            "zmin": bbox.ZMin,
            "xmax": bbox.XMax,
            "ymax": bbox.YMax,
            "zmax": bbox.ZMax
        }
        self.metadata["dimensions"] = [
            bbox.XLength,
            bbox.YLength,
            bbox.ZLength
        ]
        
        # Center of mass
        try:
            com = self.shape.CenterOfMass
            self.metadata["center_of_mass"] = [com.x, com.y, com.z]
        except Exception as e:
            print(f"Error calculating center of mass: {e}")
            self.metadata["center_of_mass"] = [0, 0, 0]
        
        # Count features
        self.metadata["face_count"] = len(self.shape.Faces)
        self.metadata["edge_count"] = len(self.shape.Edges)
        self.metadata["vertex_count"] = len(self.shape.Vertexes)
        
        # Check if it's an assembly
        if self.doc:
            # Simple heuristic: if there are multiple objects with shapes
            shape_objects = [obj for obj in self.doc.Objects if hasattr(obj, "Shape")]
            self.metadata["is_assembly"] = len(shape_objects) > 1
            self.metadata["part_count"] = len(shape_objects)
    
    def _detect_holes(self):
        """
        Detect and analyze holes in the model.
        
        A hole is identified by a cylindrical face or a set of connected
        cylindrical faces forming a through hole or blind hole.
        """
        if not self.shape:
            return
            
        # Find cylindrical faces
        cylindrical_faces = []
        for i, face in enumerate(self.shape.Faces):
            if face.Surface.TypeId == 'Part::GeomCylinder':
                cylindrical_faces.append((i, face))
        
        # Process each cylindrical face
        processed_faces = set()
        for idx, face in cylindrical_faces:
            if idx in processed_faces:
                continue
                
            # Get cylinder properties
            cylinder = face.Surface
            radius = cylinder.Radius
            axis = cylinder.Axis
            location = cylinder.Location
            
            # Check if this is part of a hole
            # For simplicity, we'll consider any cylindrical face as a potential hole
            hole = {
                "id": len(self.features["holes"]),
                "radius": radius,
                "diameter": radius * 2,
                "axis": [axis.x, axis.y, axis.z],
                "location": [location.x, location.y, location.z],
                "face_indices": [idx]
            }
            
            # Try to determine if it's a through hole or blind hole
            # This is a simplified approach - a more robust solution would
            # require analyzing the topology more carefully
            hole["type"] = "unknown"  # Default
            
            # Add to holes list
            self.features["holes"].append(hole)
            processed_faces.add(idx)
    
    def _detect_fillets_and_chamfers(self):
        """
        Detect and analyze fillets and chamfers in the model.
        
        Fillets are identified by cylindrical faces with convex edges.
        Chamfers are identified by planar faces connecting two other faces at an angle.
        """
        if not self.shape:
            return
            
        # Process each face
        for i, face in enumerate(self.shape.Faces):
            # Check for fillets (cylindrical faces)
            if face.Surface.TypeId == 'Part::GeomCylinder':
                # Check if this face is already part of a hole
                is_hole = False
                for hole in self.features["holes"]:
                    if i in hole["face_indices"]:
                        is_hole = True
                        break
                
                if not is_hole:
                    # This is likely a fillet
                    cylinder = face.Surface
                    radius = cylinder.Radius
                    
                    fillet = {
                        "id": len(self.features["fillets"]),
                        "radius": radius,
                        "face_index": i
                    }
                    self.features["fillets"].append(fillet)
            
            # Check for chamfers (planar faces connecting two other faces at an angle)
            elif face.Surface.TypeId == 'Part::GeomPlane':
                # This is a simplified approach - real chamfer detection would be more complex
                # We'll look for small planar faces connecting two other faces
                if face.Area < self.metadata["surface_area"] * 0.01:  # Small face
                    edges = face.Edges
                    if len(edges) == 4:  # Quadrilateral face
                        # Check if two opposite edges are much shorter than the other two
                        lengths = [edge.Length for edge in edges]
                        lengths.sort()
                        if lengths[0] < lengths[2] * 0.5:  # Significant difference in lengths
                            chamfer = {
                                "id": len(self.features["chamfers"]),
                                "face_index": i,
                                "size": lengths[0]  # Approximate chamfer size
                            }
                            self.features["chamfers"].append(chamfer)
    
    def _analyze_wall_thickness(self):
        """
        Analyze wall thickness throughout the model.
        
        This is a simplified approach that samples points on faces and measures
        distance to the nearest face in the opposite direction.
        """
        if not self.shape:
            return
            
        # This is a complex analysis that requires sampling points on faces
        # and measuring distances to opposite faces
        # For now, we'll implement a simplified version
        
        walls = []
        min_thickness = float('inf')
        max_thickness = 0
        
        # Sample points on each face
        for i, face in enumerate(self.shape.Faces):
            # Skip very small faces
            if face.Area < self.metadata["surface_area"] * 0.001:
                continue
                
            # Get face normal at center
            try:
                u_mid = (face.ParameterRange[0] + face.ParameterRange[1]) / 2
                v_mid = (face.ParameterRange[2] + face.ParameterRange[3]) / 2
                surface_normal = face.normalAt(u_mid, v_mid)
                
                # Sample point at center of face
                center_point = face.valueAt(u_mid, v_mid)
                
                # Create a line in the opposite direction of the normal
                line_length = max(self.metadata["dimensions"]) * 2  # Make it long enough
                line_dir = surface_normal.negative()
                line = Part.LineSegment(center_point, center_point.add(line_dir.multiply(line_length)))
                
                # Find intersections with other faces
                intersections = []
                for j, other_face in enumerate(self.shape.Faces):
                    if i == j:  # Skip self
                        continue
                    
                    try:
                        # Check for intersection
                        section = other_face.section(line.toShape())
                        if not section.Vertexes:
                            continue
                            
                        # Calculate distance to intersection
                        for vertex in section.Vertexes:
                            dist = center_point.distanceToPoint(vertex.Point)
                            if dist > 0.001:  # Avoid self-intersections
                                intersections.append((dist, j))
                    except Exception:
                        continue
                
                # If we found intersections, record the minimum distance as wall thickness
                if intersections:
                    intersections.sort()  # Sort by distance
                    thickness = intersections[0][0]
                    
                    wall = {
                        "face_index": i,
                        "thickness": thickness,
                        "location": [center_point.x, center_point.y, center_point.z]
                    }
                    walls.append(wall)
                    
                    # Update min/max thickness
                    min_thickness = min(min_thickness, thickness)
                    max_thickness = max(max_thickness, thickness)
            
            except Exception as e:
                print(f"Error analyzing wall at face {i}: {e}")
                continue
        
        # Store results
        self.features["walls"] = walls
        if walls:
            self.metadata["min_wall_thickness"] = min_thickness
            self.metadata["max_wall_thickness"] = max_thickness
            
            # Calculate average thickness
            avg_thickness = sum(wall["thickness"] for wall in walls) / len(walls)
            self.metadata["avg_wall_thickness"] = avg_thickness
        else:
            self.metadata["min_wall_thickness"] = 0
            self.metadata["max_wall_thickness"] = 0
            self.metadata["avg_wall_thickness"] = 0
    
    def _detect_ribs(self):
        """
        Detect and analyze ribs in the model.
        
        Ribs are typically thin, elongated features used to add structural support.
        They are identified by thin walls with high aspect ratio.
        """
        if not self.shape or not self.features["walls"]:
            return
            
        # This is a simplified approach - real rib detection would be more complex
        # We'll look for thin walls with high aspect ratio
        
        for i, face in enumerate(self.shape.Faces):
            # Skip faces that are already part of other features
            skip = False
            for hole in self.features["holes"]:
                if i in hole["face_indices"]:
                    skip = True
                    break
            if skip:
                continue
                
            # Check if this face is part of a wall
            wall_data = None
            for wall in self.features["walls"]:
                if wall["face_index"] == i:
                    wall_data = wall
                    break
            
            if not wall_data:
                continue
                
            # Check if this is a thin wall
            if wall_data["thickness"] < self.metadata.get("avg_wall_thickness", float('inf')) * 0.7:
                # Check face aspect ratio
                try:
                    # Get face bounds
                    bounds = face.BoundBox
                    length = max(bounds.XLength, bounds.YLength, bounds.ZLength)
                    width = min(bounds.XLength, bounds.YLength, bounds.ZLength)
                    
                    # High aspect ratio indicates a rib
                    if length > width * 3 and length > wall_data["thickness"] * 5:
                        rib = {
                            "id": len(self.features["ribs"]),
                            "face_index": i,
                            "thickness": wall_data["thickness"],
                            "length": length,
                            "aspect_ratio": length / wall_data["thickness"]
                        }
                        self.features["ribs"].append(rib)
                except Exception as e:
                    print(f"Error analyzing potential rib at face {i}: {e}")
                    continue


class FeatureVisualizer:
    """
    Provides visualization capabilities for CAD features.
    """
    
    def __init__(self, doc, analyzer):
        """
        Initialize the visualizer.
        
        Args:
            doc: FreeCAD document
            analyzer: CADAnalyzer instance with completed analysis
        """
        self.doc = doc
        self.analyzer = analyzer
        self.visualization_objects = []
    
    def show_wall_thickness(self, min_thickness=None, max_thickness=None):
        """
        Visualize wall thickness using a color gradient.
        
        Args:
            min_thickness: Minimum thickness to highlight (default: global min)
            max_thickness: Maximum thickness to highlight (default: global max)
        """
        if not self.doc or not self.analyzer.analysis_complete:
            return
            
        # Use global min/max if not specified
        if min_thickness is None:
            min_thickness = self.analyzer.metadata.get("min_wall_thickness", 0)
        if max_thickness is None:
            max_thickness = self.analyzer.metadata.get("max_wall_thickness", 1)
            
        # Ensure we have a valid range
        if min_thickness >= max_thickness:
            max_thickness = min_thickness + 1
            
        # Create a color gradient
        def get_color(thickness):
            # Red (thin) to green (thick)
            if thickness <= min_thickness:
                return (1.0, 0.0, 0.0)  # Red
            elif thickness >= max_thickness:
                return (0.0, 1.0, 0.0)  # Green
            else:
                # Linear interpolation
                t = (thickness - min_thickness) / (max_thickness - min_thickness)
                return (1.0 - t, t, 0.0)
        
        # Create visualization for each wall
        for wall in self.analyzer.features["walls"]:
            thickness = wall["thickness"]
            face_idx = wall["face_index"]
            
            # Get the face
            if face_idx < len(self.analyzer.shape.Faces):
                face = self.analyzer.shape.Faces[face_idx]
                
                # Create a copy of the face for visualization
                face_copy = face.copy()
                
                # Create a new object
                obj = self.doc.addObject("Part::Feature", f"Wall_{face_idx}")
                obj.Shape = face_copy
                
                # Set color based on thickness
                color = get_color(thickness)
                obj.ViewObject.ShapeColor = color
                
                # Make it slightly transparent
                obj.ViewObject.Transparency = 50
                
                # Add to visualization objects
                self.visualization_objects.append(obj)
        
        # Refresh view
        self.doc.recompute()
    
    def show_holes(self):
        """Highlight holes in the model."""
        if not self.doc or not self.analyzer.analysis_complete:
            return
            
        # Create visualization for each hole
        for hole in self.analyzer.features["holes"]:
            # Create a cylinder to represent the hole
            radius = hole["radius"]
            location = hole["location"]
            axis = hole["axis"]
            
            # Create a cylinder
            cylinder = Part.makeCylinder(radius, 10, 
                                        FreeCAD.Vector(location[0], location[1], location[2]),
                                        FreeCAD.Vector(axis[0], axis[1], axis[2]))
            
            # Create a new object
            obj = self.doc.addObject("Part::Feature", f"Hole_{hole['id']}")
            obj.Shape = cylinder
            
            # Set color
            obj.ViewObject.ShapeColor = (0.0, 0.0, 1.0)  # Blue
            
            # Make it transparent
            obj.ViewObject.Transparency = 80
            
            # Add to visualization objects
            self.visualization_objects.append(obj)
        
        # Refresh view
        self.doc.recompute()
    
    def clear_visualizations(self):
        """Remove all visualization objects."""
        if not self.doc:
            return
            
        # Remove all visualization objects
        for obj in self.visualization_objects:
            self.doc.removeObject(obj.Name)
        
        self.visualization_objects = []
        
        # Refresh view
        self.doc.recompute()


def analyze_active_document():
    """
    Analyze the active FreeCAD document and return the results.
    
    Returns:
        Dict containing analysis results
    """
    doc = FreeCAD.ActiveDocument
    if not doc:
        raise ValueError("No active document")
        
    analyzer = CADAnalyzer(doc)
    results = analyzer.analyze()
    
    return results


def get_analysis_summary():
    """
    Get a summary of the analysis results for the active document.
    
    Returns:
        Dict containing summary information
    """
    doc = FreeCAD.ActiveDocument
    if not doc:
        raise ValueError("No active document")
        
    analyzer = CADAnalyzer(doc)
    analyzer.analyze()
    
    return analyzer.get_summary()


if __name__ == "__main__":
    # Test with active document if run as script
    if FreeCAD.ActiveDocument:
        results = analyze_active_document()
        print("Analysis complete")
        print(f"Part name: {results['metadata'].get('name', 'Unknown')}")
        print(f"Volume: {results['metadata'].get('volume', 0):.2f} cm³")
        print(f"Surface area: {results['metadata'].get('surface_area', 0):.2f} cm²")
        print(f"Holes detected: {len(results['features']['holes'])}")
        print(f"Fillets detected: {len(results['features']['fillets'])}")
        print(f"Chamfers detected: {len(results['features']['chamfers'])}")
        print(f"Ribs detected: {len(results['features']['ribs'])}")
        if 'min_wall_thickness' in results['metadata']:
            print(f"Min wall thickness: {results['metadata']['min_wall_thickness']:.2f} mm")
    else:
        print("No active document")
