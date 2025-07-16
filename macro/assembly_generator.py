"""
Assembly generation from text descriptions
"""

import FreeCAD
import FreeCADGui
import Part
import re
from FreeCAD import Vector, Placement, Rotation
import math

class AssemblyGenerator:
    """Generate assemblies from descriptions"""
    
    def __init__(self, standard_parts=None):
        self.standard_parts = standard_parts
        self.assembly_doc = None
        self.components = []
        
    def create_assembly(self, description):
        """Create assembly from text description"""
        # Parse assembly type
        assembly_type = self.identify_assembly_type(description)
        
        if assembly_type == 'gearbox':
            return self.create_gearbox(description)
        elif assembly_type == 'linear_actuator':
            return self.create_linear_actuator(description)
        elif assembly_type == 'motor_mount':
            return self.create_motor_mount(description)
        else:
            return self.create_generic_assembly(description)
    
    def identify_assembly_type(self, description):
        """Identify what type of assembly to create"""
        desc_lower = description.lower()
        
        if 'gearbox' in desc_lower or 'reduction' in desc_lower:
            return 'gearbox'
        elif 'linear' in desc_lower or 'actuator' in desc_lower:
            return 'linear_actuator'
        elif 'motor mount' in desc_lower:
            return 'motor_mount'
        else:
            return 'generic'
    
    def create_gearbox(self, description):
        """Create a gearbox assembly"""
        # Create new document for assembly
        self.assembly_doc = FreeCAD.newDocument("Gearbox_Assembly")
        
        try:
            # Parse parameters
            ratio = self.extract_ratio(description)
            motor_type = self.extract_motor_type(description)
            
            print(f"Debug: Creating gearbox with ratio {ratio} and motor type {motor_type}")
            
            # Create housing
            housing = self.create_gearbox_housing(motor_type)
            self.components.append(('housing', housing))
            
            # Create gears with appropriate teeth for the ratio
            # For better visualization, keep input gear reasonable size
            gear1_teeth = 20  # Input gear teeth
            gear2_teeth = int(gear1_teeth * ratio)
            
            print(f"Debug: Creating gears with teeth: input={gear1_teeth}, output={gear2_teeth}")
            
            # Input gear
            input_gear = self.create_gear_component(gear1_teeth, 2.0, 15)
            input_gear.Placement = Placement(Vector(0, 0, 20), Rotation())
            self.components.append(('input_gear', input_gear))
            
            # Output gear
            output_gear = self.create_gear_component(gear2_teeth, 2.0, 15)
            # Calculate center distance based on gear teeth
            center_distance = (gear1_teeth + gear2_teeth) * 2.0 / 2
            output_gear.Placement = Placement(Vector(center_distance, 0, 20), Rotation())
            self.components.append(('output_gear', output_gear))
            
            # Create shafts
            input_shaft = self.create_shaft_component(8, 60)
            input_shaft.Placement = Placement(Vector(0, 0, -10), Rotation())
            self.components.append(('input_shaft', input_shaft))
            
            output_shaft = self.create_shaft_component(10, 60)
            output_shaft.Placement = Placement(Vector(center_distance, 0, -10), Rotation())
            self.components.append(('output_shaft', output_shaft))
            
            # Add bearings
            for pos in [(0, -5), (0, 45), (center_distance, -5), (center_distance, 45)]:
                bearing = self.create_bearing_component('608')
                bearing.Placement = Placement(Vector(pos[0], 0, pos[1]), 
                                            Rotation(Vector(1, 0, 0), 90))
                self.components.append(('bearing', bearing))
            
            self.assembly_doc.recompute()
            
            return {
                'success': True,
                'message': f'Created gearbox assembly with {ratio}:1 reduction',
                'document': self.assembly_doc,
                'components': len(self.components),
                'specs': {
                    'ratio': ratio,
                    'center_distance': center_distance,
                    'input_teeth': gear1_teeth,
                    'output_teeth': gear2_teeth
                }
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error creating gearbox: {str(e)}'}
    
    def create_motor_mount(self, description):
        """Create a motor mount assembly"""
        self.assembly_doc = FreeCAD.newDocument("MotorMount_Assembly")
        
        try:
            # Identify motor type
            motor_type = 'NEMA17'  # Default
            if 'nema23' in description.lower():
                motor_type = 'NEMA23'
            elif 'nema34' in description.lower():
                motor_type = 'NEMA34'
            
            # Motor specifications
            motor_specs = {
                'NEMA17': {'size': 42.3, 'hole_spacing': 31, 'shaft': 5},
                'NEMA23': {'size': 57, 'hole_spacing': 47.14, 'shaft': 6.35},
                'NEMA34': {'size': 86, 'hole_spacing': 69.6, 'shaft': 14}
            }
            
            spec = motor_specs[motor_type]
            
            # Create mount plate
            plate = self.create_mount_plate(spec['size'], spec['hole_spacing'])
            self.components.append(('mount_plate', plate))
            
            # Add motor representation
            motor = self.create_motor_representation(motor_type, spec)
            motor.Placement = Placement(Vector(0, 0, 10), Rotation())
            self.components.append(('motor', motor))
            
            # Add standoffs if mentioned
            if 'standoff' in description.lower() or 'raised' in description.lower():
                for x, y in [(15, 15), (-15, 15), (15, -15), (-15, -15)]:
                    standoff = self.create_standoff(20)
                    standoff.Placement = Placement(Vector(x, y, -20), Rotation())
                    self.components.append(('standoff', standoff))
            
            self.assembly_doc.recompute()
            
            return {
                'success': True,
                'message': f'Created motor mount for {motor_type}',
                'document': self.assembly_doc,
                'components': len(self.components)
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error creating motor mount: {str(e)}'}
    
    def create_linear_actuator(self, description):
        """Create a linear actuator assembly"""
        self.assembly_doc = FreeCAD.newDocument("LinearActuator_Assembly")
        
        try:
            # Determine stroke length
            stroke = 100  # Default
            numbers = re.findall(r'\d+', description)
            if numbers:
                stroke = float(numbers[0])
            
            # Create base
            base = Part.makeBox(60, 40, 20)
            base.translate(Vector(-30, -20, 0))
            base_obj = self.assembly_doc.addObject("Part::Feature", "Base")
            base_obj.Shape = base
            self.components.append(('base', base_obj))
            
            # Create guide rails
            for x in [-20, 20]:
                rail = Part.makeCylinder(4, stroke + 40)
                rail.translate(Vector(x, 0, 20))
                rail_obj = self.assembly_doc.addObject("Part::Feature", "GuideRail")
                rail_obj.Shape = rail
                self.components.append(('guide_rail', rail_obj))
            
            # Create carriage
            carriage = Part.makeBox(50, 30, 15)
            carriage.translate(Vector(-25, -15, 25))
            # Add holes for rails
            for x in [-20, 20]:
                hole = Part.makeCylinder(4.5, 15)
                hole.translate(Vector(x, 0, 25))
                carriage = carriage.cut(hole)
            
            carriage_obj = self.assembly_doc.addObject("Part::Feature", "Carriage")
            carriage_obj.Shape = carriage
            self.components.append(('carriage', carriage_obj))
            
            # Create lead screw
            lead_screw = Part.makeCylinder(4, stroke + 20)
            lead_screw.translate(Vector(0, 0, 10))
            screw_obj = self.assembly_doc.addObject("Part::Feature", "LeadScrew")
            screw_obj.Shape = lead_screw
            self.components.append(('lead_screw', screw_obj))
            
            self.assembly_doc.recompute()
            
            return {
                'success': True,
                'message': f'Created linear actuator with {stroke}mm stroke',
                'document': self.assembly_doc,
                'components': len(self.components)
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error creating linear actuator: {str(e)}'}
    
    def create_generic_assembly(self, description):
        """Create a generic assembly based on description"""
        self.assembly_doc = FreeCAD.newDocument("Generic_Assembly")
        
        try:
            # Create a simple base plate
            base = Part.makeBox(100, 100, 10)
            base.translate(Vector(-50, -50, 0))
            base_obj = self.assembly_doc.addObject("Part::Feature", "BasePlate")
            base_obj.Shape = base
            self.components.append(('base_plate', base_obj))
            
            # Add a simple component on top
            component = Part.makeBox(40, 40, 30)
            component.translate(Vector(-20, -20, 10))
            comp_obj = self.assembly_doc.addObject("Part::Feature", "Component")
            comp_obj.Shape = component
            self.components.append(('component', comp_obj))
            
            self.assembly_doc.recompute()
            
            return {
                'success': True,
                'message': 'Created generic assembly',
                'document': self.assembly_doc,
                'components': len(self.components)
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error creating generic assembly: {str(e)}'}
    
    # Helper methods
    def create_gearbox_housing(self, motor_type):
        """Create gearbox housing"""
        # Create main body
        housing = Part.makeBox(100, 60, 50)
        housing.translate(Vector(-30, -30, 0))
        
        # Hollow it out
        shell = Part.makeBox(94, 54, 47)
        shell.translate(Vector(-27, -27, 3))
        housing = housing.cut(shell)
        
        # Add shaft holes
        for x in [0, 40]:
            hole = Part.makeCylinder(12, 60)
            hole.translate(Vector(x, -30, 25))
            hole.rotate(Vector(0, 0, 0), Vector(1, 0, 0), 90)
            housing = housing.cut(hole)
        
        housing_obj = self.assembly_doc.addObject("Part::Feature", "Housing")
        housing_obj.Shape = housing
        return housing_obj
    
    def create_gear_component(self, teeth, module, width):
        """Create gear for assembly"""
        pitch_dia = teeth * module
        outer_dia = pitch_dia + 2 * module
        
        gear = Part.makeCylinder(outer_dia/2, width)
        # Add center hole
        hole = Part.makeCylinder(4, width)
        gear = gear.cut(hole)
        
        gear_obj = self.assembly_doc.addObject("Part::Feature", f"Gear_T{teeth}")
        gear_obj.Shape = gear
        return gear_obj
    
    def create_shaft_component(self, diameter, length):
        """Create shaft for assembly"""
        shaft = Part.makeCylinder(diameter/2, length)
        shaft_obj = self.assembly_doc.addObject("Part::Feature", f"Shaft_D{diameter}")
        shaft_obj.Shape = shaft
        return shaft_obj
    
    def create_bearing_component(self, bearing_type):
        """Create bearing for assembly"""
        # Simplified bearing representation
        bearing = Part.makeCylinder(11, 7)  # 608 bearing
        inner = Part.makeCylinder(4, 7)
        bearing = bearing.cut(inner)
        
        bearing_obj = self.assembly_doc.addObject("Part::Feature", "Bearing")
        bearing_obj.Shape = bearing
        return bearing_obj
    
    def create_mount_plate(self, motor_size, hole_spacing):
        """Create motor mount plate"""
        # Plate size
        plate_size = motor_size + 20
        plate = Part.makeBox(plate_size, plate_size, 5)
        plate.translate(Vector(-plate_size/2, -plate_size/2, 0))
        
        # Center hole for shaft
        center_hole = Part.makeCylinder(12, 5)
        plate = plate.cut(center_hole)
        
        # Mounting holes
        hole_offset = hole_spacing / 2
        for x, y in [(hole_offset, hole_offset), (-hole_offset, hole_offset),
                     (hole_offset, -hole_offset), (-hole_offset, -hole_offset)]:
            hole = Part.makeCylinder(1.5, 5)
            hole.translate(Vector(x, y, 0))
            plate = plate.cut(hole)
        
        plate_obj = self.assembly_doc.addObject("Part::Feature", "MountPlate")
        plate_obj.Shape = plate
        return plate_obj
    
    def create_motor_representation(self, motor_type, spec):
        """Create simplified motor model"""
        # Motor body
        motor = Part.makeBox(spec['size'], spec['size'], 40)
        motor.translate(Vector(-spec['size']/2, -spec['size']/2, 0))
        
        # Shaft
        shaft = Part.makeCylinder(spec['shaft']/2, 20)
        shaft.translate(Vector(0, 0, 40))
        motor = motor.fuse(shaft)
        
        motor_obj = self.assembly_doc.addObject("Part::Feature", motor_type)
        motor_obj.Shape = motor
        return motor_obj
    
    def create_standoff(self, height):
        """Create standoff/spacer"""
        standoff = Part.makeCylinder(5, height)
        hole = Part.makeCylinder(1.5, height)
        standoff = standoff.cut(hole)
        
        standoff_obj = self.assembly_doc.addObject("Part::Feature", "Standoff")
        standoff_obj.Shape = standoff
        return standoff_obj
    
    def extract_ratio(self, description):
        """Extract gear ratio from description"""
        import re
        
        # Debug
        print(f"Debug: Extracting ratio from: {description}")
        
        # Look for patterns like "3:1", "3 to 1", "3.5:1", etc.
        ratio_patterns = [
            r'(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)',  # 3:1, 3.5:1
            r'(\d+(?:\.\d+)?)\s*to\s*(\d+(?:\.\d+)?)',  # 3 to 1, 3.5 to 1
            r'(\d+(?:\.\d+)?)\s*[:-]\s*1',  # 3:1, 3-1
            r'ratio\s*(?:of|is|=|:)\s*(\d+(?:\.\d+)?)'  # ratio of 3, ratio: 3
        ]
        
        for pattern in ratio_patterns:
            ratio_match = re.search(pattern, description.lower())
            if ratio_match:
                if len(ratio_match.groups()) == 2:
                    # Format like "3:1" or "3 to 1"
                    input_value = float(ratio_match.group(1))
                    output_value = float(ratio_match.group(2))
                    ratio = input_value / output_value
                    print(f"Debug: Found ratio {input_value}:{output_value} = {ratio}")
                    return ratio
                else:
                    # Format like "ratio of 3"
                    ratio = float(ratio_match.group(1))
                    print(f"Debug: Found ratio {ratio}:1")
                    return ratio
        
        print("Debug: No ratio found, using default 3.0")
        return 3.0  # Default ratio
    
    def extract_motor_type(self, description):
        """Extract motor type from description"""
        desc_lower = description.lower()
        if 'nema' in desc_lower:
            if '23' in desc_lower:
                return 'NEMA23'
            elif '34' in desc_lower:
                return 'NEMA34'
        return 'NEMA17'  # Default
