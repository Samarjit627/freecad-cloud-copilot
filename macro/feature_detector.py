"""
Feature Detection for CAD Models
"""

import FreeCAD
import Part

class FeatureDetector:
    """Detect features in CAD models"""
    
    def find_holes(self, shape):
        """Find cylindrical holes"""
        holes = []
        for face in shape.Faces:
            if isinstance(face.Surface, Part.Cylinder):
                if face.Area < 1000:  # Small cylinders are likely holes
                    holes.append({
                        'diameter': face.Surface.Radius * 2,
                        'center': face.Surface.Center
                    })
        return holes
    
    def find_vertical_faces(self, shape):
        """Find vertical faces"""
        vertical = []
        for face in shape.Faces:
            normal = face.normalAt(0, 0)
            if abs(normal.z) < 0.1:  # Nearly vertical
                vertical.append(face)
        return vertical
    
    def find_edges_for_fillet(self, shape):
        """Find edges suitable for filleting"""
        edges = []
        for edge in shape.Edges:
            if edge.Length > 1:  # Skip tiny edges
                edges.append(edge)
        return edges
