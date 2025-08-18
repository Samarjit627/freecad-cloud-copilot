import FreeCAD as App
import Part


def create_cylinder(doc=None,
                    diameter=20.0,
                    height=50.0,
                    center_at_origin=False,
                    bore_diameter=0.0,
                    label=None,
                    transparency=0):
    """
    Create a simple cylinder primitive with optional bore.

    Args:
        doc: FreeCAD document. If None, a new document named "Cylinder" is created.
        diameter: Outer diameter in mm.
        height: Height in mm.
        center_at_origin: If True, center along Z around origin; otherwise base at Z=0.
        bore_diameter: Optional inner bore diameter (0 for solid).
        label: Optional label for the Part object.
        transparency: View transparency 0..100

    Returns:
        The FreeCAD document containing the cylinder object.
    """
    if doc is None:
        doc = App.newDocument("Cylinder")

    r = max(0.01, float(diameter) / 2.0)
    h = max(0.01, float(height))

    base_vec = App.Vector(0, 0, -h/2.0) if center_at_origin else App.Vector(0, 0, 0)
    cyl = Part.makeCylinder(r, h, base_vec, App.Vector(0, 0, 1))

    if bore_diameter and bore_diameter > 0:
        br = max(0.01, float(bore_diameter) / 2.0)
        if br >= r:
            br = r - 0.1
        bore = Part.makeCylinder(br, h, base_vec, App.Vector(0, 0, 1))
        cyl = cyl.cut(bore)

    obj = doc.addObject("Part::Feature", "Cylinder")
    obj.Shape = cyl
    obj.Label = label or f"Cylinder D{diameter}xH{height}"

    try:
        import FreeCADGui
        if hasattr(FreeCADGui, 'ActiveDocument') and FreeCADGui.ActiveDocument:
            obj.ViewObject.Transparency = int(transparency)
            obj.ViewObject.ShapeColor = (0.8, 0.8, 0.85)
    except Exception:
        pass

    doc.recompute()
    try:
        import FreeCADGui
        if FreeCADGui.ActiveDocument:
            FreeCADGui.updateGui()
    except Exception:
        pass

    return doc


if __name__ == "__main__":
    create_cylinder()
