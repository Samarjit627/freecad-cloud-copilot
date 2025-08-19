#!/usr/bin/env python3
"""
Component code generators that return FreeCAD Python code strings.
These are used as a local fallback when the Text-to-CAD server returns
trivial primitives for complex components.

All generated code follows safety rules:
- Uses only FreeCAD + Part (and Draft for array) modules
- No file/network/system access
- Works in mm and recomputes + makes objects visible
"""
from __future__ import annotations
from typing import Dict


def _val(d: Dict, k: str, default):
    return d[k] if k in d and d[k] not in (None, "") else default


def generate_alloy_wheel_code(params: Dict) -> str:
    """Generate FreeCAD code for a simple parametric alloy wheel.
    Params (mm unless noted):
    - rim_diameter_mm, rim_width_mm, center_bore_mm
    - pcd_count, pcd_dia_mm, offset_mm
    - spokes_count, spoke_style ('straight'|'y')
    """
    # Defaults
    rim_diameter = float(_val(params, 'rim_diameter_mm', 432.0))
    rim_width = float(_val(params, 'rim_width_mm', 178.0))
    center_bore = float(_val(params, 'center_bore_mm', 66.6))
    pcd_count = int(_val(params, 'pcd_count', 5))
    pcd_dia = float(_val(params, 'pcd_dia_mm', 114.3))
    offset = float(_val(params, 'offset_mm', 35.0))
    spokes_count = int(_val(params, 'spokes_count', 10))
    spoke_style = str(_val(params, 'spoke_style', 'y'))

    # Derive dimensions
    rim_radius = rim_diameter / 2.0
    barrel_outer_r = rim_radius
    barrel_inner_r = max(barrel_outer_r - 10.0, 5.0)  # 10mm wall
    barrel_len = rim_width
    hub_radius = max(center_bore / 2.0 + 8.0, 20.0)
    hat_thickness = 12.0
    # Make spokes span most of rim width so they are clearly visible
    spoke_thickness = max(8.0, barrel_len - 6.0)  # leave ~3mm clearance per side
    # Make spokes clearly visible
    spoke_width_root = max(25.0, 0.20 * barrel_outer_r)

    # PCD hole size reasonable default
    bolt_hole_d = 14.0

    # Simple Y/straight adjusts tip width
    spoke_width_tip = spoke_width_root * (1.6 if spoke_style.lower().startswith('y') else 1.2)
    # Spoke length: from hub clearance to INNER rim radius (ensure contact)
    # Ensure spokes overlap the barrel wall by a few mm so fuse is guaranteed
    spoke_len_val = max((barrel_inner_r + 8.0) - (hub_radius + 2.0), 30.0)

    code = f"""
import FreeCAD as App
import Part

# Document
_doc = App.ActiveDocument or App.newDocument("AlloyWheelDoc")
App.setActiveDocument(_doc.Name)

# Helpers
from math import pi, sin, cos

def make_barrel(outer_r, inner_r, length):
    outer = Part.makeCylinder(outer_r, length)
    inner = Part.makeCylinder(inner_r, length)
    return outer.cut(inner)

# Barrel (rim)
barrel = make_barrel({barrel_outer_r:.3f}, {barrel_inner_r:.3f}, {barrel_len:.3f})
barrel.Placement.Base.z = -{barrel_len/2.0:.3f}

# Hub/hat as short cylinder at center
hub = Part.makeCylinder({hub_radius:.3f}, {hat_thickness:.3f})
hub.Placement.Base.z = -{hat_thickness/2.0:.3f}

# Spoke prototype: oriented radially in XY (length along +X), thin along Z
spoke_len = {spoke_len_val:.3f}
spoke = Part.makeBox(spoke_len, {spoke_width_root:.3f}, {barrel_len - 4.0:.3f})
# Place so it starts just outside hub radius, centered on Y,Z
spoke.Placement.Base.x = {hub_radius + 2.0:.3f}
spoke.Placement.Base.y = -{spoke_width_root/2.0:.3f}
spoke.Placement.Base.z = -{(barrel_len - 4.0)/2.0:.3f}

# Taper tip (approximate) by cutting a wedge
# Optional tip flare by adding a wider box at the far end
try:
    tip = Part.makeBox(spoke_len/2.0, {spoke_width_tip:.3f}, {barrel_len - 4.0:.3f})
    tip.Placement.Base.x = {hub_radius + 2.0:.3f} + spoke_len/2.0
    tip.Placement.Base.y = -{spoke_width_tip/2.0:.3f}
    tip.Placement.Base.z = -{spoke_thickness/2.0:.3f}
    base = Part.makeBox(spoke_len/2.0, {spoke_width_root:.3f}, {barrel_len - 4.0:.3f})
    base.Placement.Base.x = {hub_radius + 2.0:.3f}
    base.Placement.Base.y = -{spoke_width_root/2.0:.3f}
    base.Placement.Base.z = -{(barrel_len - 4.0)/2.0:.3f}
    spoke = base.fuse(tip)
except Exception:
    pass

# Move spoke outward from origin slightly to clear center bore
## spokes already positioned in XY; no Z translation required

# Pattern spokes around Z axis
spokes = spoke
for i in range(1, {spokes_count}):
    angle = (360.0/{spokes_count})*i
    rot = spoke.copy()
    rot.Placement = App.Placement(App.Vector(0,0,0), App.Rotation(App.Vector(0,0,1), angle), App.Vector(0,0,0))
    spokes = spokes.fuse(rot)

# Drill center bore
center_bore_solid = Part.makeCylinder({center_bore/2.0:.3f}, {max(hat_thickness, barrel_len):.3f})
center_bore_solid.Placement.Base.z = -{max(hat_thickness, barrel_len)/2.0:.3f}

print(f"[AlloyWheel] barrel_outer_r={barrel_outer_r:.1f} inner_r={barrel_inner_r:.1f} len={barrel_len:.1f}")
print(f"[AlloyWheel] hub_radius={hub_radius:.1f} spoke_len={spoke_len:.1f} width_root={spoke_width_root:.1f} width_tip={spoke_width_tip:.1f}")
wheel = barrel.fuse(hub).fuse(spokes)
wheel = wheel.cut(center_bore_solid)

# Bolt circle holes
from math import radians
pcd_r = {pcd_dia/2.0:.3f}
bolt_len = {max(hat_thickness, barrel_len):.3f}
for i in range({pcd_count}):
    a = radians((360.0/{pcd_count})*i)
    x = pcd_r * cos(a)
    y = pcd_r * sin(a)
    hole = Part.makeCylinder({bolt_hole_d/2.0:.3f}, bolt_len)
    hole.Placement.Base = App.Vector(x, y, -bolt_len/2.0)
    wheel = wheel.cut(hole)

# Small edge fillet (try/catch)
try:
    wheel = wheel.makeFillet(1.0, wheel.Edges)
except Exception:
    pass

# Create debug object for spokes (to verify geometry visually)
try:
    dbg = _doc.addObject("Part::Feature", "SpokesDebug")
    dbg.Shape = spokes
except Exception:
    pass

# Create final object
obj = _doc.addObject("Part::Feature", "AlloyWheel")
obj.Shape = wheel
_doc.recompute()
"""
    return code
