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
               include_keyway=False,
               double_helical=False):
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
    print(f"Requested thickness: {thickness}mm, helix angle: {helix_angle}°")
    
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
    # Ensure Part and App are available in this scope for all fallbacks
    try:
        import FreeCAD as App  # noqa: F401
    except Exception:
        pass
    try:
        import Part  # noqa: F401
    except Exception:
        Part = None
    
    try:
        # Prefer freecad.gears features module (headless) for true involute/helical
        gear_shape = None
        try:
            import importlib, inspect
            inv_mod = None
            # Most installs expose a single module file: freecad.gears.features (deprecated warning you saw)
            # Try that first, then the submodule variant.
            for mod_name in [
                'freecad.gears.features',
                'freecad.gears.involute_gear',
            ]:
                try:
                    m = importlib.import_module(mod_name)
                    if hasattr(m, 'InvoluteGear'):
                        inv_mod = m
                        print(f"Gears WB feature import succeeded: {mod_name}")
                        break
                    else:
                        print(f"Gears WB module loaded but no InvoluteGear on {mod_name}")
                except Exception as e:
                    print(f"Gears WB feature import failed for {mod_name}: {e}")
            if inv_mod is not None:
                inv_ctor = getattr(inv_mod, 'InvoluteGear')

                def _set_prop_g(obj, names, value):
                    for n in names:
                        try:
                            if hasattr(obj, n):
                                setattr(obj, n, value)
                                return True
                            if hasattr(obj, 'PropertiesList') and n in getattr(obj, 'PropertiesList', []):
                                setattr(obj, n, value)
                                return True
                        except Exception:
                            pass
                    return False

                def _make_gears(name, beta_deg, height_val):
                    g = doc.addObject("Part::FeaturePython", name)
                    inv_ctor(g)
                    # Common property names in freecad.gears
                    _set_prop_g(g, ["num_teeth", "z", "teeth", "Teeth", "NumberOfTeeth"], int(teeth))
                    _set_prop_g(g, ["m", "module", "Module"], float(module))
                    _set_prop_g(g, ["alpha", "pressure_angle", "PressureAngle", "pressureAngle"], float(pressure_angle))
                    _set_prop_g(g, ["beta", "helix_angle", "HelixAngle", "Beta"], float(beta_deg))
                    _set_prop_g(g, ["w", "height", "thickness", "Width", "Thickness"], float(height_val))
                    # Bore handling (if provided)
                    try:
                        bore = float(center_bore) if center_bore is not None else None
                    except Exception:
                        bore = None
                    if bore is not None:
                        _set_prop_g(g, ["axle_hole"], True)
                        _set_prop_g(g, ["axle_holesize", "offset_holesize"], bore)
                    # Double helical if supported natively
                    if double_helical:
                        if _set_prop_g(g, ["double_helix"], True):
                            # rely on native double helix; keep height as requested
                            pass
                    doc.recompute()
                    shape = getattr(g, 'Shape', None)
                    if not shape or shape.isNull():
                        raise RuntimeError("freecad.gears InvoluteGear produced no Shape")
                    return g

                if double_helical and abs(helix_angle) < 0.1:
                    helix_angle = 15.0

                if double_helical:
                    h_half = max(0.1, thickness/2.0)
                    # First try native double_helix support
                    try:
                        g_native = _make_gears("HelicalGear_DH", abs(helix_angle), float(thickness))
                        shp = g_native.Shape
                        if shp and not shp.isNull():
                            gear_shape = shp.copy()
                            try:
                                import FreeCADGui
                                if FreeCADGui.ActiveDocument:
                                    FreeCADGui.ActiveDocument.getObject(g_native.Name).Visibility = False
                            except Exception:
                                pass
                        else:
                            raise RuntimeError("native double_helix produced no shape")
                    except Exception:
                        # Fallback: two halves with opposite helix
                        g1 = _make_gears("HelicalGear_A", abs(helix_angle), h_half)
                        g2 = _make_gears("HelicalGear_B", -abs(helix_angle), h_half)
                        try:
                            pl = g2.Placement
                            pl.Base.z += h_half
                            g2.Placement = pl
                        except Exception:
                            pass
                        doc.recompute()
                        gear_shape = g1.Shape.fuse(g2.Shape)
                        try:
                            import FreeCADGui
                            if FreeCADGui.ActiveDocument:
                                FreeCADGui.ActiveDocument.getObject(g1.Name).Visibility = False
                                FreeCADGui.ActiveDocument.getObject(g2.Name).Visibility = False
                        except Exception:
                            pass
                else:
                    g = _make_gears("Gear", float(helix_angle), float(thickness))
                    # Some versions produce wires; turn into solid if needed
                    shp = g.Shape
                    try:
                        if len(shp.Solids) == 0:
                            import Part, FreeCAD as App
                            wires = shp.Wires if hasattr(shp,'Wires') else []
                            outer = max(wires, key=lambda w: w.BoundBox.DiagonalLength) if wires else Part.Wire(shp.Edges)
                            face = Part.Face(outer)
                            solid = face.extrude(App.Vector(0,0,float(thickness)))
                            gear_shape = solid
                        else:
                            gear_shape = shp.copy()
                    except Exception:
                        gear_shape = shp.copy()
                    try:
                        import FreeCADGui
                        if FreeCADGui.ActiveDocument:
                            FreeCADGui.ActiveDocument.getObject(g.Name).Visibility = False
                    except Exception:
                        pass

                try:
                    print(f"Using Gears WB features from {inspect.getfile(inv_mod)}")
                except Exception:
                    pass
            else:
                print("Gears WB feature module not found; will try alternative paths")
        except Exception as _:  # keep variable concise; detailed logs above
            pass

        if gear_shape is None:
            # Legacy paths only if headless features unavailable
            fcg_err = None
            try:
                raise ImportError("Skip FCGear path per environment")
            except Exception as fcg_err:
                # Attempt 2.5: PartDesign built-in involute gear feature (if present)
                try:
                    import FreeCAD as App
                    g = doc.addObject("PartDesign::InvoluteGear", "PD_InvoluteGear")
                    def _set_pd(obj, names, val):
                        for n in names:
                            try:
                                if hasattr(obj, n):
                                    setattr(obj, n, val)
                                    return True
                                if hasattr(obj, 'PropertiesList') and n in getattr(obj, 'PropertiesList', []):
                                    setattr(obj, n, val)
                                    return True
                            except Exception:
                                pass
                        return False
                    _set_pd(g, ["NbTeeth","NumberOfTeeth","teeth","Teeth","z"], int(teeth))
                    _set_pd(g, ["Module","module","m"], float(module))
                    _set_pd(g, ["PressureAngle","pressure_angle","alpha"], float(pressure_angle))
                    _set_pd(g, ["HelixAngle","beta","helix_angle","Beta"], float(helix_angle))
                    _set_pd(g, ["Width","height","thickness","Thickness","w"], float(thickness))
                    doc.recompute()
                    shape = getattr(g, 'Shape', None)
                    if not shape or shape.isNull():
                        raise RuntimeError("PartDesign::InvoluteGear produced no Shape")
                    gear_shape = shape.copy()
                    try:
                        import FreeCADGui
                        if FreeCADGui.ActiveDocument:
                            FreeCADGui.ActiveDocument.getObject(g.Name).Visibility = False
                    except Exception:
                        pass
                except Exception as pd_err:
                    # As a last attempt with the gears WB, try invoking its GUI command
                    try:
                        import FreeCAD as App, FreeCADGui
                        # Ensure we have an active document
                        if App.ActiveDocument is None:
                            App.newDocument("GearsAuto")
                        # Close any active task dialogs to avoid conflicts
                        try:
                            while getattr(FreeCADGui.Control, 'activeDialog', lambda: None)():
                                FreeCADGui.Control.closeDialog()
                        except Exception:
                            pass
                        if FreeCADGui and FreeCADGui.ActiveDocument:
                            try:
                                # Activate workbench if available and run the create command
                                try:
                                    FreeCADGui.activateWorkbench('GearsWorkbench')
                                except Exception:
                                    pass
                                # Discover a suitable command id
                                try:
                                    avail = [c for c in getattr(FreeCADGui, 'listCommands', lambda: [])()]
                                except Exception:
                                    avail = []
                                preferred = [
                                    'gearsCreateInvoluteGear',
                                    'gearsInvoluteGear',
                                    'Gears_CreateInvoluteGear',
                                    'Gears_InvoluteGear',
                                ]
                                cmd_to_run = None
                                for name in preferred:
                                    if name in avail:
                                        cmd_to_run = name
                                        break
                                if cmd_to_run is None and avail:
                                    # Fallback fuzzy match
                                    lowers = [c for c in avail if 'gear' in c.lower() and 'involute' in c.lower()]
                                    cmd_to_run = lowers[0] if lowers else (avail[0] if avail else None)
                                if not cmd_to_run:
                                    raise RuntimeError('No gears GUI command found (listCommands was empty)')
                                ok = FreeCADGui.runCommand(cmd_to_run)
                                if ok is None:
                                    # Some versions return None even on success
                                    pass
                                doc.recompute()
                                # Get the newest object as the created gear
                                g = doc.Objects[-1] if doc.Objects else None
                                if g is None:
                                    raise RuntimeError('gears GUI command did not create an object')
                                # Map parameters defensively
                                def _set(obj, names, val):
                                    for n in names:
                                        try:
                                            if hasattr(obj, n):
                                                setattr(obj, n, val)
                                                return True
                                        except Exception:
                                            pass
                                    return False
                                _set(g, ["teeth","Teeth","NumberOfTeeth","z","NbTeeth"], int(teeth))
                                _set(g, ["module","Module","m"], float(module))
                                _set(g, ["pressure_angle","PressureAngle","pressureAngle","alpha"], float(pressure_angle))
                                _set(g, ["beta","helix_angle","HelixAngle","Beta"], float(helix_angle))
                                _set(g, ["height","thickness","Width","Thickness","w"], float(thickness))
                                doc.recompute()
                                shape = getattr(g, 'Shape', None)
                                if not shape or shape.isNull():
                                    raise RuntimeError('gears GUI command produced no Shape')
                                # If only wires/edges, build face and extrude by thickness to make a solid
                                try:
                                    if len(shape.Solids) == 0:
                                        import Part
                                        # Try to get the biggest outer wire
                                        wires = shape.Wires if hasattr(shape, 'Wires') else []
                                        outer = None
                                        if wires:
                                            outer = max(wires, key=lambda w: w.BoundBox.DiagonalLength)
                                        else:
                                            # Build wire from edges
                                            outer = Part.Wire(shape.Edges)
                                        face = Part.Face(outer)
                                        solid = face.extrude(App.Vector(0,0,float(thickness)))
                                        gear_shape = solid.removeSplitter() if hasattr(solid, 'removeSplitter') else solid
                                    else:
                                        gear_shape = shape.copy()
                                except Exception:
                                    gear_shape = shape.copy()
                                # Hide the parametric source for stability
                                try:
                                    FreeCADGui.ActiveDocument.getObject(g.Name).Visibility = False
                                except Exception:
                                    pass
                            except Exception as cmd_err:
                                raise cmd_err
                        else:
                            raise RuntimeError('FreeCADGui not available or no ActiveDocument')
                    except Exception as cmd_gears_err:
                        print(f"FCGear/gears/PartDesign not available or failed; using fallback. Detail: {fcg_err} | gears: {gears_err} | partdesign: {pd_err} | gears-cmd: {cmd_gears_err}")
                        # Create simplified involute-like gear (existing fallback)
                        gear_shape = create_involute_gear(teeth, module, pressure_angle, helix_angle, thickness)
                try:
                    import FreeCAD as App, FreeCADGui
                    # Ensure we have an active document
                    if App.ActiveDocument is None:
                        App.newDocument("GearsAuto")
                    if FreeCADGui and FreeCADGui.ActiveDocument:
                        try:
                            # Activate workbench if available and run the create command
                            try:
                                FreeCADGui.activateWorkbench('GearsWorkbench')
                            except Exception:
                                pass
                            # Discover a suitable command id
                            try:
                                avail = [c for c in getattr(FreeCADGui, 'listCommands', lambda: [])()]
                            except Exception:
                                avail = []
                            preferred = [
                                'gearsCreateInvoluteGear',
                                'gearsInvoluteGear',
                                'Gears_CreateInvoluteGear',
                                'Gears_InvoluteGear',
                            ]
                            cmd_to_run = None
                            for name in preferred:
                                if name in avail:
                                    cmd_to_run = name
                                    break
                            if cmd_to_run is None and avail:
                                # Fallback fuzzy match
                                lowers = [c for c in avail if 'gear' in c.lower() and 'involute' in c.lower()]
                                cmd_to_run = lowers[0] if lowers else (avail[0] if avail else None)
                            if not cmd_to_run:
                                raise RuntimeError('No gears GUI command found (listCommands was empty)')
                            ok = FreeCADGui.runCommand(cmd_to_run)
                            if ok is None:
                                # Some versions return None even on success
                                pass
                            doc.recompute()
                            # Get the newest object as the created gear
                            g = doc.Objects[-1] if doc.Objects else None
                            if g is None:
                                raise RuntimeError('gearsCreateInvoluteGear did not create an object')
                            # Map parameters defensively
                            def _set(obj, names, val):
                                for n in names:
                                    try:
                                        if hasattr(obj, n):
                                            setattr(obj, n, val)
                                            return True
                                    except Exception:
                                        pass
                                return False
                            _set(g, ["teeth","Teeth","NumberOfTeeth","z"], int(teeth))
                            _set(g, ["module","Module","m"], float(module))
                            _set(g, ["pressure_angle","PressureAngle","pressureAngle","alpha"], float(pressure_angle))
                            _set(g, ["beta","helix_angle","HelixAngle","Beta"], float(helix_angle))
                            _set(g, ["height","thickness","Width","Thickness","w"], float(thickness))
                            doc.recompute()
                            shape = getattr(g, 'Shape', None)
                            if not shape or shape.isNull():
                                raise RuntimeError('gearsCreateInvoluteGear produced no Shape')
                            # Use its shape (copy) as final
                            gear_shape = shape.copy()
                            # Hide the parametric source for stability
                            try:
                                FreeCADGui.ActiveDocument.getObject(g.Name).Visibility = False
                            except Exception:
                                pass
                        except Exception as cmd_err:
                            raise cmd_err
                    else:
                        raise RuntimeError('FreeCADGui not available or no ActiveDocument')
                except Exception as cmd_gears_err:
                    print(f"FCGear/gears not available or failed; using fallback. Detail: {fcg_err} | gears: {gears_err} | gears-cmd: {cmd_gears_err}")
                    # Create simplified involute-like gear (existing fallback)
                    gear_shape = create_involute_gear(teeth, module, pressure_angle, helix_angle, thickness)

        # Bore
        if bore_diameter > 0 and gear_shape is not None:
            bore = Part.makeCylinder(bore_diameter/2, thickness, App.Vector(0,0,0), App.Vector(0,0,1))
            gear_shape = gear_shape.cut(bore)
            print(f"Added center bore with diameter {bore_diameter}mm")

        # Hub
        if hub_diameter > 0 and hub_thickness > 0 and gear_shape is not None:
            if hub_diameter <= pitch_diameter:
                hub = Part.makeCylinder(hub_diameter/2, thickness + hub_thickness,
                                       App.Vector(0,0,-hub_thickness), App.Vector(0,0,1))
                gear_shape = gear_shape.fuse(hub)
                print(f"Added hub with diameter {hub_diameter}mm and thickness {hub_thickness}mm")
            else:
                print("Hub diameter too large, ignoring hub")

        # Keyway
        if include_keyway and bore_diameter > 5 and gear_shape is not None:
            keyway_width = min(bore_diameter/4, 5)
            keyway_depth = keyway_width / 2
            keyway_length = thickness
            keyway = Part.makeBox(keyway_depth, keyway_width, keyway_length,
                                 App.Vector(-bore_diameter/2 - keyway_depth/2, -keyway_width/2, 0))
            gear_shape = gear_shape.cut(keyway)
            print(f"Added keyway {keyway_width:.1f}x{keyway_depth:.1f}mm")

        # If something went wrong, fallback to cylinder
        if gear_shape is None:
            raise RuntimeError("Gear shape generation failed")

    except Exception as e:
        print(f"Error creating gear: {e}")
        # Fallback to simple cylindrical gear
        gear_shape = Part.makeCylinder(pitch_diameter/2, thickness)
        if bore_diameter > 0:
            bore = Part.makeCylinder(bore_diameter/2, thickness)
            gear_shape = gear_shape.cut(bore)
    
    # Create FreeCAD object
    safe_beta = float(helix_angle)
    hand = 'LH' if safe_beta < 0 else ('RH' if safe_beta > 0 else 'SPUR')
    name_core = f"Gear_T{int(teeth)}_m{float(module):g}_b{abs(int(round(safe_beta)))}_{hand}"
    name_core = name_core.replace('.', 'p')
    obj_name = name_core[:60]
    gear_obj = doc.addObject("Part::Feature", obj_name)
    gear_obj.Shape = gear_shape
    gear_obj.Label = f"Gear M{module} T{teeth} Beta {helix_angle}° Bore {bore_diameter}mm"
    
    # Attach key metadata as properties for later inspection/measurement
    try:
        def add_prop(obj, ptype, pname, val):
            if not hasattr(obj, pname):
                obj.addProperty(ptype, pname)
            setattr(obj, pname, val)
        add_prop(gear_obj, 'App::PropertyInteger', 'num_teeth', int(teeth))
        add_prop(gear_obj, 'App::PropertyFloat', 'module', float(module))
        add_prop(gear_obj, 'App::PropertyFloat', 'pressure_angle', float(pressure_angle))
        add_prop(gear_obj, 'App::PropertyFloat', 'helix_angle', float(helix_angle))
        add_prop(gear_obj, 'App::PropertyFloat', 'height', float(thickness))
        add_prop(gear_obj, 'App::PropertyFloat', 'bore_diameter', float(bore_diameter))
        add_prop(gear_obj, 'App::PropertyBool', 'double_helix', bool(double_helical))
    except Exception:
        pass

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
            # Keep view stable; don't force fitAll to preserve relative scale across multiple objects
            FreeCADGui.ActiveDocument.ActiveView.viewAxometric()
            FreeCADGui.updateGui()
    except Exception:
        pass
    
    print("Gear creation complete")
    return gear_obj

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
    # Note: When FCGear is unavailable, we approximate helicals as spur gears with the correct thickness.
    # The prior implementation incorrectly used revolve with a tiny angle, producing a wafer-thin wedge.
    if helix_angle != 0:
        print("[Fallback] Approximating helical gear as spur extrusion (FCGear not available)")
    gear = gear_face.extrude(App.Vector(0, 0, float(thickness)))
    
    return gear

if __name__ == "__main__":
    create_gear()
