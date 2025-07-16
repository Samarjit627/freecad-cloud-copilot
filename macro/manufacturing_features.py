"""
Manufacturing-specific features for CAD models
"""

import math
import sys
import re
import FreeCAD
import FreeCADGui
import Part
import PartDesign
import Sketcher
from FreeCAD import Base
from PySide2 import QtWidgets

class ManufacturingFeatures:
    """Add manufacturing-specific features to parts"""
    
    def __init__(self):
        """Initialize manufacturing features"""
        self.hole_diameter = 5.0  # Default hole diameter
        self.hole_depth = 10.0  # Default hole depth
        self.fillet_radius = 2.0  # Default fillet
        self.extrude_distance = 10.0  # Default extrusion distance
        self.chamfer_distance = 1.0  # Default chamfer distance
        
    def add_draft_angles(self, angle=3.0, faces=None):
        """Add draft angles to selected faces or all vertical faces using native PartDesign::Draft"""
        try:
            doc = FreeCAD.ActiveDocument
            if not doc:
                return {'success': False, 'message': 'No active document'}
            
            # Get part from selection
            selection = FreeCADGui.Selection.getSelection()
            if not selection:
                return {'success': False, 'message': 'No object selected'}
            part = selection[0]
                
            print(f"Debug: Adding draft angles of {angle}\u00b0 to {part.Name}")
            
            # Make sure we have a valid angle
            if angle is None:
                angle = 3.0
            elif angle < 0:
                angle = 0.0
            
            # Create a body to hold the draft feature
            body = doc.addObject("PartDesign::Body", f"DraftBody_{part.Name}")
            
            # Create a base feature by copying the original part's shape
            base = body.newObject("PartDesign::AdditivePrism", "Base")
            base.Shape = part.Shape.copy()
            doc.recompute()
            
            # Print available faces for debugging
            print("Available faces for part:")
            for i, face in enumerate(base.Shape.Faces):
                face_type = face.Surface.__class__.__name__
                normal = face.normalAt(0, 0)
                print(f"Face{i+1}: {face_type}, Normal: ({normal.x:.2f}, {normal.y:.2f}, {normal.z:.2f})")
            
            # Find vertical faces for drafting
            support_faces = []
            for i, face in enumerate(base.Shape.Faces):
                # Check if face is vertical (normal has no Z component)
                if abs(face.normalAt(0, 0).z) < 0.01:
                    support_faces.append(f"Face{i+1}")
                    print(f"Selected Face{i+1} as support face for draft")
            
            if not support_faces:
                return {'success': False, 'message': 'No vertical faces found for drafting'}
            
            # Find the bottom face for neutral plane
            neutral_face = None
            for i, face in enumerate(base.Shape.Faces):
                normal = face.normalAt(0, 0)
                if abs(normal.z + 1.0) < 0.01:  # Normal pointing down (-Z)
                    neutral_face = f"Face{i+1}"
                    print(f"Selected {neutral_face} as neutral plane, Normal: ({normal.x:.2f}, {normal.y:.2f}, {normal.z:.2f})")
                    break
            
            if not neutral_face:
                # Try to find any horizontal face if bottom face not found
                for i, face in enumerate(base.Shape.Faces):
                    normal = face.normalAt(0, 0)
                    if abs(abs(normal.z) - 1.0) < 0.01:  # Any horizontal face
                        neutral_face = f"Face{i+1}"
                        print(f"Selected {neutral_face} as neutral plane (not bottom), Normal: ({normal.x:.2f}, {normal.y:.2f}, {normal.z:.2f})")
                        break
            
            if not neutral_face:
                return {'success': False, 'message': 'No suitable neutral plane found for drafting'}
            
            # Apply draft angle to the selected faces
            draft = body.newObject("PartDesign::Draft", "Draft")
            draft.Base = base
            draft.Support = [(base, face) for face in support_faces]  # The faces to apply draft
            draft.Angle = angle                                      # Positive = outward taper
            draft.Reversed = False                                   # True = inward (negative) draft
            draft.Type = 0                                           # Neutral plane mode
            draft.NeutralPlane = (base, [neutral_face])              # Usually bottom face
            
            # Update document
            doc.recompute()
            
            # Hide the original part
            part.Visibility = False
            
            print(f"Debug: Created draft angle of {angle}\u00b0 using native PartDesign::Draft")
            return {'success': True, 'message': f'Added draft angle of {angle}\u00b0 to {part.Name}'}
            
        except Exception as e:
            print(f"Debug: Error using PartDesign::Draft: {str(e)}")
            return {'success': False, 'message': f'Error adding draft angle: {str(e)}'}
            
            # Make the original part invisible
            part.Visibility = False
            
            print(f"Debug: Created draft with angle {angle}° and shape type: {part.Name}")
            
            doc.recompute()
            
            # Count the number of faces in the final shape
            face_count = len(drafted_part.Shape.Faces) if hasattr(drafted_part.Shape, 'Faces') else 4
            
            return {
                'success': True,
                'message': f'Added draft angles of {angle}° to {face_count} faces',
                'angle': angle,
                'faces': face_count,
                'object': drafted_part
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error adding draft: {str(e)}'}
    
    def add_ribs(self, thickness=2.0, height=10.0, pattern='cross'):
        """Add reinforcement ribs"""
        doc = FreeCAD.ActiveDocument
        if not doc:
            return {'success': False, 'message': 'No active document'}
            
        try:
            # Use provided part or get from selection
            selection = FreeCADGui.Selection.getSelection()
            if not selection:
                return {'success': False, 'message': 'No object selected'}
            part = selection[0]
            
            # Get bounding box
            bbox = part.Shape.BoundBox
            
            # Determine rib pattern
            if pattern == 'auto':
                # Auto-detect best pattern based on shape
                if bbox.XLength > bbox.YLength * 2:
                    pattern = 'longitudinal'
                elif bbox.YLength > bbox.XLength * 2:
                    pattern = 'transverse'
                else:
                    pattern = 'cross'
                    
            rib_count = 0
            
            # Get part dimensions
            center_x = (bbox.XMin + bbox.XMax) / 2
            center_y = (bbox.YMin + bbox.YMax) / 2
            bottom_z = bbox.ZMin
            top_z = bottom_z + height
            
            rib_objects = []
            
            if pattern == 'cross':
                # Create cross pattern ribs
                rib_count = 2
                
                # Instead of using Part::Fuse which can cause invalid shapes,
                # we'll create a new Part::Feature with the combined shape
                
                # Create rib shapes directly
                x_rib_shape = Part.makeBox(bbox.XLength, thickness, height,
                                         FreeCAD.Vector(bbox.XMin, center_y - thickness/2, bottom_z))
                
                y_rib_shape = Part.makeBox(thickness, bbox.YLength, height,
                                         FreeCAD.Vector(center_x - thickness/2, bbox.YMin, bottom_z))
                
                # Get the part's shape
                part_shape = part.Shape.copy()
                
                # Combine shapes
                # Create simple box ribs without trying to fuse them
                # This avoids the "Resulting shape is invalid" error
                x_rib = doc.addObject("Part::Box", "RibX")
                x_rib.Length = bbox.XLength
                x_rib.Width = thickness
                x_rib.Height = height
                x_rib.Placement.Base = FreeCAD.Vector(bbox.XMin, center_y - thickness/2, bottom_z)
                
                y_rib = doc.addObject("Part::Box", "RibY")
                y_rib.Length = thickness
                y_rib.Width = bbox.YLength
                y_rib.Height = height
                y_rib.Placement.Base = FreeCAD.Vector(center_x - thickness/2, bbox.YMin, bottom_z)
                
                doc.recompute()
                
                # Create a group to keep them together
                try:
                    import Draft
                    group = doc.addObject("App::DocumentObjectGroup", "RibGroup")
                    group.addObject(x_rib)
                    group.addObject(y_rib)
                    print("Debug: Created rib group")
                    fusion = group
                except Exception as e:
                    print(f"Debug: Error creating group: {str(e)}")
                    # Just return the ribs as separate objects
                    fusion = x_rib  # Return one of the ribs as a reference
                
            elif pattern == 'radial':
                # Create radial ribs from center
                rib_count = 6
                radius = max(bbox.XLength, bbox.YLength) / 2
                
                # Get the part's shape
                part_shape = part.Shape.copy()
                
                # Create all rib shapes
                rib_shapes = []
                for i in range(rib_count):
                    angle = i * (360 / rib_count)
                    rad_angle = math.radians(angle)
                    
                    # Create box
                    box = Part.makeBox(radius, thickness, height, 
                                      FreeCAD.Vector(0, -thickness/2, 0))
                    
                    # Rotate and position
                    rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), angle)
                    box.rotate(FreeCAD.Vector(0, 0, 0), rotation.Axis, rotation.Angle)
                    box.translate(FreeCAD.Vector(center_x, center_y, bottom_z))
                    
                    rib_shapes.append(box)
                
                # Create individual rib objects instead of trying to fuse them
                rib_objects = []
                for i in range(rib_count):
                    angle = i * (360 / rib_count)
                    
                    # Create a box for each rib
                    rib = doc.addObject("Part::Box", f"Rib{i}")
                    rib.Length = radius
                    rib.Width = thickness
                    rib.Height = height
                    
                    # Position and rotate the rib
                    rib.Placement.Base = FreeCAD.Vector(center_x, center_y, bottom_z)
                    rib.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), angle)
                    
                    rib_objects.append(rib)
                
                doc.recompute()
                
                # Create a group to keep them together
                try:
                    import Draft
                    group = doc.addObject("App::DocumentObjectGroup", "RadialRibGroup")
                    for rib in rib_objects:
                        group.addObject(rib)
                    print("Debug: Created radial rib group")
                    fusion = group
                except Exception as e:
                    print(f"Debug: Error creating group: {str(e)}")
                    # Just return one of the ribs as a reference
                    fusion = rib_objects[0] if rib_objects else part
                
            # Recompute document to update the fusion
            doc.recompute()
            
            return {
                'success': True,
                'message': f'Added {rib_count} {pattern} ribs ({thickness}mm thick, {height}mm tall)',
                'pattern': pattern,
                'count': rib_count,
                'object': fusion if 'fusion' in locals() else None
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error adding fillets: {str(e)}'}
    
    def add_chamfers(self, part, distance=1.0, edges='auto'):
        """Add chamfers to edges"""
        doc = FreeCAD.ActiveDocument
        if not doc:
            return {'success': False, 'message': 'No active document'}
            
        try:
            # Similar to fillets but with chamfer
            if edges == 'auto':
                edges_to_chamfer = []
                for i, edge in enumerate(part.Shape.Edges):
                    if edge.Length > 2:  # Suitable for chamfering
                        edges_to_chamfer.append(i + 1)
                        
                edges_to_chamfer = edges_to_chamfer[:8]  # Limit
            else:
                edges_to_chamfer = edges
                
            if not edges_to_chamfer:
                return {'success': False, 'message': 'No suitable edges found'}
                
            # Create chamfer
            chamfer = doc.addObject("Part::Chamfer", "Chamfer")
            chamfer.Base = part
            
            edge_list = [(part, f"Edge{i}") for i in edges_to_chamfer]
            chamfer.Edges = edge_list
            
            doc.recompute()
            
            return {
                'success': True,
                'message': f'Added {distance}mm chamfers to {len(edges_to_chamfer)} edges',
                'edges_chamfered': len(edges_to_chamfer)
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error adding chamfers: {str(e)}'}
    
    def create_shell(self, thickness=None):
        """Create a shell from a solid by hollowing it out"""
        if thickness is None:
            thickness = 1.0  # Default thickness
            
        try:
            doc = FreeCAD.ActiveDocument
            if not doc:
                return {'success': False, 'message': 'No active document'}
                
            # Get selected object
            selection = FreeCADGui.Selection.getSelection()
            if not selection:
                return {'success': False, 'message': 'No object selected'}
                
            obj = selection[0]
            
            # Create shell
            shell = doc.addObject("Part::Thickness", "Shell")
            shell.Faces = []
            shell.Value = thickness
            shell.SourceObject = obj
            shell.Mode = 0  # Skin inside
            shell.Join = 2  # Intersection
            
            doc.recompute()
            
            return {
                'success': True,
                'wall_thickness': thickness,
                'object': shell
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error creating shell: {str(e)}'}
            
    def create_fillet(self, radius=None, edges=None):
        """Create fillets on selected edges or all edges of selected object
        
        Parameters:
        - radius: float, fillet radius in mm
        - edges: list of edge indices or None for all edges
        
        Returns:
        - Dictionary with success status, message, and fillet object
        """
        print(f"Debug: Creating fillet with radius={radius}, edges={edges}")
        
        # Set default radius if not provided
        if radius is None:
            radius = self.fillet_radius
            print(f"Debug: Using default fillet radius: {radius}mm")
        
        try:
            doc = FreeCAD.ActiveDocument
            if not doc:
                print("Debug: No active document")
                return {'success': False, 'message': 'No active document'}
            
            # Get current selection
            selection = FreeCADGui.Selection.getSelectionEx()
            if not selection:
                print("Debug: No object selected")
                return {'success': False, 'message': 'No object selected. Please select an object first.'}
            
            results = []
            for sel_obj in selection:
                obj = sel_obj.Object
                print(f"Debug: Processing object {obj.Name}")
                
                # Check if edges are selected
                selected_edges = []
                if sel_obj.SubElementNames:
                    for sub in sel_obj.SubElementNames:
                        if sub.startswith('Edge'):
                            edge_idx = int(sub.replace('Edge', '')) - 1
                            selected_edges.append(edge_idx)
                            print(f"Debug: Selected edge: {sub}")
                
                # If no specific edges selected and no edges parameter, use all edges
                if not selected_edges and edges is None:
                    print("Debug: No specific edges selected, using all edges")
                    selected_edges = list(range(len(obj.Shape.Edges)))
                elif edges is not None:
                    selected_edges = edges
                
                if not selected_edges:
                    print("Debug: No edges to fillet")
                    continue
                
                try:
                    # Create fillet
                    fillet_name = f"Fillet_{obj.Name}"
                    fillet = doc.addObject("Part::Fillet", fillet_name)
                    
                    # Ensure the base object is properly linked
                    try:
                        # Make sure the object is in the document
                        if obj.Document is None or obj.Document.Name != doc.Name:
                            print(f"Debug: Object {obj.Name} not properly linked to document, cannot create fillet")
                            continue
                            
                        # Set the base object and ensure it's not deleted
                        fillet.Base = obj
                        print(f"Debug: Set base object for fillet to {obj.Name}")
                    except Exception as link_e:
                        print(f"Debug: Error linking base object: {str(link_e)}")
                        continue
                    
                    # Add edges to fillet
                    edge_strings = []
                    for edge_idx in selected_edges:
                        if edge_idx < len(obj.Shape.Edges):
                            edge_strings.append((edge_idx+1, radius, radius))
                        else:
                            print(f"Debug: Edge index {edge_idx} out of range for object {obj.Name}")
                    
                    fillet.Edges = edge_strings
                    
                    # Set appearance properties
                    if hasattr(FreeCADGui, "ActiveDocument") and FreeCADGui.ActiveDocument:
                        try:
                            # Set color for the fillet
                            FreeCADGui.ActiveDocument.getObject(fillet.Name).ShapeColor = (0.8, 0.2, 0.2)
                            
                            # Hide the original object but keep it in the document
                            # This is critical to maintain the parametric link
                            FreeCADGui.ActiveDocument.getObject(obj.Name).Visibility = False
                            
                            # Make the original object non-selectable to avoid confusion
                            FreeCADGui.ActiveDocument.getObject(obj.Name).Selectable = False
                            
                            print(f"Debug: Hidden original object {obj.Name} and made it non-selectable")
                        except Exception as vis_e:
                            print(f"Debug: Could not set appearance properties: {str(vis_e)}")
                            
                        # Ensure the fillet object is selectable and visible
                        try:
                            FreeCADGui.ActiveDocument.getObject(fillet.Name).Visibility = True
                            FreeCADGui.ActiveDocument.getObject(fillet.Name).Selectable = True
                        except Exception as sel_e:
                            print(f"Debug: Could not set fillet properties: {str(sel_e)}")
                    
                    doc.recompute()
                    
                    results.append({
                        'object': fillet,
                        'radius': radius,
                        'edges': len(edge_strings)
                    })
                    print(f"Debug: Successfully created fillet {fillet.Name} with {len(edge_strings)} edges")
                    
                except Exception as inner_e:
                    print(f"Debug: Error creating fillet for {obj.Name}: {str(inner_e)}")
            
            if not results:
                print("Debug: No fillets were created")
                return {'success': False, 'message': 'No fillets were created. Please check your selection.'}
            
            print(f"Debug: Successfully created {len(results)} fillets")
            return {
                'success': True,
                'message': f'Created {len(results)} fillet(s) with radius {radius}mm',
                'fillets': results
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Debug: Error creating fillet: {str(e)}")
            return {'success': False, 'message': f'Error creating fillet: {str(e)}'}
    
    def shell_part(self, thickness=2.0, faces_to_remove='auto'):
        """Create a hollow shell from a solid part"""
        print(f"Debug: Creating shell with thickness={thickness}mm")
        
        doc = FreeCAD.ActiveDocument
        if not doc:
            return {'success': False, 'message': 'No active document'}
            
        try:
            # Get selection
            selection = FreeCADGui.Selection.getSelection()
            if not selection:
                return {'success': False, 'message': 'No object selected'}
            part = selection[0]
            
            print(f"Debug: Creating shell for {part.Name} with thickness {thickness}mm")
            
            # Try to use makeThickness directly on the shape
            try:
                # Create a new shape using makeThickness
                shell_shape = part.Shape.makeThickness(
                    [0],  # Face indices (0 = first face)
                    thickness,
                    1.0e-3  # Tolerance
                )
                
                # Create a new object with the shell shape
                shell = doc.addObject("Part::Feature", f"{part.Name}_Shell")
                shell.Shape = shell_shape
                print("Debug: Created shell using makeThickness")
                
            except Exception as e:
                print(f"Debug: makeThickness failed: {str(e)}")
                print("Debug: Using fallback box-cutting approach")
                
                # Fallback: Create a hollow shell by cutting an inner box from an outer box
                bbox = part.Shape.BoundBox
                
                # Create outer box (original size)
                outer_box = doc.addObject("Part::Box", f"{part.Name}_Outer")
                outer_box.Length = bbox.XLength
                outer_box.Width = bbox.YLength
                outer_box.Height = bbox.ZLength
                outer_box.Placement.Base = FreeCAD.Vector(bbox.XMin, bbox.YMin, bbox.ZMin)
                
                # Create inner box (smaller by thickness)
                inner_box = doc.addObject("Part::Box", f"{part.Name}_Inner")
                inner_box.Length = bbox.XLength - 2 * thickness
                inner_box.Width = bbox.YLength - 2 * thickness
                inner_box.Height = bbox.ZLength - 2 * thickness
                inner_box.Placement.Base = FreeCAD.Vector(
                    bbox.XMin + thickness,
                    bbox.YMin + thickness,
                    bbox.ZMin + thickness
                )
                
                # Cut inner from outer
                shell = doc.addObject("Part::Cut", f"{part.Name}_Shell")
                shell.Base = outer_box
                shell.Tool = inner_box
                
                print("Debug: Created shell using box-cutting approach")
            
            # Recompute document to update the shell
            doc.recompute()
            
            return {
                'success': True,
                'message': f'Created shell with {thickness}mm wall thickness',
                'wall_thickness': thickness,
                'object': shell
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error creating shell: {str(e)}'}
        finally:
            pass  # Add a finally clause to complete the try statement
    def extrude_face(self, distance=None, direction=None):
        """Extrude selected face by specified distance
        
        Parameters:
        - distance: float, extrusion distance in mm
        - direction: string, 'up', 'down', or 'auto' for face normal
        
        Returns:
        - Dictionary with success status, message, and extrusion results
        """
        print(f"Debug: Extruding face by distance={distance}, direction={direction}")
        
        # Set default values if not provided
        if distance is None:
            distance = self.extrude_distance
            print(f"Debug: Using default extrusion distance: {distance}mm")
            
        if direction is None:
            direction = 'auto'
            print(f"Debug: Using default direction: {direction}")
            
        # Ensure distance is positive
        abs_distance = abs(distance)
        
        # Check for active document
        doc = FreeCAD.ActiveDocument
        if not doc:
            print("Debug: No active document")
            return {'success': False, 'message': 'No active document'}
            
        try:
            # Get current selection
            selection = FreeCADGui.Selection.getSelectionEx()
            if not selection:
                print("Debug: No face selected")
                return {'success': False, 'message': 'No face selected. Please select a face first.'}
                
            print(f"Debug: Found {len(selection)} selected items")
            
            # Process each selected item
            results = []
            for sel in selection:
                obj = sel.Object
                for sub in sel.SubElementNames:
                    print(f"Debug: Processing {obj.Name}.{sub}")
                    
                    if not sub.startswith('Face'):
                        print(f"Debug: Selected element {sub} is not a face, skipping")
                        continue
                        
                    # Create extrusion using a different approach
                    face_name = sub
                    face_idx = int(sub.replace('Face', '')) - 1
                    
                    if face_idx < len(obj.Shape.Faces):
                        face = obj.Shape.Faces[face_idx]
                        
                        # Determine extrusion direction
                        if direction == 'up':
                            # Positive Z direction
                            extrude_dir = FreeCAD.Vector(0, 0, abs_distance)
                            print("Debug: Extruding in +Z (up) direction")
                        elif direction == 'down':
                            # Negative Z direction
                            extrude_dir = FreeCAD.Vector(0, 0, -abs_distance)
                            print("Debug: Extruding in -Z (down) direction")
                        else:  # 'auto' or any other value
                            # Use face normal
                            normal = face.normalAt(0, 0)
                            if normal.Length > 0.001:
                                normal.normalize()
                                extrude_dir = normal.multiply(abs_distance)
                                print(f"Debug: Extruding along face normal: {normal}")
                            else:
                                # Fallback to Z direction if normal is too small
                                extrude_dir = FreeCAD.Vector(0, 0, abs_distance)
                                print("Debug: Face normal too small, using +Z direction")
                        
                        try:
                            # Create the extrusion shape
                            extruded_shape = face.extrude(extrude_dir)
                            
                            # Create a new object with the extruded shape
                            extrude_name = f"Extrude_{obj.Name}_{face_idx+1}"
                            extrude = doc.addObject("Part::Feature", extrude_name)
                            extrude.Shape = extruded_shape
                            
                            # Set appearance properties
                            if hasattr(FreeCADGui, "ActiveDocument") and FreeCADGui.ActiveDocument:
                                try:
                                    FreeCADGui.ActiveDocument.getObject(extrude.Name).ShapeColor = (0.0, 0.6, 0.8)
                                except:
                                    print("Debug: Could not set shape color")
                            
                            # Add to results
                            results.append({
                                'object': extrude,
                                'face': face_name,
                                'distance': abs_distance,
                                'direction': direction
                            })
                            print(f"Debug: Successfully created extrusion {extrude.Name}")
                        except Exception as inner_e:
                            print(f"Debug: Error creating extrusion for {obj.Name}.{sub}: {str(inner_e)}")
                    else:
                        print(f"Debug: Face index {face_idx} out of range for object {obj.Name}")
            
            # Recompute document after all extrusions
            doc.recompute()
            
            if not results:
                print("Debug: No valid faces were extruded")
                return {'success': False, 'message': 'No valid faces to extrude. Please select a face and try again.'}
                
            print(f"Debug: Successfully extruded {len(results)} faces")
            return {
                'success': True,
                'message': f'Extruded {len(results)} face(s) by {abs_distance}mm',
                'extrusions': results
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Debug: Error extruding face: {str(e)}")
            return {'success': False, 'message': f'Error extruding face: {str(e)}'}
