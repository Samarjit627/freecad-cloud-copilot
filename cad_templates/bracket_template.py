import math
import FreeCAD as App
import Part

def create_bracket(doc=None, 
                   length=100, 
                   width=50, 
                   height=50, 
                   thickness=5, 
                   hole_diameter=8, 
                   fillet_radius=5,
                   mounting_holes=True,
                   reinforcement=False):
    """
    Creates a customizable L-bracket with optional features.
    
    Args:
        doc: FreeCAD document object. If None, a new document is created.
        length: Length of the horizontal arm in mm
        width: Width of the horizontal arm in mm
        height: Height of the vertical arm in mm
        thickness: Material thickness in mm
        hole_diameter: Diameter of mounting holes in mm
        fillet_radius: Radius for fillets in mm
        mounting_holes: Whether to include mounting holes
        reinforcement: Whether to add a reinforcement rib
        
    Returns:
        The FreeCAD document containing the bracket.
    """
    # Create a new document if not provided
    if doc is None:
        doc = App.newDocument("Bracket")
    
    print(f"Creating bracket with dimensions: {length}x{width}x{height}mm")
    
    # Create the horizontal arm
    horizontal = Part.makeBox(length, width, thickness)
    
    # Create the vertical arm
    vertical = Part.makeBox(thickness, width, height)
    
    # Position the vertical arm at the end of the horizontal arm
    vertical.translate(App.Vector(0, 0, 0))
    
    # Fuse the arms together
    try:
        bracket = horizontal.fuse(vertical)
        print("Base bracket shape created successfully")
    except Exception as e:
        print(f"Error fusing bracket parts: {e}")
        # Fallback to using a compound
        bracket = Part.Compound([horizontal, vertical])
    
    # Add fillets if specified
    if fillet_radius > 0:
        try:
            # Find the edge to fillet (the inner corner)
            edges_to_fillet = []
            for edge in bracket.Edges:
                # Find the edge at the intersection of the two arms
                if (abs(edge.Length - width) < 0.01 and 
                    abs(edge.Vertexes[0].Z) < 0.01 and 
                    abs(edge.Vertexes[1].Z) < 0.01 and
                    abs(edge.Vertexes[0].X) < 0.01 and
                    abs(edge.Vertexes[1].X) < 0.01):
                    edges_to_fillet.append(edge)
                    break
            
            if edges_to_fillet:
                bracket = bracket.makeFillet(fillet_radius, edges_to_fillet)
                print(f"Added fillet with radius {fillet_radius}mm")
            else:
                print("Could not find edge to fillet")
        except Exception as e:
            print(f"Error creating fillet: {e}")
    
    # Add mounting holes if specified
    if mounting_holes:
        try:
            # Calculate hole positions
            hole_margin = max(2 * hole_diameter, width/4)
            
            # Holes in horizontal arm
            h1_pos = App.Vector(length/4, width/2, 0)
            h2_pos = App.Vector(3*length/4, width/2, 0)
            
            # Holes in vertical arm
            v1_pos = App.Vector(0, width/2, height/4)
            v2_pos = App.Vector(0, width/2, 3*height/4)
            
            # Create holes
            h1 = Part.makeCylinder(hole_diameter/2, thickness, h1_pos, App.Vector(0,0,1))
            h2 = Part.makeCylinder(hole_diameter/2, thickness, h2_pos, App.Vector(0,0,1))
            v1 = Part.makeCylinder(hole_diameter/2, thickness, v1_pos, App.Vector(1,0,0))
            v2 = Part.makeCylinder(hole_diameter/2, thickness, v2_pos, App.Vector(1,0,0))
            
            # Cut holes from bracket
            bracket = bracket.cut(h1)
            bracket = bracket.cut(h2)
            bracket = bracket.cut(v1)
            bracket = bracket.cut(v2)
            print(f"Added {4} mounting holes with diameter {hole_diameter}mm")
        except Exception as e:
            print(f"Error creating mounting holes: {e}")
    
    # Add reinforcement rib if specified
    if reinforcement:
        try:
            # Create a triangular reinforcement rib
            rib_height = min(height, length) / 2
            rib_width = width
            rib_thickness = thickness / 2
            
            # Create points for the triangular face
            p1 = App.Vector(0, 0, 0)
            p2 = App.Vector(rib_height, 0, rib_height)
            p3 = App.Vector(0, 0, rib_height)
            
            # Create the triangular face
            wire = Part.makePolygon([p1, p2, p3, p1])
            face = Part.Face(wire)
            
            # Extrude the face to create the rib
            rib = face.extrude(App.Vector(0, rib_width, 0))
            
            # Position the rib
            rib.translate(App.Vector(thickness, 0, thickness))
            
            # Fuse the rib to the bracket
            bracket = bracket.fuse(rib)
            print("Added reinforcement rib")
        except Exception as e:
            print(f"Error creating reinforcement rib: {e}")
    
    # Create FreeCAD object
    bracket_obj = doc.addObject("Part::Feature", "Bracket")
    bracket_obj.Shape = bracket
    bracket_obj.Label = f"Bracket {length}x{width}x{height}mm"
    
    # Add information labels
    try:
        info_label = doc.addObject("App::Annotation", "BracketInfo")
        info_label.LabelText = f"Bracket {length}x{width}x{height}mm, t={thickness}mm"
        info_label.Position = App.Vector(length/2, -20, height/2)
    except Exception as e:
        print(f"Could not create labels: {e}")
    
    # Set nice colors
    try:
        import FreeCADGui
        if hasattr(FreeCADGui, 'ActiveDocument') and FreeCADGui.ActiveDocument:
            bracket_obj.ViewObject.ShapeColor = (0.6, 0.6, 0.8)
    except:
        pass
    
    # Recompute and update view
    doc.recompute()
    
    try:
        import FreeCADGui
        if FreeCADGui.ActiveDocument:
            FreeCADGui.ActiveDocument.ActiveView.fitAll()
            FreeCADGui.updateGui()
    except:
        pass
    
    print("Bracket creation complete")
    return doc

if __name__ == "__main__":
    create_bracket()
