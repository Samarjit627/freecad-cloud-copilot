import FreeCAD as App
import Part
import math

# Create a new document
doc = App.newDocument("WaterBottle")

# Define bottle parameters
volume = 750  # ml
wall_thickness = 2  # mm
neck_diameter = 28  # mm
neck_height = 20  # mm
cap_height = 15  # mm
thread_height = 15  # mm
transition_height = 20  # mm

# Calculate body dimensions to achieve desired volume
body_diameter = 80  # mm
# Account for the transition section and neck in volume calculation
transition_volume = (math.pi * transition_height / 3) * ((body_diameter/2)**2 + (body_diameter/2)*(neck_diameter/2) + (neck_diameter/2)**2)
neck_volume = math.pi * (neck_diameter/2 - wall_thickness)**2 * neck_height

# Calculate body height needed for remaining volume
remaining_volume = volume * 1000 - transition_volume - neck_volume
body_inner_radius = body_diameter/2 - wall_thickness
body_height = remaining_volume / (math.pi * body_inner_radius**2) + wall_thickness

# Create bottle body with proper wall thickness
body_outer = Part.makeCylinder(body_diameter/2, body_height)
body_inner = Part.makeCylinder(body_diameter/2 - wall_thickness, body_height - wall_thickness)
body_inner.translate(App.Vector(0, 0, wall_thickness))
body = body_outer.cut(body_inner)

# Create bottle neck
neck_outer = Part.makeCylinder(neck_diameter/2, neck_height)
neck_inner = Part.makeCylinder(neck_diameter/2 - wall_thickness, neck_height)
neck = neck_outer.cut(neck_inner)
neck.translate(App.Vector(0, 0, body_height))

# Create transition between body and neck
transition = Part.makeCone(body_diameter/2, neck_diameter/2, transition_height)
transition_hollow = Part.makeCone(body_diameter/2 - wall_thickness, neck_diameter/2 - wall_thickness, transition_height)
transition = transition.cut(transition_hollow)
transition.translate(App.Vector(0, 0, body_height - transition_height))

# Create cap
cap = Part.makeCylinder(neck_diameter/2 + 2, cap_height)
cap.translate(App.Vector(0, 0, body_height + neck_height))

# Create a simplified thread ring instead of individual thread elements
thread_height = 10  # mm
thread_outer_dia = neck_diameter + 1  # mm
thread_inner_dia = neck_diameter  # mm

# Create a single thread ring around the neck
thread_ring_outer = Part.makeCylinder(thread_outer_dia/2, thread_height)
thread_ring_inner = Part.makeCylinder(thread_inner_dia/2, thread_height)
thread_ring = thread_ring_outer.cut(thread_ring_inner)
thread_ring.translate(App.Vector(0, 0, body_height + 5))  # Position in middle of neck

# Combine all parts
bottle = body.fuse(neck).fuse(transition).fuse(thread_ring)

# Create FreeCAD objects
bottle_obj = doc.addObject("Part::Feature", "Bottle")
bottle_obj.Shape = bottle
cap_obj = doc.addObject("Part::Feature", "Cap")
cap_obj.Shape = cap

# Calculate actual volume
body_volume = body_inner.Volume / 1000  # Convert mm^3 to ml
transition_inner_volume = transition_hollow.Volume / 1000  # Convert mm^3 to ml
neck_inner_volume = neck_inner.Volume / 1000  # Convert mm^3 to ml
actual_volume = body_volume + transition_inner_volume + neck_inner_volume
print(f"Actual volume: {actual_volume:.2f} ml")
print(f"  - Body volume: {body_volume:.2f} ml")
print(f"  - Transition volume: {transition_inner_volume:.2f} ml")
print(f"  - Neck volume: {neck_inner_volume:.2f} ml")

# Ensure view is updated
doc.recompute()

# If GUI is available, update the view
try:
    import FreeCADGui
    FreeCADGui.ActiveDocument.ActiveView.fitAll()
    FreeCADGui.updateGui()
    print("3D view updated")
except:
    print("Running in console mode, no GUI updates")
