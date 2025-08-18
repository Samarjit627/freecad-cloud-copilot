import FreeCAD as App
import Part


def create_cube(doc=None,
                length=20.0,
                width=20.0,
                height=20.0,
                fillet_radius=0.0,
                label=None,
                transparency=0):
    """
    Create a rectangular block (cube/prism) with optional edge fillet.

    Args:
        doc: FreeCAD document. If None, a new document named "Cube" is created.
        length: X dimension in mm.
        width: Y dimension in mm.
        height: Z dimension in mm.
        fillet_radius: Optional fillet radius for vertical edges (0 for none).
        label: Optional label for the Part object.
        transparency: View transparency 0..100

    Returns:
        The FreeCAD document containing the cube object.
    """
    if doc is None:
        doc = App.newDocument("Cube")

    L = max(0.01, float(length))
    W = max(0.01, float(width))
    H = max(0.01, float(height))

    box = Part.makeBox(L, W, H)

    # Optional simple fillet on vertical outer edges
    if fillet_radius and fillet_radius > 0:
        try:
            edges_to_fillet = []
            for e in box.Edges:
                v1, v2 = e.Vertexes[0].Point, e.Vertexes[1].Point
                # Vertical edges have same X,Y and different Z
                if abs(v1.x - v2.x) < 1e-6 and abs(v1.y - v2.y) < 1e-6 and abs(v1.z - v2.z) > 1e-6:
                    edges_to_fillet.append(e)
            if edges_to_fillet:
                box = box.makeFillet(float(fillet_radius), edges_to_fillet)
        except Exception:
            pass

    obj = doc.addObject("Part::Feature", "Cube")
    obj.Shape = box
    obj.Label = label or f"Cube {L}x{W}x{H}"

    try:
        import FreeCADGui
        if hasattr(FreeCADGui, 'ActiveDocument') and FreeCADGui.ActiveDocument:
            obj.ViewObject.Transparency = int(transparency)
            obj.ViewObject.ShapeColor = (0.85, 0.85, 0.9)
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
    create_cube()
