import FreeCAD as App
import Part
import math
import re

class AlloyWheelGenerator:
    def __init__(self):
        self.doc = App.ActiveDocument
        if not self.doc:
            self.doc = App.newDocument("AlloyWheel")
    
    def parse_wheel_command(self, command):
        params = {}
        size_match = re.search(r'(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)', command)
        if size_match:
            params['diameter'] = float(size_match.group(1)) * 25.4
            params['width'] = float(size_match.group(2)) * 25.4
        bolt_match = re.search(r'(\d+)x(\d+(?:\.\d+)?)', command)
        if bolt_match:
            params['bolt_count'] = int(bolt_match.group(1))
            params['bolt_circle'] = float(bolt_match.group(2))
        bore_match = re.search(r'center bore (\d+(?:\.\d+)?)', command, re.IGNORECASE)
        if bore_match:
            params['center_bore'] = float(bore_match.group(1))
        offset_match = re.search(r'offset (\d+(?:\.\d+)?)', command, re.IGNORECASE)
        if offset_match:
            params['offset'] = float(offset_match.group(1))
        spoke_match = re.search(r'(\d+)-spoke', command, re.IGNORECASE)
        if spoke_match:
            params['spoke_count'] = int(spoke_match.group(1))
        if 'y-style' in command.lower():
            params['spoke_style'] = 'y_spoke'
        elif 'split' in command.lower():
            params['spoke_style'] = 'split_spoke'
        elif 'twisted' in command.lower():
            params['spoke_style'] = 'twisted'
        else:
            params['spoke_style'] = 'straight'
        return params
    
    def create_wheel_rim(self, diameter, width, offset):
        """Create a more realistic rim cross-section: barrel + bead seats + front lip."""
        outer_radius = diameter / 2
        wall = 8.0
        bead_seat = 12.0
        drop_depth = 10.0
        inner_radius = max(outer_radius - wall - bead_seat, 1)

        # Base barrel (drop center)
        barrel_outer = Part.makeCylinder(outer_radius, width)
        barrel_inner = Part.makeCylinder(inner_radius, width)
        rim = barrel_outer.cut(barrel_inner)

        # Bead seats near both edges
        seat_r = inner_radius + bead_seat
        seat_h = 10.0
        front_seat = Part.makeCylinder(seat_r, seat_h)
        rear_seat = Part.makeCylinder(seat_r, seat_h)
        rear_seat.Placement.Base = App.Vector(0, 0, width - seat_h)
        rim = rim.fuse(front_seat).fuse(rear_seat)

        # Front lip slightly smaller than OD
        lip_height = 8.0
        lip_radius = max(outer_radius - 3.0, 1)
        lip = Part.makeCylinder(lip_radius, lip_height)
        lip.Placement.Base = App.Vector(0, 0, width - lip_height)
        rim = rim.fuse(lip)

        return rim
    
    def create_center_hub(self, center_bore, bolt_count, bolt_circle, width, offset):
        hub_radius = (bolt_circle / 2) + 20
        hub_thickness = max(width * 0.5, 5)
        hub = Part.makeCylinder(hub_radius, hub_thickness)
        center_hole = Part.makeCylinder(center_bore / 2, hub_thickness)
        hub = hub.cut(center_hole)
        bolt_hole_radius = 6.5
        for i in range(int(bolt_count)):
            angle = (2 * math.pi * i) / int(bolt_count)
            x = (bolt_circle / 2) * math.cos(angle)
            y = (bolt_circle / 2) * math.sin(angle)
            bolt_hole = Part.makeCylinder(bolt_hole_radius, hub_thickness)
            bolt_hole.Placement.Base = App.Vector(x, y, 0)
            hub = hub.cut(bolt_hole)
            # Add a shallow 90° countersink (approx) on front face
            try:
                cs_h = 3.0
                cs_r = bolt_hole_radius * 1.6
                cs = Part.makeCone(cs_r, bolt_hole_radius, cs_h)
                cs.Placement.Base = App.Vector(x, y, hub_thickness - cs_h)
                hub = hub.cut(cs)
            except Exception:
                pass
        hub.translate(App.Vector(0, 0, offset))
        return hub
    
    def create_y_spokes(self, spoke_count, rim_radius, hub_radius, width, offset):
        spokes = []
        spoke_thickness = min(max(10, width - 6), width)
        for i in range(int(spoke_count)):
            angle_deg = (360.0 * i) / int(spoke_count)
            # Extend to slightly overlap the inner rim for a robust fuse
            spoke_length = max(rim_radius - hub_radius - 2 + 4, 12)
            root_w = 24.0
            tip_w = root_w * 1.4
            main_arm = Part.makeBox(spoke_length, root_w, spoke_thickness)
            main_arm.Placement.Base = App.Vector(hub_radius + 5, -root_w/2, offset + width/2 - spoke_thickness/2)
            # Add a wider tip segment to simulate Y split merge
            tip = Part.makeBox(max(spoke_length * 0.35, 10), tip_w, spoke_thickness)
            tip.Placement.Base = App.Vector(hub_radius + 5 + spoke_length - max(spoke_length * 0.35, 10), -tip_w/2, offset + width/2 - spoke_thickness/2)
            # Branches for Y aesthetic
            branch_length = spoke_length * 0.28
            branch_angle = 25
            left_branch = Part.makeBox(branch_length, root_w * 0.7, spoke_thickness)
            left_branch.rotate(App.Vector(0,0,0), App.Vector(0,0,1), branch_angle)
            left_branch.Placement.Base = App.Vector(hub_radius + spoke_length * 0.5, -root_w/3, offset + width/2 - spoke_thickness/2)
            right_branch = Part.makeBox(branch_length, root_w * 0.7, spoke_thickness)
            right_branch.rotate(App.Vector(0,0,0), App.Vector(0,0,1), -branch_angle)
            right_branch.Placement.Base = App.Vector(hub_radius + spoke_length * 0.5, -root_w/3, offset + width/2 - spoke_thickness/2)
            y_spoke = main_arm.fuse(tip).fuse(left_branch).fuse(right_branch)
            y_spoke.rotate(App.Vector(0,0,0), App.Vector(0,0,1), angle_deg)
            spokes.append(y_spoke)
        return spokes
    
    def create_straight_spokes(self, spoke_count, rim_radius, hub_radius, width, offset):
        spokes = []
        spoke_thickness = min(max(12, width - 6), width)
        root_w = 22
        for i in range(int(spoke_count)):
            angle_deg = (360.0 * i) / int(spoke_count)
            spoke_length = max(rim_radius - hub_radius - 2 + 4, 12)
            tip_w = root_w * 1.3
            spoke = Part.makeBox(spoke_length, root_w, spoke_thickness)
            spoke.Placement.Base = App.Vector(hub_radius + 5, -root_w/2, offset + width/2 - spoke_thickness/2)
            tip = Part.makeBox(max(spoke_length * 0.3, 8), tip_w, spoke_thickness)
            tip.Placement.Base = App.Vector(hub_radius + 5 + spoke_length - max(spoke_length * 0.3, 8), -tip_w/2, offset + width/2 - spoke_thickness/2)
            spoke = spoke.fuse(tip)
            spoke.rotate(App.Vector(0,0,0), App.Vector(0,0,1), angle_deg)
            spokes.append(spoke)
        return spokes
    
    def create_split_spokes(self, spoke_count, rim_radius, hub_radius, width, offset):
        spokes = []
        spoke_thickness = min( max(8, width - 6), width )
        spoke_width = 15
        split_gap = 5
        for i in range(int(spoke_count)):
            angle_deg = (360.0 * i) / int(spoke_count)
            spoke_length = max(rim_radius - hub_radius - 10, 10)
            spoke1 = Part.makeBox(spoke_length, spoke_width, spoke_thickness)
            spoke1.Placement.Base = App.Vector(hub_radius + 5, split_gap/2, offset + width/2 - spoke_thickness/2)
            spoke2 = Part.makeBox(spoke_length, spoke_width, spoke_thickness)
            spoke2.Placement.Base = App.Vector(hub_radius + 5, -split_gap/2 - spoke_width, offset + width/2 - spoke_thickness/2)
            twin_spoke = spoke1.fuse(spoke2)
            twin_spoke.rotate(App.Vector(0,0,0), App.Vector(0,0,1), angle_deg)
            spokes.append(twin_spoke)
        return spokes
    
    def add_wheel_details(self, wheel):
        valve_hole = Part.makeCylinder(4, 50)
        valve_angle = math.pi / 4
        valve_radius = max(wheel.BoundBox.XMax * 0.7, 1)
        valve_x = valve_radius * math.cos(valve_angle)
        valve_y = valve_radius * math.sin(valve_angle)
        valve_hole.Placement.Base = App.Vector(valve_x, valve_y, -10)
        wheel = wheel.cut(valve_hole)
        # Light fillet for nicer look (best-effort)
        try:
            wheel = wheel.makeFillet(1.0, [e for e in wheel.Edges])
        except Exception:
            pass
        return wheel
    
    def generate_wheel(self, command):
        params = self.parse_wheel_command(command)
        diameter = params.get('diameter', 17 * 25.4)
        width = params.get('width', 7 * 25.4)
        bolt_count = params.get('bolt_count', 5)
        bolt_circle = params.get('bolt_circle', 114.3)
        center_bore = params.get('center_bore', 66.6)
        offset = params.get('offset', 35)
        spoke_count = params.get('spoke_count', 10)
        spoke_style = params.get('spoke_style', 'straight')
        rim = self.create_wheel_rim(diameter, width, offset)
        hub = self.create_center_hub(center_bore, bolt_count, bolt_circle, width, offset)
        rim_radius = diameter / 2 - 15
        hub_radius = (bolt_circle / 2) + 20
        if spoke_style == 'y_spoke':
            spokes = self.create_y_spokes(spoke_count, rim_radius, hub_radius, width, offset)
        elif spoke_style == 'split_spoke':
            spokes = self.create_split_spokes(spoke_count, rim_radius, hub_radius, width, offset)
        else:
            spokes = self.create_straight_spokes(spoke_count, rim_radius, hub_radius, width, offset)
        wheel = rim.fuse(hub)
        for s in spokes:
            wheel = wheel.fuse(s)
        wheel = self.add_wheel_details(wheel)
        obj = self.doc.addObject("Part::Feature", "AlloyWheel")
        obj.Shape = wheel
        try:
            obj.ViewObject.ShapeColor = (0.8, 0.8, 0.9)
        except Exception:
            pass
        self.doc.recompute()
        return obj


def create_wheel_from_command(command: str):
    gen = AlloyWheelGenerator()
    return gen.generate_wheel(command)
