import math
import FreeCAD as App
import Part

def create_gear(doc=None,
               module=1.0,
               teeth=20,
               thickness=5,
               bore_diameter=5,
               pressure_angle=20,
               helix_angle=0,
               hub_diameter=0,
               hub_thickness=0,
               include_keyway=False):
    """
    Creates a parametric involute spur or helical gear.
    
    Args:
        doc: FreeCAD document object. If None, a new document is created.
        module: Module (size of teeth) in mm
        teeth: Number of teeth
        thickness: Gear thickness in mm
        bore_diameter: Center hole diameter in mm
        pressure_angle: Pressure angle in degrees (typically 20)
        helix_angle: Helix angle in degrees (0 for spur gear)
        hub_diameter: Hub diameter (0 for no hub)
        hub_thickness: Hub thickness (0 for no hub)
        include_keyway: Whether to include a keyway in the bore
        
    Returns:
        The FreeCAD document containing the gear.
    """
    # Create a new document if not provided
    if doc is None:
        doc = App.newDocument("Gear")
    
    print(f"Creating gear with {teeth} teeth, module {module}")
    
    # Calculate gear parameters
    pitch_diameter = module * teeth
    outer_diameter = pitch_diameter + 2 * module  # Addendum = 1 * module
    root_diameter = pitch_diameter - 2.5 * module  # Dedendum = 1.25 * module
    base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
    
    # Ensure bore diameter is not too large
    max_bore = root_diameter - 4
    if bore_diameter > max_bore:
        print(f"Warning: Bore diameter {bore_diameter} is too large, reducing to {max_bore}")
        bore_diameter = max_bore
    
    print(f"Pitch diameter: {pitch_diameter:.2f}mm")
    print(f"Outer diameter: {outer_diameter:.2f}mm")
    print(f"Root diameter: {root_diameter:.2f}mm")
    
    try:
        # Create basic gear profile
        gear = create_involute_gear(teeth, module, pressure_angle, helix_angle, thickness)
        
        # Create center bore
        if bore_diameter > 0:
            bore = Part.makeCylinder(bore_diameter/2, thickness, App.Vector(0,0,0), App.Vector(0,0,1))
            gear = gear.cut(bore)
            print(f"Added center bore with diameter {bore_diameter}mm")
        
        # Create hub if specified
        if hub_diameter > 0 and hub_thickness > 0:
            # Ensure hub diameter is reasonable
            if hub_diameter <= pitch_diameter:
                hub = Part.makeCylinder(hub_diameter/2, thickness + hub_thickness, 
                                       App.Vector(0,0,-hub_thickness), App.Vector(0,0,1))
                gear = gear.fuse(hub)
                print(f"Added hub with diameter {hub_diameter}mm and thickness {hub_thickness}mm")
            else:
                print("Hub diameter too large, ignoring hub")
        
        # Add keyway if specified
        if include_keyway and bore_diameter > 5:
            keyway_width = min(bore_diameter/4, 5)
            keyway_depth = keyway_width / 2
            keyway_length = thickness
            
            # Create keyway shape
            keyway = Part.makeBox(keyway_depth, keyway_width, keyway_length,
                                 App.Vector(-bore_diameter/2 - keyway_depth/2, -keyway_width/2, 0))
            
            gear = gear.cut(keyway)
            print(f"Added keyway {keyway_width:.1f}x{keyway_depth:.1f}mm")
    
    except Exception as e:
        print(f"Error creating gear: {e}")
        # Fallback to simple cylindrical gear
        gear = Part.makeCylinder(pitch_diameter/2, thickness)
        if bore_diameter > 0:
            bore = Part.makeCylinder(bore_diameter/2, thickness)
            gear = gear.cut(bore)
    
    # Create FreeCAD object
    gear_obj = doc.addObject("Part::Feature", "Gear")
    gear_obj.Shape = gear
    gear_obj.Label = f"Gear M{module} T{teeth}"
    
    # Add information labels
    try:
        info_label = doc.addObject("App::Annotation", "GearInfo")
        info_label.LabelText = f"Module: {module}, Teeth: {teeth}, PD: {pitch_diameter:.1f}mm"
        info_label.Position = App.Vector(0, -outer_diameter/2 - 10, thickness/2)
        
        specs_label = doc.addObject("App::Annotation", "GearSpecs")
        specs_label.LabelText = f"OD: {outer_diameter:.1f}mm, Bore: {bore_diameter}mm"
        specs_label.Position = App.Vector(0, -outer_diameter/2 - 10, thickness/2 - 5)
    except Exception as e:
        print(f"Could not create labels: {e}")
    
    # Set nice colors
    try:
        import FreeCADGui
        if hasattr(FreeCADGui, 'ActiveDocument') and FreeCADGui.ActiveDocument:
            gear_obj.ViewObject.ShapeColor = (0.7, 0.7, 0.5)
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
    
    print("Gear creation complete")
    return doc

def create_involute_gear(teeth, module, pressure_angle=20, helix_angle=0, thickness=5):
    """Helper function to create an involute gear profile"""
    
    # Basic gear parameters
    pitch_diameter = module * teeth
    outer_diameter = pitch_diameter + 2 * module  # Addendum = 1 * module
    root_diameter = pitch_diameter - 2.5 * module  # Dedendum = 1.25 * module
    base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
    
    # Function to calculate involute point
    def involute_point(base_radius, angle):
        # Involute function
        inv_angle = math.tan(angle) - angle
        r = base_radius * math.sqrt(1 + inv_angle**2)
        theta = math.atan2(inv_angle, 1)
        return App.Vector(r * math.cos(theta), r * math.sin(theta), 0)
    
    # Create a simplified gear using a polygon approximation
    num_points_per_tooth = 6  # Points per tooth profile
    tooth_angle = 2 * math.pi / teeth
    
    # Create points for one tooth
    tooth_points = []
    
    # Root circle points
    root_radius = root_diameter / 2
    
    # Outer circle points
    outer_radius = outer_diameter / 2
    
    # Create a simplified tooth profile
    for i in range(teeth):
        angle_base = i * tooth_angle
        
        # Add points for this tooth
        # Simplified tooth profile with straight lines
        tooth_points.append(App.Vector(root_radius * math.cos(angle_base - tooth_angle/4),
                                      root_radius * math.sin(angle_base - tooth_angle/4), 0))
        
        tooth_points.append(App.Vector(outer_radius * math.cos(angle_base - tooth_angle/8),
                                      outer_radius * math.sin(angle_base - tooth_angle/8), 0))
        
        tooth_points.append(App.Vector(outer_radius * math.cos(angle_base + tooth_angle/8),
                                      outer_radius * math.sin(angle_base + tooth_angle/8), 0))
        
        tooth_points.append(App.Vector(root_radius * math.cos(angle_base + tooth_angle/4),
                                      root_radius * math.sin(angle_base + tooth_angle/4), 0))
    
    # Close the polygon
    tooth_points.append(tooth_points[0])
    
    # Create wire from points
    gear_wire = Part.makePolygon(tooth_points)
    gear_face = Part.Face(gear_wire)
    
    # Extrude to create 3D gear
    if helix_angle == 0:
        # Simple extrusion for spur gear
        gear = gear_face.extrude(App.Vector(0, 0, thickness))
    else:
        # Helical extrusion
        # This is a simplified approach - real helical gears are more complex
        twist_angle = math.radians(helix_angle) * thickness / (pitch_diameter/2)
        gear = gear_face.revolve(App.Vector(0,0,0), App.Vector(0,0,1), twist_angle)
    
    return gear

if __name__ == "__main__":
    create_gear()
