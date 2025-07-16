"""
FreeCAD Engineering Analyzer Module
Provides comprehensive analysis of parts including dimensions, wall thickness, and manufacturability
"""

import FreeCAD
import Part
from FreeCAD import Base
from typing import Dict, Any, List, Tuple, Optional

def run_full_analysis(document, selected_objects=None):
    """
    Main function to run all analyses on the selected object(s).
    
    Args:
        document: FreeCAD document
        selected_objects: List of objects to analyze (if None, uses current selection)
        
    Returns:
        Dict containing analysis results
    """
    if selected_objects is None:
        selection = FreeCAD.Gui.Selection.getSelection()
    else:
        selection = selected_objects
        
    if not selection:
        print("Error: Please select at least one object.")
        return {"error": "No objects selected"}

    print("Starting full engineering analysis...")

    # --- Create a single compound shape for consistent analysis ---
    all_shapes = [s.Shape for s in selection if hasattr(s, 'Shape')]
    if not all_shapes:
        print("No valid shapes found in selection.")
        return {"error": "No valid shapes found"}
        
    main_shape = Part.makeCompound(all_shapes)

    # --- 1. Overall Dimensions ---
    try:
        overall_bbox = main_shape.BoundBox
        
        # Check for unreasonable values and fix them
        max_reasonable_size = 10000.0  # 10 meters is a reasonable max size for most parts
        
        x_length = min(overall_bbox.XLength, max_reasonable_size) if overall_bbox.XLength > 0 else 0
        y_length = min(overall_bbox.YLength, max_reasonable_size) if overall_bbox.YLength > 0 else 0
        z_length = min(overall_bbox.ZLength, max_reasonable_size) if overall_bbox.ZLength > 0 else 0
        
        # Use shape's actual volume and surface area, but cap at reasonable values
        volume = min(main_shape.Volume, max_reasonable_size**3) if main_shape.Volume > 0 else 0
        surface_area = min(main_shape.Area, max_reasonable_size**2) if main_shape.Area > 0 else 0
        
        dimensions = {
            "length_x": x_length,
            "width_y": y_length,
            "height_z": z_length,
            "volume": volume,
            "surface_area": surface_area
        }
        
        print(f"Dimensions calculated: X={x_length:.2f}, Y={y_length:.2f}, Z={z_length:.2f} mm")
    except Exception as e:
        print(f"Error calculating dimensions: {str(e)}")
        # Provide fallback dimensions
        dimensions = {
            "length_x": 0,
            "width_y": 0,
            "height_z": 0,
            "volume": 0,
            "surface_area": 0
        }

    # --- 2. Wall Thickness ---
    min_t, max_t = analyze_wall_thickness(main_shape)
    thickness = {
        "min": min_t,
        "max": max_t
    }

    # --- 3. Draft, Undercut, Fillet, and Chamfer Analysis ---
    pull_direction = Base.Vector(0, 0, 1)  # Assumes pull from Z-axis
    feature_results = analyze_features(main_shape, pull_direction)
    
    # Store both counts and actual face lists for fillets and chamfers
    features = {
        "positive_draft_count": len(feature_results['positive_draft']),
        "zero_draft_vertical_count": len(feature_results['zero_draft_vertical']),
        "undercuts_count": len(feature_results['undercuts']),
        "fillets_count": len(feature_results['fillets']),
        "chamfers_count": len(feature_results['chamfers']),
        "pull_direction": [pull_direction.x, pull_direction.y, pull_direction.z],
        # Include the actual fillets and chamfers lists
        "fillets": feature_results['fillets'],
        "chamfers": feature_results['chamfers']
    }

    # --- 4. Complexity and Manufacturability Scores ---
    complexity_score = calculate_complexity_score(main_shape, feature_results)
    manufacturability_score = calculate_manufacturability_score(feature_results, min_t, max_t, complexity_score)
    
    scores = {
        "complexity": complexity_score,
        "manufacturability": manufacturability_score
    }

    # Compile all results
    analysis_result = {
        "dimensions": dimensions,
        "thickness": thickness,
        "features": features,
        "scores": scores
    }
    
    print("Engineering analysis complete.")
    return analysis_result


def analyze_features(shape, pull_direction):
    """
    Analyzes every face for draft, undercuts, fillets, and chamfers.
    
    Args:
        shape: FreeCAD shape to analyze
        pull_direction: Vector indicating pull direction for draft analysis
        
    Returns:
        Dict containing lists of faces categorized by feature type
    """
    results = { 
        "positive_draft": [], 
        "zero_draft_vertical": [], 
        "undercuts": [], 
        "fillets": [], 
        "chamfers": [] 
    }
    
    for face in shape.Faces:
        try:
            # --- Draft/Undercut Analysis ---
            try:
                # Get normal at center of mass
                normal = None
                try:
                    # Try using Surface.parameter if available
                    if hasattr(face, 'Surface') and hasattr(face.Surface, 'parameter'):
                        u, v = face.Surface.parameter(face.CenterOfMass)
                        normal = face.normalAt(u, v)
                    else:
                        # Fallback: use face normal directly
                        normal = face.normalAt(0, 0)
                except Exception:
                    # Last resort: use face orientation
                    normal = face.Surface.Axis
                    
                # Calculate draft angle
                angle_to_pull = normal.getAngle(pull_direction) * 180 / 3.14159
                draft_angle = 90.0 - angle_to_pull
                
                # Categorize face based on draft angle
                if abs(draft_angle) < 0.1:  # Near zero draft (vertical face)
                    results["zero_draft_vertical"].append(face)
                elif draft_angle < 0:  # Negative draft (undercut)
                    results["undercuts"].append(face)
                else:  # Positive draft
                    results["positive_draft"].append(face)
            except Exception as e:
                print(f"Warning: Error in draft analysis: {str(e)}")

            # --- Fillet/Chamfer Analysis ---
            try:
                if is_likely_blend_face(face, shape):
                    # Improved distinction between fillets and chamfers
                    if isinstance(face.Surface, (Part.Plane, Part.Cone)):
                        results["chamfers"].append(face)
                    else:
                        results["fillets"].append(face)
            except Exception as e:
                print(f"Warning: Error in fillet/chamfer analysis: {str(e)}")
                
        except Exception as e:
            print(f"Warning: Error analyzing face: {str(e)}")
            continue
            
    return results


def is_likely_blend_face(face, shape, tolerance=1e-4):  # Increased tolerance for better detection
    """
    CORRECTED, ROBUST helper to check if a face is a blend (fillet/chamfer)
    by manually checking for G1 tangency with its neighbors.
    
    Args:
        face: Face to check
        shape: Parent shape
        tolerance: Tolerance for tangency check (increased for better detection)
        
    Returns:
        Boolean indicating if the face is likely a blend face
    """
    # For rubber parts and other models with subtle fillets, we need to be more lenient
    # A blend face typically has a low number of edges. This is a quick filter.
    if len(face.Edges) > 8:  # Increased from 6 to 8 to catch more potential fillets
        return False
        
    # Check if the face is cylindrical, conical or toroidal - common for fillets
    is_common_fillet_surface = isinstance(face.Surface, (Part.Cylinder, Part.Cone, Part.Toroid))
    
    # For cylindrical, conical or toroidal surfaces, we can be more confident they're fillets/chamfers
    if is_common_fillet_surface and face.Area < shape.Area * 0.2:  # Small relative to total area
        # Additional check for small faces that are likely fillets
        return True

    tangent_edge_count = 0
    for edge in face.Edges:
        try:
            # Find faces that share this edge. There should be exactly two.
            adjacent_faces = shape.ancestorsOfType(Part.Face, edge)
            if len(adjacent_faces) != 2:
                continue

            neighbor = adjacent_faces[0] if adjacent_faces[1] == face else adjacent_faces[1]

            # The Core Tangency Check
            p_on_edge = edge.valueAt(edge.FirstParameter + edge.Length / 2)
            uv_face = face.Surface.parameter(p_on_edge)
            uv_neighbor = neighbor.Surface.parameter(p_on_edge)
            normal_face = face.normalAt(uv_face[0], uv_face[1])
            normal_neighbor = neighbor.normalAt(uv_neighbor[0], uv_neighbor[1])

            # Check if the normals are parallel (dot product is close to 1 or -1)
            if abs(normal_face.dot(normal_neighbor)) > (1.0 - tolerance):
                tangent_edge_count += 1

        except Exception:
            continue # Skip edge if any calculation fails

    # If at least one edge is tangent, we classify it as a blend.
    return tangent_edge_count >= 1


def analyze_wall_thickness(shape, samples=200):
    """
    Approximates wall thickness using ray-shooting.
    
    Args:
        shape: FreeCAD shape to analyze
        samples: Number of sample points to use
        
    Returns:
        Tuple of (min_thickness, max_thickness)
    """
    import random
    import math
    
    min_thick, max_thick = float('inf'), 0.0
    successful_measurements = 0
    
    try:
        # Use more sample points for complex shapes
        if len(shape.Faces) > 20:
            samples = max(samples, len(shape.Faces) * 5)
            
        print(f"Using {samples} sample points for thickness analysis")
        
        # Collect sample points from face centers
        points = []
        for face in shape.Faces:
            try:
                points.append(face.CenterOfMass)
            except Exception:
                # If center of mass fails, try a vertex
                if len(face.Vertexes) > 0:
                    points.append(face.Vertexes[0].Point)
        
        # If we don't have enough points, add random points from tessellation
        if len(points) < samples:
            try:
                mesh = shape.tessellate(0.1)[0]
                points.extend(mesh)
            except Exception as e:
                print(f"Warning: Tessellation failed: {str(e)}")
        
        # Limit to requested sample count
        if len(points) > samples:
            random.shuffle(points)
            points = points[:samples]
            
        if not points:
            print("Warning: No sample points available for thickness analysis")
            return None, None
            
        # For each point, shoot rays in multiple directions
        directions = [
            Base.Vector(1, 0, 0), Base.Vector(-1, 0, 0),
            Base.Vector(0, 1, 0), Base.Vector(0, -1, 0),
            Base.Vector(0, 0, 1), Base.Vector(0, 0, -1)
        ]
        
        bbox_diag = shape.BoundBox.DiagonalLength
        
        for point in points:
            for direction in directions:
                try:
                    # Create a ray through the shape
                    ray_start = point.add(direction.multiply(bbox_diag))
                    ray_end = point.add(direction.multiply(-bbox_diag))
                    ray = Part.makeLine(ray_start, ray_end)
                    
                    # Find intersections with the shape
                    intersections = []
                    try:
                        common = ray.common(shape)
                        if common.Edges:
                            for edge in common.Edges:
                                for vertex in edge.Vertexes:
                                    intersections.append(vertex.Point)
                    except Exception:
                        # Fallback to distToShape
                        try:
                            dist_info = shape.distToShape(ray)
                            if dist_info[0] < 1e-6:  # There's an intersection
                                for pair in dist_info[1]:
                                    intersections.append(pair[0])
                        except Exception as e:
                            continue
                    
                    # If we have at least 2 intersections, calculate thickness
                    if len(intersections) >= 2:
                        # Sort intersections by distance from ray_start
                        intersections.sort(key=lambda p: p.distanceToPoint(ray_start))
                        
                        # Calculate thickness between consecutive intersections
                        for i in range(len(intersections)-1):
                            thickness = intersections[i].distanceToPoint(intersections[i+1])
                            if thickness > 1e-3:  # Ignore tiny thicknesses
                                min_thick = min(min_thick, thickness)
                                max_thick = max(max_thick, thickness)
                                successful_measurements += 1
                except Exception as e:
                    continue
        
        print(f"Completed {successful_measurements} successful thickness measurements")
        
        if min_thick == float('inf') or successful_measurements == 0:
            print("Warning: Could not determine wall thickness")
            return None, None
            
        # Apply reasonable limits to thickness values
        max_reasonable_thickness = shape.BoundBox.DiagonalLength / 2
        if max_thick > max_reasonable_thickness:
            max_thick = max_reasonable_thickness
        
        return min_thick, max_thick
        
    except Exception as e:
        print(f"Warning: Error in wall thickness analysis: {str(e)}")
        return None, None


def calculate_complexity_score(shape, feature_results):
    """
    Calculates a heuristic complexity score.
    
    Args:
        shape: FreeCAD shape to analyze
        feature_results: Dict of feature analysis results
        
    Returns:
        Float complexity score
    """
    face_count = len(shape.Faces)
    curved_face_count = sum(1 for f in shape.Faces if not isinstance(f.Surface, Part.Plane))
    fillet_count = len(feature_results['fillets'])
    chamfer_count = len(feature_results['chamfers'])
    
    score = (face_count * 0.1) + (curved_face_count * 0.5) + (fillet_count * 1.0) + (chamfer_count * 0.8)
    return score


def calculate_manufacturability_score(feature_results, min_thick, max_thick, complexity):
    """
    Calculates a heuristic manufacturability score for injection molding.
    
    Args:
        feature_results: Dict of feature analysis results
        min_thick: Minimum wall thickness
        max_thick: Maximum wall thickness
        complexity: Complexity score
        
    Returns:
        Float manufacturability score (0-100)
    """
    score = 100.0
    
    # Deduct points for undercuts
    score -= len(feature_results['undercuts']) * 20.0
    
    # Deduct points for vertical faces (zero draft)
    score -= len(feature_results['zero_draft_vertical']) * 5.0
    
    # Deduct points for uneven wall thickness
    if min_thick is not None and min_thick > 1e-4:
        ratio = max_thick / min_thick if min_thick > 0 else 1.0
        if ratio > 2.0:
            score -= (ratio - 2.0) * 5.0
            
    # Deduct points for complexity
    score -= complexity * 0.1

    return max(0, min(100, score))
