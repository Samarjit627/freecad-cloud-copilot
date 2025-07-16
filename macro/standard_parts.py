"""
Standard parts library (gears, bearings, etc.)
"""

import FreeCAD
import FreeCADGui
import Part
import math
import traceback

class StandardParts:
    """Create standard mechanical parts"""
    
    def __init__(self):
        self.gear_module = 2.0
        self.pressure_angle = 20.0
        
    def create_gear(self, teeth=20, module=None, width=20, bore=10):
        """Create a gear with visible teeth using extrusions and cuts"""
        print(f"Debug: Creating gear with teeth={teeth}, module={module}, width={width}, bore={bore}")
        
        try:
            # Ensure we have an active document
            if FreeCAD.ActiveDocument is None:
                print("Debug: Creating new document for gear")
                doc = FreeCAD.newDocument("Gear")
            else:
                print("Debug: Using active document")
                doc = FreeCAD.ActiveDocument
            
            # Calculate module if not provided
            if module is None:
                module = 2.0  # Default module
            
            print(f"Debug: Using module={module}")
            
            # Calculate gear dimensions
            pitch_diameter = teeth * module
            outer_diameter = pitch_diameter + 2 * module  # Addendum
            root_diameter = pitch_diameter - 2.5 * module  # Dedendum
            
            print(f"Debug: Gear dimensions - pitch_dia={pitch_diameter}, outer_dia={outer_diameter}, root_dia={root_diameter}")
            
            # Create the base cylinder at the root diameter (not outer)
            print("Debug: Creating base cylinder at root diameter")
            base_cylinder = Part.makeCylinder(root_diameter/2, width)
            
            # Create the teeth by adding blocks around the perimeter
            print(f"Debug: Creating {teeth} teeth")
            tooth_angle = 360.0 / teeth  # Angle between teeth
            tooth_width_angle = tooth_angle * 0.4  # Width of each tooth in degrees
            
            # Create a compound shape to hold all teeth
            all_teeth = []
            
            for i in range(teeth):
                # Calculate the angle for this tooth
                angle = i * tooth_angle
                
                # Create a tooth as a box
                tooth_height = (outer_diameter - root_diameter) / 2  # Radial height of tooth
                tooth_width = root_diameter * math.sin(math.radians(tooth_width_angle))  # Arc width at root diameter
                
                # Create the tooth as a box
                tooth = Part.makeBox(tooth_height, tooth_width, width)
                
                # Position the tooth at the edge of the root cylinder
                tooth.translate(FreeCAD.Vector(root_diameter/2, -tooth_width/2, 0))
                
                # Rotate the tooth to its position
                tooth.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), angle)
                
                # Add to our collection
                all_teeth.append(tooth)
            
            # Fuse all teeth with the base cylinder
            print("Debug: Fusing teeth with base cylinder")
            gear_shape = base_cylinder
            for tooth in all_teeth:
                gear_shape = gear_shape.fuse(tooth)
            
            # Create center bore if specified
            if bore > 0:
                print(f"Debug: Creating center bore with diameter {bore}")
                center_hole = Part.makeCylinder(bore/2, width)
                gear_shape = gear_shape.cut(center_hole)
            
            # Create the final object
            print("Debug: Creating Part::Feature object")
            gear_obj = doc.addObject("Part::Feature", f"Gear_T{teeth}_M{module}")
            gear_obj.Shape = gear_shape
            
            print("Debug: Recomputing document")
            doc.recompute()
            
            result = {
                'success': True,
                'message': f'Created gear: {teeth} teeth, module {module}, \u00f8{pitch_diameter}mm pitch diameter',
                'object': gear_obj,
                'specs': {
                    'teeth': teeth,
                    'module': module,
                    'pitch_diameter': pitch_diameter,
                    'outer_diameter': outer_diameter,
                    'width': width,
                    'bore': bore
                }
            }
            print(f"Debug: Gear creation successful: {result['message']}")
            return result
            
        except Exception as e:
            print(f"Debug: Error creating gear: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f'Error creating gear: {str(e)}'}
    
    def create_bearing_block(self, bearing_type='608', mounting_holes=True):
        """Create a bearing block"""
        print(f"Debug: Creating bearing block with type={bearing_type}, mounting_holes={mounting_holes}")
        try:
            # Ensure we have an active document
            if FreeCAD.ActiveDocument is None:
                print("Debug: Creating new document for bearing block")
                doc = FreeCAD.newDocument("BearingBlock")
            else:
                print("Debug: Using active document")
                doc = FreeCAD.ActiveDocument
            
            # Determine bearing dimensions based on type
            if bearing_type == '608':
                outer_dia = 22
                inner_dia = 8
                width = 7
            elif bearing_type == '6001':
                outer_dia = 28
                inner_dia = 12
                width = 8
            elif bearing_type == '6201':
                outer_dia = 32
                inner_dia = 12
                width = 10
            else:
                # Default
                outer_dia = 22
                inner_dia = 8
                width = 7
                
            print(f"Debug: Using bearing dimensions - outer_dia={outer_dia}, inner_dia={inner_dia}, width={width}")
                
            # Create block dimensions
            block_width = width + 10
            block_height = outer_dia + 10
            block_depth = outer_dia + 10
            
            print("Debug: Creating main block")
            # Create main block
            block = Part.makeBox(block_width, block_height, block_depth)
            
            print("Debug: Creating bearing hole")
            # Create bearing hole
            bearing_hole = Part.makeCylinder(outer_dia/2, block_width)
            bearing_hole.translate(FreeCAD.Vector(0, block_height/2, block_depth/2))
            bearing_hole.rotate(FreeCAD.Vector(0, block_height/2, block_depth/2), FreeCAD.Vector(0, 1, 0), 90)
            
            # Cut bearing hole from block
            block = block.cut(bearing_hole)
            
            # Add mounting holes if requested
            if mounting_holes:
                print("Debug: Adding mounting holes")
                hole_dia = 5
                for x, z in [(block_height/4, block_depth/4), 
                             (block_height/4, 3*block_depth/4),
                             (3*block_height/4, block_depth/4),
                             (3*block_height/4, 3*block_depth/4)]:
                    mount_hole = Part.makeCylinder(hole_dia/2, block_width)
                    mount_hole.translate(FreeCAD.Vector(0, x, z))
                    mount_hole.rotate(FreeCAD.Vector(0, x, z), FreeCAD.Vector(0, 1, 0), 90)
                    block = block.cut(mount_hole)
            
            print("Debug: Creating Part::Feature object")
            # Create the final object
            bearing_block = doc.addObject("Part::Feature", f"BearingBlock_{bearing_type}")
            bearing_block.Shape = block
            
            print("Debug: Recomputing document")
            doc.recompute()
            
            result = {
                'success': True,
                'message': f'Created bearing block for {bearing_type} bearing',
                'object': bearing_block,
                'specs': {
                    'bearing_type': bearing_type,
                    'outer_diameter': outer_dia,
                    'inner_diameter': inner_dia,
                    'width': width,
                    'mounting_holes': mounting_holes
                }
            }
            print(f"Debug: Bearing block creation successful: {result['message']}")
            return result
            
        except Exception as e:
            print(f"Debug: Error creating bearing block: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f'Error creating bearing block: {str(e)}'}
    
    def create_shaft(self, diameter=10, length=100, keyway=False):
        """Create a shaft"""
        print(f"Debug: Creating shaft with diameter={diameter}, length={length}, keyway={keyway}")
        
        try:
            # Ensure we have an active document
            if FreeCAD.ActiveDocument is None:
                print("Debug: Creating new document for shaft")
                doc = FreeCAD.newDocument("Shaft")
            else:
                print("Debug: Using active document")
                doc = FreeCAD.ActiveDocument
            
            print("Debug: Creating basic shaft cylinder")
            # Create basic shaft
            shaft = Part.makeCylinder(diameter/2, length)
            
            # Add keyway if requested
            if keyway:
                print("Debug: Adding keyway to shaft")
                keyway_width = diameter * 0.25
                keyway_depth = diameter * 0.125
                keyway_length = length * 0.8
                
                # Create keyway cutout
                keyway_box = Part.makeBox(keyway_width, keyway_depth, keyway_length)
                keyway_box.translate(FreeCAD.Vector(-keyway_width/2, diameter/2 - keyway_depth, length * 0.1))
                
                # Cut keyway from shaft
                shaft = shaft.cut(keyway_box)
            
            print("Debug: Creating Part::Feature object")
            # Create the final object
            shaft_obj = doc.addObject("Part::Feature", f"Shaft_D{diameter}_L{length}")
            shaft_obj.Shape = shaft
            
            print("Debug: Recomputing document")
            doc.recompute()
            
            result = {
                'success': True,
                'message': f'Created shaft: ⌀{diameter}mm x {length}mm' + (' with keyway' if keyway else ''),
                'object': shaft_obj,
                'specs': {
                    'diameter': diameter,
                    'length': length,
                    'keyway': keyway
                }
            }
            print(f"Debug: Shaft creation successful: {result['message']}")
            return result
            
        except Exception as e:
            print(f"Debug: Error creating shaft: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f'Error creating shaft: {str(e)}'}
