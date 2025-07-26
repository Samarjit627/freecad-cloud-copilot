import math
import FreeCAD as App
import Part

def create_enclosure(doc=None, 
                    length=100, 
                    width=80, 
                    height=40, 
                    wall_thickness=2.5, 
                    corner_radius=5,
                    include_lid=True,
                    include_mounting_holes=True,
                    include_ventilation=False,
                    include_cable_cutout=False):
    """
    Creates a customizable enclosure with optional features.
    
    Args:
        doc: FreeCAD document object. If None, a new document is created.
        length: External length of the enclosure in mm
        width: External width of the enclosure in mm
        height: External height of the enclosure in mm
        wall_thickness: Wall thickness in mm
        corner_radius: Radius for rounded corners in mm
        include_lid: Whether to create a removable lid
        include_mounting_holes: Whether to include mounting holes
        include_ventilation: Whether to add ventilation slots
        include_cable_cutout: Whether to add a cable cutout
        
    Returns:
        The FreeCAD document containing the enclosure.
    """
    # Create a new document if not provided
    if doc is None:
        doc = App.newDocument("Enclosure")
    
    print(f"Creating enclosure with dimensions: {length}x{width}x{height}mm")
    
    # Calculate internal dimensions
    inner_length = length - 2 * wall_thickness
    inner_width = width - 2 * wall_thickness
    inner_height = height - 2 * wall_thickness
    
    # Calculate lid height (25% of total height)
    lid_height = height * 0.25 if include_lid else 0
    base_height = height - lid_height if include_lid else height
    
    # Create outer shell with rounded corners
    outer_box = None
    inner_box = None
    
    try:
        if corner_radius > 0 and corner_radius < min(length, width, height) / 2:
            # Create rounded box for outer shell
            outer_box = create_rounded_box(length, width, base_height, corner_radius)
            
            # Create rounded box for inner cavity
            inner_corner_radius = max(0, corner_radius - wall_thickness)
            inner_box = create_rounded_box(inner_length, inner_width, inner_height, inner_corner_radius)
            
            # Position inner box
            inner_box.translate(App.Vector(wall_thickness, wall_thickness, wall_thickness))
        else:
            # Create simple boxes if corner radius is zero or too large
            outer_box = Part.makeBox(length, width, base_height)
            inner_box = Part.makeBox(inner_length, inner_width, inner_height)
            inner_box.translate(App.Vector(wall_thickness, wall_thickness, wall_thickness))
    except Exception as e:
        print(f"Error creating base shapes: {e}")
        # Fallback to simple boxes
        outer_box = Part.makeBox(length, width, base_height)
        inner_box = Part.makeBox(inner_length, inner_width, inner_height)
        inner_box.translate(App.Vector(wall_thickness, wall_thickness, wall_thickness))
    
    # Cut inner cavity from outer shell
    try:
        enclosure_base = outer_box.cut(inner_box)
        print("Created enclosure base with inner cavity")
    except Exception as e:
        print(f"Error cutting inner cavity: {e}")
        enclosure_base = outer_box  # Fallback to solid box
    
    # Add mounting holes if requested
    if include_mounting_holes:
        try:
            hole_diameter = min(5, wall_thickness * 1.5)  # Reasonable hole size
            hole_depth = wall_thickness + 5  # Slightly deeper than wall
            
            # Calculate hole positions (in each corner with margin)
            margin = max(10, corner_radius * 2)
            hole_positions = [
                App.Vector(margin, margin, 0),
                App.Vector(length - margin, margin, 0),
                App.Vector(margin, width - margin, 0),
                App.Vector(length - margin, width - margin, 0)
            ]
            
            # Create and cut holes
            for pos in hole_positions:
                hole = Part.makeCylinder(hole_diameter/2, hole_depth, pos, App.Vector(0,0,1))
                enclosure_base = enclosure_base.cut(hole)
            
            print(f"Added {len(hole_positions)} mounting holes")
        except Exception as e:
            print(f"Error creating mounting holes: {e}")
    
    # Add ventilation slots if requested
    if include_ventilation:
        try:
            slot_width = 15
            slot_height = 2
            slot_depth = wall_thickness + 1  # Slightly deeper than wall
            num_slots = 5
            slot_spacing = (length - 40) / (num_slots + 1)
            
            # Create slots on both sides
            for side in range(2):
                y_pos = side * (width - wall_thickness)
                for i in range(num_slots):
                    x_pos = 20 + (i + 1) * slot_spacing
                    slot_pos = App.Vector(x_pos, y_pos, height/3)
                    
                    # Create slot
                    slot = Part.makeBox(slot_width, wall_thickness + 2, slot_height, slot_pos)
                    enclosure_base = enclosure_base.cut(slot)
            
            print(f"Added {num_slots * 2} ventilation slots")
        except Exception as e:
            print(f"Error creating ventilation slots: {e}")
    
    # Add cable cutout if requested
    if include_cable_cutout:
        try:
            cutout_width = 15
            cutout_height = 8
            cutout_pos = App.Vector(length/2 - cutout_width/2, 0, wall_thickness + 5)
            
            cutout = Part.makeBox(cutout_width, wall_thickness + 1, cutout_height, cutout_pos)
            enclosure_base = enclosure_base.cut(cutout)
            
            print("Added cable cutout")
        except Exception as e:
            print(f"Error creating cable cutout: {e}")
    
    # Create enclosure object
    enclosure_obj = doc.addObject("Part::Feature", "EnclosureBase")
    enclosure_obj.Shape = enclosure_base
    enclosure_obj.Label = "Enclosure Base"
    
    # Create lid if requested
    lid_obj = None
    if include_lid:
        try:
            # Create outer shell of lid
            if corner_radius > 0 and corner_radius < min(length, width) / 2:
                lid_outer = create_rounded_box(length, width, lid_height, corner_radius)
            else:
                lid_outer = Part.makeBox(length, width, lid_height)
            
            # Create inner cutout for lid (slightly smaller than base to create overlap)
            overlap = 0.5
            lid_inner_length = inner_length - overlap * 2
            lid_inner_width = inner_width - overlap * 2
            lid_inner_height = lid_height - wall_thickness
            
            if corner_radius > 0:
                inner_corner_radius = max(0, corner_radius - wall_thickness - overlap)
                lid_inner = create_rounded_box(lid_inner_length, lid_inner_width, lid_inner_height, inner_corner_radius)
            else:
                lid_inner = Part.makeBox(lid_inner_length, lid_inner_width, lid_inner_height)
            
            # Position inner cutout
            lid_inner.translate(App.Vector(wall_thickness + overlap, wall_thickness + overlap, 0))
            
            # Cut inner from outer
            lid = lid_outer.cut(lid_inner)
            
            # Position lid above base
            lid.translate(App.Vector(0, 0, base_height + 10))  # Add gap for visibility
            
            # Create lid object
            lid_obj = doc.addObject("Part::Feature", "EnclosureLid")
            lid_obj.Shape = lid
            lid_obj.Label = "Enclosure Lid"
            
            print("Created enclosure lid")
        except Exception as e:
            print(f"Error creating lid: {e}")
    
    # Add information labels
    try:
        info_label = doc.addObject("App::Annotation", "EnclosureInfo")
        info_label.LabelText = f"Enclosure {length}x{width}x{height}mm, t={wall_thickness}mm"
        info_label.Position = App.Vector(length/2, -20, height/2)
    except Exception as e:
        print(f"Could not create labels: {e}")
    
    # Set nice colors
    try:
        import FreeCADGui
        if hasattr(FreeCADGui, 'ActiveDocument') and FreeCADGui.ActiveDocument:
            enclosure_obj.ViewObject.ShapeColor = (0.8, 0.8, 0.9)
            enclosure_obj.ViewObject.Transparency = 20
            
            if lid_obj:
                lid_obj.ViewObject.ShapeColor = (0.7, 0.7, 0.8)
                lid_obj.ViewObject.Transparency = 20
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
    
    print("Enclosure creation complete")
    return doc

def create_rounded_box(length, width, height, radius):
    """Helper function to create a box with rounded edges"""
    if radius <= 0:
        return Part.makeBox(length, width, height)
    
    # Ensure radius isn't too large
    radius = min(radius, length/2, width/2, height/2)
    
    # Create rounded 2D shape
    points = [
        App.Vector(radius, 0, 0),
        App.Vector(length - radius, 0, 0),
        App.Vector(length, radius, 0),
        App.Vector(length, width - radius, 0),
        App.Vector(length - radius, width, 0),
        App.Vector(radius, width, 0),
        App.Vector(0, width - radius, 0),
        App.Vector(0, radius, 0),
        App.Vector(radius, 0, 0)
    ]
    
    # Create arcs for corners
    arcs = []
    arc_points = [
        (App.Vector(length - radius, radius, 0), App.Vector(length, 0, 0), App.Vector(0, 0, 1)),
        (App.Vector(length - radius, width - radius, 0), App.Vector(0, length, 0), App.Vector(0, 0, 1)),
        (App.Vector(radius, width - radius, 0), App.Vector(-length, 0, 0), App.Vector(0, 0, 1)),
        (App.Vector(radius, radius, 0), App.Vector(0, -length, 0), App.Vector(0, 0, 1))
    ]
    
    edges = []
    for i in range(len(points) - 1):
        if i % 2 == 0:  # Straight edge
            edges.append(Part.makeLine(points[i], points[i+1]))
        else:  # Arc edge
            center, direction, normal = arc_points[i // 2]
            edges.append(Part.makeCircle(radius, center, normal, 0, 90))
    
    # Create wire from edges
    wire = Part.Wire(edges)
    face = Part.Face(wire)
    
    # Extrude to create 3D shape
    box = face.extrude(App.Vector(0, 0, height))
    
    return box

if __name__ == "__main__":
    create_enclosure()
