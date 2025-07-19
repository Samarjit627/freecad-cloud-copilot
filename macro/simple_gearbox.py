"""
Simple Gearbox Generator for FreeCAD
This module creates a simple gearbox assembly without using complex boolean operations
that might cause "shape is invalid" errors.
"""

import math
import re
import time

# Try to import FreeCAD modules, but allow the module to be imported for inspection
# even when FreeCAD is not available
try:
    import FreeCAD
    import Part
    from FreeCAD import Base
    FREECAD_AVAILABLE = True
except ImportError:
    print("Warning: FreeCAD modules not available. Only extraction functions will work.")
    FREECAD_AVAILABLE = False

def create_simple_gearbox(ratio, motor_type="NEMA17"):
    """Create a simple gearbox assembly with the specified ratio and motor type.
    
    Args:
    - ratio: Gear ratio (output teeth / input teeth)
    - motor_type: Motor type (e.g., "NEMA17", "NEMA23")
    
    Returns:
    - Dictionary with success status, message, and document
    """
    print(f"\n==== CREATING SIMPLE GEARBOX ====\nRatio: {ratio}\nMotor Type: {motor_type}\n")
    print(f"Creating simple gearbox with ratio {ratio} and motor type {motor_type}")
    
    # Check if FreeCAD is available
    if not FREECAD_AVAILABLE:
        return {
            'success': False,
            'message': 'FreeCAD modules not available. Cannot create gearbox.'
        }
    
    # Close any existing document with the same name to avoid conflicts
    for doc in FreeCAD.listDocuments().values():
        if doc.Name == "Simple_Gearbox":
            print(f"Closing existing document {doc.Name}")
            FreeCAD.closeDocument(doc.Name)
    
    # Create new document
    doc = FreeCAD.newDocument("Simple_Gearbox")
    components = []
    
    try:
        print("Debug: Starting gearbox component creation")
        # Calculate gear teeth based on ratio
        input_teeth = 20
        output_teeth = int(input_teeth * ratio)
        print(f"Debug: Calculated teeth - input: {input_teeth}, output: {output_teeth}")
        
        # Calculate dimensions
        module = 2.0  # mm per tooth
        input_diameter = input_teeth * module
        output_diameter = output_teeth * module
        # Correct center distance for proper meshing
        center_distance = (input_diameter + output_diameter) / 2
        print(f"Debug: Calculated dimensions - input diameter: {input_diameter}mm, output diameter: {output_diameter}mm, center distance: {center_distance}mm")
        
        # Create housing (base plate) - make it larger to accommodate the 10:1 ratio gears
        housing_width = center_distance + 80  # Wider to fit large output gear
        housing_depth = 100  # Deeper for better visibility
        housing_height = 10
        
        housing = Part.makeBox(housing_width, housing_depth, housing_height)
        housing.translate(Base.Vector(-30, -housing_depth/2, 0))  # Position further left
        housing_obj = doc.addObject("Part::Feature", "Housing_Base")
        housing_obj.Shape = housing
        if hasattr(housing_obj, "ViewObject"):
            housing_obj.ViewObject.ShapeColor = (0.2, 0.2, 0.8)  # Blue
            housing_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("housing_base", housing_obj))
        print(f"Debug: Created housing base: {housing_obj.Name}, size: {housing_width}x{housing_depth}x{housing_height}mm")
        
        # Create housing walls - taller and more visible
        wall_thickness = 5
        wall_height = 40  # Taller walls
        
        # Front wall
        front_wall = Part.makeBox(housing_width, wall_thickness, wall_height)
        front_wall.translate(Base.Vector(-30, -housing_depth/2, housing_height))
        front_wall_obj = doc.addObject("Part::Feature", "Housing_FrontWall")
        front_wall_obj.Shape = front_wall
        if hasattr(front_wall_obj, "ViewObject"):
            front_wall_obj.ViewObject.ShapeColor = (0.2, 0.2, 0.8)  # Blue
            front_wall_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("front_wall", front_wall_obj))
        print(f"Debug: Created front wall: {front_wall_obj.Name}")
        
        # Back wall
        back_wall = Part.makeBox(housing_width, wall_thickness, wall_height)
        back_wall.translate(Base.Vector(-30, housing_depth/2 - wall_thickness, housing_height))
        back_wall_obj = doc.addObject("Part::Feature", "Housing_BackWall")
        back_wall_obj.Shape = back_wall
        if hasattr(back_wall_obj, "ViewObject"):
            back_wall_obj.ViewObject.ShapeColor = (0.2, 0.2, 0.8)  # Blue
            back_wall_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("back_wall", back_wall_obj))
        print(f"Debug: Created back wall: {back_wall_obj.Name}")
        
        # Left wall
        left_wall = Part.makeBox(wall_thickness, housing_depth - 2*wall_thickness, wall_height)
        left_wall.translate(Base.Vector(-30, -housing_depth/2 + wall_thickness, housing_height))
        left_wall_obj = doc.addObject("Part::Feature", "Housing_LeftWall")
        left_wall_obj.Shape = left_wall
        if hasattr(left_wall_obj, "ViewObject"):
            left_wall_obj.ViewObject.ShapeColor = (0.2, 0.2, 0.8)  # Blue
            left_wall_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("left_wall", left_wall_obj))
        print(f"Debug: Created left wall: {left_wall_obj.Name}")
        
        # Right wall
        right_wall = Part.makeBox(wall_thickness, housing_depth - 2*wall_thickness, wall_height)
        right_wall.translate(Base.Vector(housing_width - 30 - wall_thickness, -housing_depth/2 + wall_thickness, housing_height))
        right_wall_obj = doc.addObject("Part::Feature", "Housing_RightWall")
        right_wall_obj.Shape = right_wall
        if hasattr(right_wall_obj, "ViewObject"):
            right_wall_obj.ViewObject.ShapeColor = (0.2, 0.2, 0.8)  # Blue
            right_wall_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("right_wall", right_wall_obj))
        print(f"Debug: Created right wall: {right_wall_obj.Name}")
        
        # Create input gear with improved teeth
        gear_thickness = 15  # Thicker gears
        tooth_height = 5.0  # Taller teeth for better visibility
        tooth_width_angle = 360.0 / (input_teeth * 3)  # Width of tooth in degrees (adjusted for better appearance)
        
        # Create base cylinder for input gear
        input_gear_base = Part.makeCylinder(input_diameter/2 - tooth_height, gear_thickness)
        
        # Create teeth for input gear - improved shape
        input_gear_with_teeth = input_gear_base
        for i in range(input_teeth):
            # Calculate tooth position
            angle = i * 360.0 / input_teeth  # Angle in degrees
            
            # Create tooth as a trapezoid (wider at base, narrower at tip) for better gear teeth appearance
            tooth_width = 2 * math.pi * (input_diameter/2) * tooth_width_angle / 360.0
            
            # Create points for a trapezoid shape
            base_radius = input_diameter/2 - tooth_height
            tip_radius = input_diameter/2 + tooth_height/2  # Slightly extended for better meshing
            
            # Create a box shape for each tooth (simpler than wedge to avoid parameter issues)
            tooth = Part.makeBox(tooth_height*1.5, tooth_width, gear_thickness)
            
            # Position and rotate tooth
            tooth.translate(Base.Vector(base_radius, -tooth_width/2, 0))
            tooth.rotate(Base.Vector(0, 0, 0), Base.Vector(0, 0, 1), angle)
            
            # Add tooth to gear
            input_gear_with_teeth = input_gear_with_teeth.fuse(tooth)
        
        # Position the gear
        input_gear_with_teeth.translate(Base.Vector(0, 0, housing_height + 15))
        input_gear_obj = doc.addObject("Part::Feature", "InputGear")
        input_gear_obj.Shape = input_gear_with_teeth
        if hasattr(input_gear_obj, "ViewObject"):
            input_gear_obj.ViewObject.ShapeColor = (0.9, 0.2, 0.2)  # Bright Red
            input_gear_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("input_gear", input_gear_obj))
        print(f"Debug: Created input gear with teeth: {input_gear_obj.Name}, diameter: {input_diameter}mm, teeth: {input_teeth}")
        
        # Create output gear with improved teeth - matching input gear style
        tooth_width_angle = 360.0 / (output_teeth * 3)  # Width of tooth in degrees (adjusted for better appearance)
        
        # Create base cylinder for output gear
        output_gear_base = Part.makeCylinder(output_diameter/2 - tooth_height, gear_thickness)
        
        # Create teeth for output gear - improved shape
        output_gear_with_teeth = output_gear_base
        for i in range(output_teeth):
            # Calculate tooth position
            angle = i * 360.0 / output_teeth  # Angle in degrees
            
            # Create tooth as a trapezoid (wider at base, narrower at tip) for better gear teeth appearance
            tooth_width = 2 * math.pi * (output_diameter/2) * tooth_width_angle / 360.0
            
            # Create points for a trapezoid shape
            base_radius = output_diameter/2 - tooth_height
            tip_radius = output_diameter/2 + tooth_height/2  # Slightly extended for better meshing
            
            # Create a box shape for each tooth (simpler than wedge to avoid parameter issues)
            tooth = Part.makeBox(tooth_height*1.5, tooth_width, gear_thickness)
            
            # Position and rotate tooth
            tooth.translate(Base.Vector(base_radius, -tooth_width/2, 0))
            tooth.rotate(Base.Vector(0, 0, 0), Base.Vector(0, 0, 1), angle)
            
            # Add tooth to gear
            output_gear_with_teeth = output_gear_with_teeth.fuse(tooth)
        
        # Position the gear - ensure proper alignment with input gear for meshing
        # Calculate rotation to mesh gears properly
        mesh_angle = 180.0 / output_teeth + (360.0 / output_teeth / 4)  # Adjusted for better meshing
        output_gear_with_teeth.rotate(Base.Vector(0, 0, 0), Base.Vector(0, 0, 1), mesh_angle)
        output_gear_with_teeth.translate(Base.Vector(center_distance, 0, housing_height + 15))
        
        # Add debug info to verify 10:1 ratio
        print(f"Debug: GEAR RATIO CHECK: {output_teeth}/{input_teeth} = {output_teeth/input_teeth:.1f}:1")
        
        output_gear_obj = doc.addObject("Part::Feature", "OutputGear")
        output_gear_obj.Shape = output_gear_with_teeth
        if hasattr(output_gear_obj, "ViewObject"):
            output_gear_obj.ViewObject.ShapeColor = (0.2, 0.9, 0.2)  # Bright Green
            output_gear_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("output_gear", output_gear_obj))
        print(f"Debug: Created output gear with teeth: {output_gear_obj.Name}, diameter: {output_diameter}mm, teeth: {output_teeth}")
        
        # Create input shaft - make it more visible and align with gear
        input_shaft_diameter = 10  # Thicker shaft
        input_shaft_length = 80    # Longer shaft for better visibility
        
        # Position shaft to extend through gear and housing
        input_shaft = Part.makeCylinder(input_shaft_diameter/2, input_shaft_length)
        # Center the shaft vertically with the gear
        input_shaft.translate(Base.Vector(0, 0, housing_height + 15 - input_shaft_length/4))
        
        input_shaft_obj = doc.addObject("Part::Feature", "InputShaft")
        input_shaft_obj.Shape = input_shaft
        if hasattr(input_shaft_obj, "ViewObject"):
            input_shaft_obj.ViewObject.ShapeColor = (0.9, 0.9, 0.2)  # Yellow
            input_shaft_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("input_shaft", input_shaft_obj))
        print(f"Debug: Created input shaft: {input_shaft_obj.Name}, diameter: {input_shaft_diameter}mm, length: {input_shaft_length}mm")
        
        # Create output shaft - make it more visible and align with gear
        output_shaft_diameter = 10  # Thicker shaft
        output_shaft_length = 80    # Longer shaft for better visibility
        
        # Position shaft to extend through gear and housing
        output_shaft = Part.makeCylinder(output_shaft_diameter/2, output_shaft_length)
        # Center the shaft vertically with the gear
        output_shaft.translate(Base.Vector(center_distance, 0, housing_height + 15 - output_shaft_length/4))
        
        output_shaft_obj = doc.addObject("Part::Feature", "OutputShaft")
        output_shaft_obj.Shape = output_shaft
        if hasattr(output_shaft_obj, "ViewObject"):
            output_shaft_obj.ViewObject.ShapeColor = (0.9, 0.9, 0.2)  # Yellow
            output_shaft_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("output_shaft", output_shaft_obj))
        print(f"Debug: Created output shaft: {output_shaft_obj.Name}, diameter: {output_shaft_diameter}mm, length: {output_shaft_length}mm")
        
        # Create input bearings - aligned with shafts
        bearing_width = 8  # Wider bearings
        bearing_outer_diameter = 20  # Larger bearings
        bearing_inner_diameter = input_shaft_diameter
        
        # Calculate bearing positions based on shaft position
        input_shaft_z_pos = housing_height + 15 - input_shaft_length/4
        
        # Front bearing for input shaft
        bearing_outer = Part.makeCylinder(bearing_outer_diameter/2, bearing_width)
        bearing_outer.rotate(Base.Vector(0, 0, 0), Base.Vector(1, 0, 0), 90)  # Rotate to align with shaft
        bearing_outer.translate(Base.Vector(0, -housing_depth/2 + wall_thickness, input_shaft_z_pos + input_shaft_length/4))
        bearing_outer_obj = doc.addObject("Part::Feature", "InputBearing_Outer_Front")
        bearing_outer_obj.Shape = bearing_outer
        if hasattr(bearing_outer_obj, "ViewObject"):
            bearing_outer_obj.ViewObject.ShapeColor = (0.7, 0.1, 0.7)  # Purple
            bearing_outer_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("input_bearing_outer", bearing_outer_obj))
        print(f"Debug: Created input front bearing outer: {bearing_outer_obj.Name}")
        
        bearing_inner = Part.makeCylinder(bearing_inner_diameter/2, bearing_width)
        bearing_inner.rotate(Base.Vector(0, 0, 0), Base.Vector(1, 0, 0), 90)  # Rotate to align with shaft
        bearing_inner.translate(Base.Vector(0, -housing_depth/2 + wall_thickness, input_shaft_z_pos + input_shaft_length/4))
        bearing_inner_obj = doc.addObject("Part::Feature", "InputBearing_Inner_Front")
        bearing_inner_obj.Shape = bearing_inner
        if hasattr(bearing_inner_obj, "ViewObject"):
            bearing_inner_obj.ViewObject.ShapeColor = (0.9, 0.9, 0.9)  # White
            bearing_inner_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("input_bearing_inner", bearing_inner_obj))
        print(f"Debug: Created input front bearing inner: {bearing_inner_obj.Name}")
        
        # Back bearing for input shaft
        bearing_outer = Part.makeCylinder(bearing_outer_diameter/2, bearing_width)
        bearing_outer.rotate(Base.Vector(0, 0, 0), Base.Vector(1, 0, 0), 90)  # Rotate to align with shaft
        bearing_outer.translate(Base.Vector(0, housing_depth/2 - wall_thickness - bearing_width, input_shaft_z_pos + input_shaft_length/4))
        bearing_outer_obj = doc.addObject("Part::Feature", "InputBearing_Outer_Back")
        bearing_outer_obj.Shape = bearing_outer
        if hasattr(bearing_outer_obj, "ViewObject"):
            bearing_outer_obj.ViewObject.ShapeColor = (0.7, 0.1, 0.7)  # Purple
            bearing_outer_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("input_bearing_outer_back", bearing_outer_obj))  # Fixed duplicate key
        print(f"Debug: Created input back bearing outer: {bearing_outer_obj.Name}")
        
        bearing_inner = Part.makeCylinder(bearing_inner_diameter/2, bearing_width)
        bearing_inner.rotate(Base.Vector(0, 0, 0), Base.Vector(1, 0, 0), 90)  # Rotate to align with shaft
        bearing_inner.translate(Base.Vector(0, housing_depth/2 - wall_thickness - bearing_width, input_shaft_z_pos + input_shaft_length/4))
        bearing_inner_obj = doc.addObject("Part::Feature", "InputBearing_Inner_Back")
        bearing_inner_obj.Shape = bearing_inner
        if hasattr(bearing_inner_obj, "ViewObject"):
            bearing_inner_obj.ViewObject.ShapeColor = (0.9, 0.9, 0.9)  # White
            bearing_inner_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("input_bearing_inner_back", bearing_inner_obj))  # Fixed duplicate key
        print(f"Debug: Created input back bearing inner: {bearing_inner_obj.Name}")
        
        # Create output bearings - aligned with shaft
        bearing_outer_diameter = 24  # Larger bearings
        bearing_inner_diameter = output_shaft_diameter
        
        # Calculate bearing positions based on shaft position
        output_shaft_z_pos = housing_height + 15 - output_shaft_length/4
        
        # Front bearing for output shaft
        bearing_outer = Part.makeCylinder(bearing_outer_diameter/2, bearing_width)
        bearing_outer.rotate(Base.Vector(0, 0, 0), Base.Vector(1, 0, 0), 90)  # Rotate to align with shaft
        bearing_outer.translate(Base.Vector(center_distance, -housing_depth/2 + wall_thickness, output_shaft_z_pos + output_shaft_length/4))
        bearing_outer_obj = doc.addObject("Part::Feature", "OutputBearing_Outer_Front")
        bearing_outer_obj.Shape = bearing_outer
        if hasattr(bearing_outer_obj, "ViewObject"):
            bearing_outer_obj.ViewObject.ShapeColor = (0.1, 0.7, 0.7)  # Teal
            bearing_outer_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("output_bearing_outer_front", bearing_outer_obj))  # Fixed key name
        print(f"Debug: Created output front bearing outer: {bearing_outer_obj.Name}")
        
        bearing_inner = Part.makeCylinder(bearing_inner_diameter/2, bearing_width)
        bearing_inner.rotate(Base.Vector(0, 0, 0), Base.Vector(1, 0, 0), 90)  # Rotate to align with shaft
        bearing_inner.translate(Base.Vector(center_distance, -housing_depth/2 + wall_thickness, output_shaft_z_pos + output_shaft_length/4))
        bearing_inner_obj = doc.addObject("Part::Feature", "OutputBearing_Inner_Front")
        bearing_inner_obj.Shape = bearing_inner
        if hasattr(bearing_inner_obj, "ViewObject"):
            bearing_inner_obj.ViewObject.ShapeColor = (0.9, 0.9, 0.9)  # White
            bearing_inner_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("output_bearing_inner_front", bearing_inner_obj))  # Fixed key name
        print(f"Debug: Created output front bearing inner: {bearing_inner_obj.Name}")
        
        # Back bearing for output shaft
        bearing_outer = Part.makeCylinder(bearing_outer_diameter/2, bearing_width)
        bearing_outer.rotate(Base.Vector(0, 0, 0), Base.Vector(1, 0, 0), 90)  # Rotate to align with shaft
        bearing_outer.translate(Base.Vector(center_distance, housing_depth/2 - wall_thickness - bearing_width, output_shaft_z_pos + output_shaft_length/4))
        bearing_outer_obj = doc.addObject("Part::Feature", "OutputBearing_Outer_Back")
        bearing_outer_obj.Shape = bearing_outer
        if hasattr(bearing_outer_obj, "ViewObject"):
            bearing_outer_obj.ViewObject.ShapeColor = (0.1, 0.7, 0.7)  # Teal
            bearing_outer_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("output_bearing_outer_back", bearing_outer_obj))  # Fixed key name
        print(f"Debug: Created output back bearing outer: {bearing_outer_obj.Name}")
        
        bearing_inner = Part.makeCylinder(bearing_inner_diameter/2, bearing_width)
        bearing_inner.rotate(Base.Vector(0, 0, 0), Base.Vector(1, 0, 0), 90)  # Rotate to align with shaft
        bearing_inner.translate(Base.Vector(center_distance, housing_depth/2 - wall_thickness - bearing_width, output_shaft_z_pos + output_shaft_length/4))
        bearing_inner_obj = doc.addObject("Part::Feature", "OutputBearing_Inner_Back")
        bearing_inner_obj.Shape = bearing_inner
        if hasattr(bearing_inner_obj, "ViewObject"):
            bearing_inner_obj.ViewObject.ShapeColor = (0.9, 0.9, 0.9)  # White
            bearing_inner_obj.ViewObject.Transparency = 0  # Fully opaque
        components.append(("output_bearing_inner_back", bearing_inner_obj))  # Fixed key name
        print(f"Debug: Created output back bearing inner: {bearing_inner_obj.Name}")
        
        # Create housing cover - make it more visible
        cover = Part.makeBox(housing_width, housing_depth, wall_thickness)
        cover.translate(Base.Vector(-30, -housing_depth/2, housing_height + wall_height))
        cover_obj = doc.addObject("Part::Feature", "Housing_Cover")
        cover_obj.Shape = cover
        if hasattr(cover_obj, "ViewObject"):
            cover_obj.ViewObject.ShapeColor = (0.2, 0.2, 0.8)  # Blue
            cover_obj.ViewObject.Transparency = 70  # Semi-transparent to see inside
        components.append(("housing_cover", cover_obj))
        print(f"Debug: Created housing cover: {cover_obj.Name}")
        
        # Recompute document and ensure all objects are shown
        print("Debug: Recomputing document to update all objects")
        doc.recompute()
        
        # Print summary of created components
        print(f"\nCreated {len(components)} gearbox components:")
        for component_type, obj in components:
            print(f"  - {component_type}: {obj.Name}")
        print("")
        
        # Set up view if GUI is available
        try:
            import FreeCADGui
            print(f"Debug: Setting up view for {len(doc.Objects)} objects")
            
            # First ensure all objects are visible
            for obj in doc.Objects:
                if hasattr(obj, "ViewObject"):
                    obj.ViewObject.Visibility = True
                    print(f"Debug: Made {obj.Name} visible")
            
            # Set display mode for all objects
            for obj in doc.Objects:
                if hasattr(obj, "ViewObject"):
                    try:
                        obj.ViewObject.DisplayMode = "Shaded"
                    except Exception as e:
                        print(f"Error setting display mode for {obj.Name}: {str(e)}")
            
            # Set the view direction to isometric for better visibility
            try:
                # First set to isometric view
                FreeCADGui.activeDocument().activeView().viewIsometric()
                print("Debug: Set view to isometric")
                
                # Then rotate to show the gear ratio clearly
                cam = FreeCADGui.activeDocument().activeView().getCameraNode()
                cam.orientation.setValue(0.342, 0.342, -0.248, 0.841)  # Adjusted orientation for better view
                print("Debug: Adjusted camera orientation for optimal view")
                
                # Add a text annotation showing the gear ratio
                try:
                    import Draft
                    ratio_text = Draft.makeText([f"Gear Ratio: {output_teeth}/{input_teeth} = {output_teeth/input_teeth:.1f}:1"], placement=FreeCAD.Placement(FreeCAD.Vector(0, -housing_depth/2 - 20, housing_height), FreeCAD.Rotation()))
                    ratio_text.ViewObject.FontSize = 14
                    ratio_text.ViewObject.TextColor = (1.0, 0.0, 0.0)  # Red color
                    print("Debug: Added gear ratio text annotation")
                except Exception as e:
                    print(f"Error adding text annotation: {str(e)}")
                
                # Fit view to show all objects
                print("Debug: Fitting view to show all objects")
                FreeCADGui.SendMsgToActiveView("ViewFit")
                FreeCADGui.updateGui()
                
                # Force another update after a short delay
                time.sleep(0.5)
                FreeCADGui.updateGui()
            except Exception as e:
                print(f"Error setting view orientation: {str(e)}")
            
            # Print summary of created objects
            print("\n==== GEARBOX CREATION SUMMARY ====\n")
            print(f"Created {len(doc.Objects)} objects in document {doc.Name}")
            print(f"Gearbox ratio: {ratio}:1 ({output_teeth}/{input_teeth} teeth)")
            print(f"Motor type: {motor_type}")
            print("================================\n")
            
            print("Debug: View setup completed")
        except Exception as e:
            print(f"Error in GUI setup: {str(e)}")
            print("FreeCADGui not available or error in view setup")
        
        return {
            'success': True,
            'message': f'Created gearbox with {ratio}:1 ratio for {motor_type}',
            'document': doc,
            'components': components,
            'specs': {
                'ratio': ratio,
                'motor_type': motor_type,
                'input_teeth': input_teeth,
                'output_teeth': output_teeth
            }
        }
        
    except Exception as e:
        import traceback
        print(f"Error creating gearbox: {str(e)}")
        traceback.print_exc()
        return {
            'success': False,
            'message': f'Error creating gearbox: {str(e)}'
        }

def extract_ratio(description):
    """Extract ratio from description"""
    # Look for patterns like "10:1" or "ratio 10" or "ratio of 10"
    ratio_match = re.search(r'(\d+(?:\.\d+)?)\s*:\s*1', description)
    if ratio_match:
        return float(ratio_match.group(1))
    
    ratio_match = re.search(r'ratio\s+(?:of\s+)?(\d+(?:\.\d+)?)', description)
    if ratio_match:
        return float(ratio_match.group(1))
    
    # Default ratio
    return 5.0

def extract_motor_type(description):
    """Extract motor type from description"""
    if 'nema17' in description.lower() or 'nema 17' in description.lower():
        return 'NEMA17'
    elif 'nema23' in description.lower() or 'nema 23' in description.lower():
        return 'NEMA23'
    elif 'nema34' in description.lower() or 'nema 34' in description.lower():
        return 'NEMA34'
    else:
        return 'NEMA17'  # Default
