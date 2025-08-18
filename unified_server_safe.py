#!/usr/bin/env python3
"""
Deterministic Text-to-CAD Sidecar Server (no LLM, no FreeCAD dependency at import time)
- Health and capabilities endpoints
- /api/v1/text-to-cad routes to deterministic generators for cube/cylinder
- Returns FreeCAD Python code as a string; does not import FreeCAD itself
- Uses the same API key header: X-API-Key
"""
import os
import time
import json
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.security import APIKeyHeader

API_KEY = os.environ.get("API_KEY", "test-api-key")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

class TextToCADRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 2000
    temperature: Optional[float] = 0.1

class TextToCADResponse(BaseModel):
    prompt: str
    engineering_analysis: str
    freecad_code: str
    metadata: Dict[str, Any]
    cloud_error: Optional[str] = None
    using_fallback: Optional[bool] = True

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return api_key

app = FastAPI(title="Deterministic Text-to-CAD Server", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": time.time(), "templates": ["cube", "cylinder", "water_bottle"]}

@app.get("/")
async def root():
    return {"message": "Deterministic Text-to-CAD Server", "endpoints": {"health": "/health", "text_to_cad": "/api/v1/text-to-cad"}}

@app.get("/list-capabilities")
async def list_capabilities(api_key: str = Depends(verify_api_key)):
    return {
        "supported_parts": ["cube", "cylinder", "water_bottle"],
        "supported_features": [],
        "version": "0.1.0"
    }

# --- Deterministic parsing and code generation ---
import re

def parse_prompt(text: str):
    t = text.lower()
    if any(k in t for k in ["bottle", "water bottle", "container"]):
        return "water_bottle"
    if any(k in t for k in ["cylinder", "diameter", "ø", "phi"]):
        return "cylinder"
    if any(k in t for k in ["cube", "block"]):
        return "cube"
    return None

def gen_cube_code(params: dict) -> str:
    L = float(params.get("length", 20.0))
    W = float(params.get("width", 20.0))
    H = float(params.get("height", 20.0))
    fillet = float(params.get("fillet_radius", 0.0))
    label = params.get("label", f"Cube_{int(L)}x{int(W)}x{int(H)}")
    return f"""
# Deterministic Cube
import FreeCAD as App
import Part

doc = App.newDocument("Cube")
App.setActiveDocument(doc.Name)

box = Part.makeBox({L}, {W}, {H})
if {fillet} > 0:
    try:
        edges_to_fillet = []
        for e in box.Edges:
            v1, v2 = e.Vertexes[0].Point, e.Vertexes[1].Point
            if abs(v1.x - v2.x) < 1e-6 and abs(v1.y - v2.y) < 1e-6 and abs(v1.z - v2.z) > 1e-6:
                edges_to_fillet.append(e)
        if edges_to_fillet:
            box = box.makeFillet({fillet}, edges_to_fillet)
    except Exception:
        pass

obj = doc.addObject("Part::Feature", "Cube")
obj.Shape = box
obj.Label = "{label}"

doc.recompute()
try:
    import FreeCADGui
    FreeCADGui.updateGui()
except Exception:
    pass
try:
    import FreeCAD as _App
    print(f"[DimReport] Cube LxWxH: {L} x {W} x {H} mm")
except Exception:
    pass
""".strip()

def gen_cylinder_code(params: dict) -> str:
    d = float(params.get("diameter", 20.0))
    h = float(params.get("height", 50.0))
    bore = params.get("bore_diameter")
    label = params.get("label", f"Cylinder_D{int(d)}_H{int(h)}")
    core = f"""
# Deterministic Cylinder
import FreeCAD as App
import Part

doc = App.newDocument("Cylinder")
App.setActiveDocument(doc.Name)

radius = {d/2.0}
height = {h}

cyl = Part.makeCylinder(radius, height)
"""
    if bore is not None:
        core += f"\ninner = Part.makeCylinder({float(bore)/2.0}, {h})\ncyl = cyl.cut(inner)\n"
    core += f"""
obj = doc.addObject("Part::Feature", "Cylinder")
obj.Shape = cyl
obj.Label = "{label}"

doc.recompute()
try:
    import FreeCADGui
    FreeCADGui.updateGui()
except Exception:
    pass
try:
    import FreeCAD as _App
    if {('None' if bore is None else 'True')}:
        print(f"[DimReport] Cylinder OD: {d} mm, Height: {h} mm")
    else:
        print(f"[DimReport] Cylinder OD: {d} mm, ID: {bore} mm, Height: {h} mm")
except Exception:
    pass
"""
    return core.strip()

def extract_params(part: str, text: str) -> dict:
    t = text.lower()
    params: Dict[str, Any] = {}
    if part == "cube":
        # 100 x 50 x 25 mm
        m = re.search(r"(\d+\.?\d*)\s*mm\s*[x×]\s*(\d+\.?\d*)\s*mm\s*[x×]\s*(\d+\.?\d*)\s*mm", t)
        if m:
            params.update({"length": float(m.group(1)), "width": float(m.group(2)), "height": float(m.group(3))})
        else:
            s = re.search(r"(\d+\.?\d*)\s*mm", t)
            if s:
                v = float(s.group(1))
                params.update({"length": v, "width": v, "height": v})
        f = re.search(r"fillet\s*(\d+\.?\d*)", t)
        if f:
            params["fillet_radius"] = float(f.group(1))
        return params
    if part == "cylinder":
        patts = [
            r"[øo]\s*(\d+\.?\d*)\s*[x×]\s*(\d+\.?\d*)\s*mm",
            r"(\d+\.?\d*)\s*mm\s*(?:diameter|dia)\s*[x×]\s*(\d+\.?\d*)\s*mm",
            r"(?:diameter|dia)\s*(\d+\.?\d*)\s*mm.*?(?:height|tall|h)\s*(\d+\.?\d*)\s*mm",
            r"(\d+\.?\d*)\s*mm\s*[x×]\s*(\d+\.?\d*)\s*mm\s*cylinder",
        ]
        d_h = None
        for p in patts:
            m = re.search(p, t)
            if m:
                d_h = (float(m.group(1)), float(m.group(2)))
                break
        if d_h:
            params["diameter"], params["height"] = d_h
        else:
            d = re.search(r"(?:diameter|dia|[øo])\s*(\d+\.?\d*)\s*mm", t)
            h = re.search(r"(?:height|tall|h)\s*(\d+\.?\d*)\s*mm", t)
            if d:
                params["diameter"] = float(d.group(1))
            if h:
                params["height"] = float(h.group(1))
        # accept order-insensitive phrasing: "8mm bore" or "bore 8mm"
        bore = re.search(r"(?:bore|inner|id)\s*(\d+\.?\d*)\s*mm", t) or \
               re.search(r"(\d+\.?\d*)\s*mm\s*(?:bore|inner|id)", t)
        if bore:
            params["bore_diameter"] = float(bore.group(1))
        return params
    if part == "water_bottle":
        # volume in ml
        ml = re.search(r"(\d+\.?\d*)\s*ml", t)
        if ml:
            params["volume_ml"] = float(ml.group(1))
        wt = re.search(r"wall(?:\s*thickness)?\s*(\d+\.?\d*)\s*mm", t)
        if wt:
            params["wall_thickness"] = float(wt.group(1))
        # Height with word boundaries to avoid matching 'h' inside words like 'pitch'
        ht = re.search(r"\b(?:height|tall|h)\b\s*(\d+\.?\d*)\s*mm", t)
        if ht:
            params["height"] = float(ht.group(1))
        params["transparent"] = ("transparent" in t or "translucent" in t)
        # Design options
        m = re.search(r"transition\s*[:=]?\s*(frustum|loft|s-?curve)", t)
        if m: params["transition"] = m.group(1)
        m = re.search(r"base\s*[:=]?\s*(flat|dome|concave)", t)
        if m: params["base"] = m.group(1)
        m = re.search(r"bottom\s*fillet\s*(\d+\.?\d*)\s*mm", t)
        if m: params["bottom_fillet"] = float(m.group(1))
        m = re.search(r"threads?\s*[:=]?\s*(helical|ring|none)", t)
        if m: params["threads"] = m.group(1)
        m = re.search(r"pitch\s*(\d+\.?\d*)\s*mm", t)
        if m: params["thread_pitch"] = float(m.group(1))
        m = re.search(r"starts?\s*(\d+)", t)
        if m: params["thread_starts"] = int(m.group(1))
        m = re.search(r"cap\s*[:=]?\s*(flat|rounded|sport|none)", t)
        if m: params["cap"] = m.group(1)
        m = re.search(r"grooves?\s*(\d+)", t)
        if m: params["groove_count"] = int(m.group(1))
        m = re.search(r"groove\s*depth\s*(\d+\.?\d*)\s*mm", t)
        if m: params["groove_depth"] = float(m.group(1))
        return params
    return params

def gen_bottle_code(params: dict) -> str:
    # Compute dimensions from volume
    V_ml = float(params.get("volume_ml", 750.0))
    V = V_ml * 1000.0  # mm^3
    wall = float(params.get("wall_thickness", 2.0))
    height = params.get("height")
    transparent = bool(params.get("transparent", False))
    # If height not given, assume aspect ratio H = 2.8 * OD and solve for OD
    import math
    if height is None:
        # Let OD = D, H = 2.8*D, volume of hollow cylinder ~ pi*(R^2 - r^2)*H.
        # Assume r = R - wall, wall relatively small; approximate with solid cylinder for solving initial D.
        # V ≈ pi*(D/2)^2*(2.8D) => V ≈ (pi*2.8/4) * D^3 ⇒ D ≈ (4V/(pi*2.8))^(1/3)
        D = (4.0*V/(math.pi*2.8))**(1.0/3.0)
        height = 2.8*D
    else:
        height = float(height)
        # Solve OD from V = pi*(R^2 - (R-wall)^2)*H = pi*(2R*wall - wall^2)*H
        # approximate for wall << R: V ≈ pi*(2R*wall)*H ⇒ R ≈ V/(2*pi*wall*H)
        R = max(5.0, V/(2.0*math.pi*wall*height))
        D = 2.0*R
    R = D/2.0
    # options
    transition = (params.get("transition") or "frustum").lower()
    base_mode = (params.get("base") or "flat").lower()
    bottom_fillet = float(params.get("bottom_fillet", 0))
    threads_mode = (params.get("threads") or "ring").lower()
    thread_pitch = float(params.get("thread_pitch", 0.12*min(20.0, 0.12*height)))
    thread_starts = int(params.get("thread_starts", 1))
    cap_mode = (params.get("cap") or "flat").lower()
    groove_count = int(params.get("groove_count", 0))
    groove_depth = float(params.get("groove_depth", 1.0))

    # initial inner radius guess
    r_inner = max(0.1, R - max(0.6*wall, wall))
    eps = 0.05
    neck_h = min(20.0, 0.12*height)
    neck_r = 0.6*R

    # Aspect-preserving capacity alignment: scale R and H together by factor s
    target_ml = V_ml
    base_R, base_H = R, height

    def _estimate_capacity_ml_scaled(s: float) -> float:
        R_s = base_R * s
        H_s = base_H * s
        neck_h_s = min(20.0, 0.12*H_s)
        trans_h_est = max(6.0, 0.15*H_s)
        body_h_est = max(10.0, H_s - trans_h_est - neck_h_s)
        rin_eff_est = max(0.1, R_s - max(0.6*wall, wall) - 0.2)
        rin_top_est = max(0.1, 0.6*R_s - max(0.6*wall, wall))
        iz0_est = max(wall, 0.6*wall)
        iz1_est = max(0.1, body_h_est - wall - 0.2)
        ih = max(0.0, iz1_est - iz0_est)
        iz2_est = max(iz1_est+1e-3, body_h_est + trans_h_est - wall - 0.2)
        th = max(0.0, iz2_est - iz1_est)
        V_body = math.pi * (rin_eff_est**2) * ih
        V_trans = (math.pi * th / 3.0) * (rin_eff_est**2 + rin_eff_est*rin_top_est + rin_top_est**2)
        return (V_body + V_trans)/1000.0

    lo, hi = 0.5, 1.6
    best_s, best_err = 1.0, float('inf')
    for _ in range(18):
        mid = (lo + hi)/2.0
        est = _estimate_capacity_ml_scaled(mid)
        err = est - target_ml
        if abs(err) < best_err:
            best_err, best_s = abs(err), mid
        if err < 0:
            lo = mid
        else:
            hi = mid

    # apply best scale to dimensions and dependent parameters
    R = base_R * best_s
    height = base_H * best_s
    neck_h = min(20.0, 0.12*height)
    neck_r = 0.6*R
    r_inner = max(0.1, R - max(0.6*wall, wall))

    label = f"Bottle_{int(V_ml)}ml"
    transparency = 70 if transparent else 0
    return f"""
# Deterministic Water Bottle (approximate cylindrical shell + simple neck)
import FreeCAD as App
import Part
import math

doc = App.newDocument("Bottle")
App.setActiveDocument(doc.Name)

R = {R}
H = {height}
wall = {wall}
rin = {r_inner}
neck_h = {neck_h}
neck_r = {neck_r}
eps = 0.05
transition = "{transition}"
base_mode = "{base_mode}"
bottom_fillet = {bottom_fillet}
threads_mode = "{threads_mode}"
thread_pitch = {thread_pitch}
thread_starts = {thread_starts}
cap_mode = "{cap_mode}"
groove_count = {groove_count}
groove_depth = {groove_depth}

trans_h = max(6.0, 0.15*H)
body_h = max(10.0, H - trans_h - neck_h)

## Continuous shell via revolve profiles (outer and inner) in XZ plane
rin_eff = max(0.1, min(rin, R - max(0.6*wall, wall) - 0.2))
rin_top_eff = max(0.1, neck_r - max(0.6*wall, wall))
z0 = 0.0
z1 = body_h
z2 = body_h + trans_h
z3 = H

# Outer profile points (to Z axis): (0,z0)->(R,z0)->(R,z1)->(neck_r,z2)->(neck_r,z3)->(0,z3)->(0,z0)
op = [
    App.Vector(0,0,z0),
    App.Vector(R,0,z0),
    App.Vector(R,0,z1),
    App.Vector(neck_r,0,z2),
    App.Vector(neck_r,0,z3),
    App.Vector(0,0,z3),
    App.Vector(0,0,z0)
]
outer_wire = Part.makePolygon(op)
outer_face = Part.Face(outer_wire)
outer = outer_face.revolve(App.Vector(0,0,0), App.Vector(0,0,1), 360)

# Inner profile points (offset inwards by wall). Start above z=0 to keep a bottom wall
iz0 = max(wall, 0.6*wall)        # preserve bottom thickness roughly equal to wall
iz1 = max(0.1, z1 - wall - 0.2)  # inner at body top with safety offset
iz2 = max(iz1+1e-3, z2 - wall - 0.2)  # inner at transition top with safety offset
iz3 = z3 + 2*eps                 # slight extension above top is okay (neck/cap area)
ip = [
    App.Vector(0,0,iz0),
    App.Vector(rin_eff - eps,0,iz0),
    App.Vector(rin_eff - eps,0,iz1),
    App.Vector(rin_top_eff - eps,0,iz2),
    App.Vector(rin_top_eff - eps,0,iz3),
    App.Vector(0,0,iz3),
    App.Vector(0,0,iz0)
]
inner_wire = Part.makePolygon(ip)
inner_face = Part.Face(inner_wire)
inner = inner_face.revolve(App.Vector(0,0,0), App.Vector(0,0,1), 360)

bottle = outer.cut(inner).removeSplitter()
inner_space = inner.removeSplitter()

# derived for threads placement
neck_base_z = z2

# Fallback: if multiple solids are produced later, rebuild using a simple pipeline
def _simple_pipeline():
    body_outer = Part.makeCylinder(R, body_h + eps)
    body_inner = Part.makeCylinder(max(0.1, rin_eff - eps), body_h + 4*eps)
    body_inner.translate(App.Vector(0,0,-2*eps))
    solid = body_outer.cut(body_inner).removeSplitter()
    # transition outer/inner
    tr_out = Part.makeCone(R, neck_r, trans_h)
    tr_out.translate(App.Vector(0,0,body_h - eps))
    tr_in = Part.makeCone(max(0.1, rin_eff - eps), max(0.1, rin_top_eff - eps), max(0.1, trans_h - 2*eps))
    tr_in.translate(App.Vector(0,0,body_h + wall))
    trans_shell = tr_out.cut(tr_in).removeSplitter()
    solid = solid.fuse(trans_shell).removeSplitter()
    # neck
    nk = Part.makeCylinder(neck_r, neck_h + 2*eps)
    nk.translate(App.Vector(0,0,body_h + trans_h - 2*eps))
    solid = solid.fuse(nk).removeSplitter()
    return solid

# add threads when requested
try:
    if threads_mode == "helical":
        pitch = max(1.0, thread_pitch)
        starts = max(1, int(thread_starts))
        prof_r = max(0.8, 0.08*neck_r)  # slightly larger for visibility
        # Extend threads to overflow slightly beyond the cap line (neck top)
        thread_overflow = 4.0  # mm beyond neck height
        height_usable = max(6.0, neck_h + thread_overflow)
        try:
            print("[Threads] mode=helical "
                  + "pitch=" + str(pitch)
                  + " starts=" + str(starts)
                  + " height=" + str(round(height_usable, 2))
                  + " prof_r=" + str(round(prof_r, 2)))
        except Exception:
            pass
        for s in range(starts):
            helix = Part.makeHelix(pitch, height_usable, neck_r + prof_r*0.3, 0)
            # triangular profile in XZ plane at helix start
            p1 = App.Vector(neck_r + prof_r*0.1, 0, neck_base_z + 0.5)
            p2 = App.Vector(neck_r + prof_r*1.6, 0, neck_base_z + 0.5)
            p3 = App.Vector(neck_r + prof_r*0.8, 0, neck_base_z + 0.5 + prof_r)
            wire = Part.makePolygon([p1,p2,p3,p1])
            face = Part.Face(wire)
            sweep = face.makePipeShell([helix], True, True)
            # rotate each additional start around Z
            if starts>1 and s>0:
                sweep.rotate(App.Vector(0,0,neck_base_z), App.Vector(0,0,1), (360.0/starts)*s)
            bottle = bottle.fuse(sweep).removeSplitter()
        try:
            print("[Threads] Helical threads fused into bottle")
        except Exception:
            pass
    elif threads_mode == "ring":
        thread_count = 4
        thread_pitch_l = max(2.0, thread_pitch)
        thread_r_minor = max(0.5, 0.08*neck_r)
        try:
            print("[Threads] mode=ring "
                  + "count=" + str(thread_count)
                  + " pitch=" + str(thread_pitch_l)
                  + " r_minor=" + str(round(thread_r_minor, 2)))
        except Exception:
            pass
        for i in range(thread_count):
            ring = Part.makeTorus(neck_r + thread_r_minor*0.2, thread_r_minor)
            zc = neck_base_z + neck_h - (i+1)*thread_pitch_l*0.5
            ring.translate(App.Vector(0,0,zc))
            bottle = bottle.fuse(ring).removeSplitter()
        try:
            print("[Threads] Ring threads fused into bottle")
        except Exception:
            pass
    else:
        # threads_mode == 'none' -> skip
        pass
except Exception:
    pass

# base features and bottom fillet
try:
    if base_mode == "dome":
        # robust bottom dome via revolve of a closed profile in XZ plane
        dome_h = max(1.0, min(0.12*R, 0.06*H))
        pA = App.Vector(R, 0, 0)
        pB = App.Vector(0, 0, dome_h)
        arc = Part.Arc(pA, App.Vector(R*0.5, 0, dome_h*0.6), pB)
        e2 = Part.LineSegment(pB, App.Vector(0,0,0))
        e3 = Part.LineSegment(App.Vector(0,0,0), pA)
        wire = Part.Wire([arc.toShape(), e2.toShape(), e3.toShape()])
        face = Part.Face(wire)
        dome = face.revolve(App.Vector(0,0,0), App.Vector(0,0,1), 360)
        dome.translate(App.Vector(0,0, eps))
        bottle = bottle.fuse(dome).removeSplitter()
    elif base_mode == "concave":
        # concave recess via revolve and subtraction
        cav_r = max(0.5*R, R*0.9)
        cav_h = max(0.8, min(0.1*R, 0.05*H))
        pA = App.Vector(cav_r, 0, 0)
        pB = App.Vector(0, 0, cav_h)
        arc = Part.Arc(pA, App.Vector(cav_r*0.5, 0, cav_h*0.6), pB)
        e2 = Part.LineSegment(pB, App.Vector(0,0,0))
        e3 = Part.LineSegment(App.Vector(0,0,0), pA)
        wire = Part.Wire([arc.toShape(), e2.toShape(), e3.toShape()])
        face = Part.Face(wire)
        cavity = face.revolve(App.Vector(0,0,0), App.Vector(0,0,1), 360)
        cavity.translate(App.Vector(0,0, eps))
        bottle = bottle.cut(cavity).removeSplitter()

    # grooves along body
    if groove_count>0:
        step = max(1, int(body_h//(groove_count+1)))
        z_start = wall + bottom_fillet + 2*eps + 2.0
        for gi in range(1, groove_count+1):
            zc = max(z_start, wall + eps + gi*step)
            cutter = Part.makeCylinder(R - 0.5*groove_depth, max(1.0, groove_depth*1.5))
            cutter.translate(App.Vector(0,0,zc))
            bottle = bottle.cut(cutter).removeSplitter()

    # consolidate: ensure single solid and report diagnostics
    try:
        solids = list(bottle.Solids)
        if len(solids) > 1:
            print("[Consolidate] Multiple solids detected: {{}}. Fusing...".format(len(solids)))
            fused = solids[0]
            for s in solids[1:]:
                fused = fused.fuse(s)
            bottle = fused.removeSplitter()
        # refine and ensure solid
        bottle = bottle.removeSplitter()
        if hasattr(bottle, 'refine'):  # Part::TopoShape in console has refine as function
            try:
                bottle = bottle.refine()
            except Exception:
                pass
        cnt = len(bottle.Solids)
        print("[Solids] count={{}}, types={{}}".format(cnt, [s.ShapeType for s in bottle.Solids]))
        print("[ZRanges] {{}}".format([ (round(s.BoundBox.ZMin,2), round(s.BoundBox.ZMax,2)) for s in bottle.Solids ]))
        if cnt != 1 or not bottle.isValid():
            print("[Fallback] Rebuilding bottle with simple pipeline ...")
            bottle = _simple_pipeline()
            cnt2 = len(bottle.Solids)
            print("[Solids:Fallback] count={{}}, valid={{}}".format(cnt2, bottle.isValid()))
    except Exception as e:
        print("[Consolidate] Skipped: {{}}".format(e))

    # bottom fillet if requested
    if bottom_fillet>0:
        try:
            edges = []
            for e in bottle.Edges:
                bb = e.BoundBox
                if abs(bb.ZMin - 0.0) < 0.05:
                    edges.append(e)
            if edges:
                rad = min(6.0, 0.15*R)
                if bottom_fillet>0:
                    rad = bottom_fillet
                bottle = bottle.makeFillet(rad, edges)
        except Exception:
            pass
except Exception:
    pass

obj = doc.addObject("Part::Feature", "WaterBottle")
obj.Shape = bottle
obj.Label = "{label}"
try:
    import FreeCADGui
    if {transparency} > 0:
        obj.ViewObject.Transparency = {transparency}
except Exception:
    pass

# independent cap: only when requested
try:
    if cap_mode != "none":
        cap_h = max(10.0, 0.6*neck_h)
        cap_or = neck_r + max(2.5, 0.12*R)
        cap_ir = max(0.1, neck_r - 0.2)  # slight clearance
        if cap_mode == "rounded":
            cap_outer = Part.makeCylinder(cap_or, cap_h*0.7)
            dome = Part.makeSphere(cap_or, App.Vector(0,0,cap_h*0.7))
            cap_outer = cap_outer.fuse(dome).removeSplitter()
        elif cap_mode == "sport":
            cap_outer = Part.makeCylinder(cap_or*0.95, cap_h)
            spout = Part.makeCylinder(max(4.0, 0.18*cap_or), cap_h*0.6)
            spout.translate(App.Vector(0,0,cap_h*0.4))
            cap_outer = cap_outer.fuse(spout).removeSplitter()
        else:
            cap_outer = Part.makeCylinder(cap_or, cap_h)
        cap_inner = Part.makeCylinder(cap_ir, cap_h - 1.0)
        cap = cap_outer.cut(cap_inner).removeSplitter()
        # fillet bottom rim of cap
        try:
            cap_edges = []
            for e in cap.Edges:
                bb = e.BoundBox
                if abs(bb.ZMin - 0.0) < 0.05:
                    cap_edges.append(e)
            if cap_edges:
                cap = cap.makeFillet(min(2.0, 0.06*cap_or), cap_edges)
        except Exception:
            pass
        cap_obj = doc.addObject("Part::Feature", "BottleCap")
        cap_obj.Shape = cap
        cap_obj.Label = "Cap_{label}"
        cap_obj.Placement.Base = App.Vector(0,0, neck_base_z + neck_h + 0.5)  # sit above neck
except Exception:
    pass

doc.recompute()
try:
    print(f"[DimReport] Bottle target: {V_ml:.1f} ml | OD: {2*R:.2f} mm | H: {height:.2f} mm | wall: {wall} mm | neck_r: {neck_r:.2f} mm")
    # Use .format and escape braces in the outer f-string
    print("[Validity] Outer valid: {{}} , Inner valid: {{}} , Result valid: {{}}".format(outer.isValid(), inner.isValid(), bottle.isValid()))
    try:
        print("[BaseMode] {{}} | bottle ZMin={{:.2f}} ZMax={{:.2f}} | contactZ~0".format(base_mode, bottle.BoundBox.ZMin, bottle.BoundBox.ZMax))
    except Exception:
        pass
    # capacity approximation equals inner (hollow) shape volume
    cap_ml = inner_space.Volume/1000.0
    target_ml = {V_ml}
    print("[Capacity] Approx volume: {{:.1f}} ml (Δ = {{:+.1f}} ml)".format(cap_ml, cap_ml - target_ml))
except Exception:
    pass
""".strip()

@app.post("/api/v1/text-to-cad", response_model=TextToCADResponse)
async def text_to_cad(req: TextToCADRequest, api_key: str = Depends(verify_api_key)):
    text = req.prompt.strip()
    part = parse_prompt(text)
    if not part:
        # Strictly deterministic server: only recognized templates
        return TextToCADResponse(
            prompt=req.prompt,
            engineering_analysis="Unrecognized deterministic template. This sidecar only supports cube/cylinder (and bottle if available).",
            freecad_code="# No-op: unsupported deterministic request",
            metadata={"recognized": False},
            cloud_error=None,
            using_fallback=True,
        )

    params = extract_params(part, text)
    try:
        if part == "cube":
            code = gen_cube_code(params)
        elif part == "cylinder":
            code = gen_cylinder_code(params)
        elif part == "water_bottle":
            code = gen_bottle_code(params)
        else:
            code = "# Unsupported in deterministic sidecar"
        return TextToCADResponse(
            prompt=req.prompt,
            engineering_analysis=f"Deterministic {part} generated with params: {json.dumps(params)}",
            freecad_code=code,
            metadata={"template": part, "params": params},
            cloud_error=None,
            using_fallback=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template render error: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8089))
    uvicorn.run(app, host="0.0.0.0", port=port)
