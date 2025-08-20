"""
cam/path_integration.py

Read-only CAM (Path) integration helpers for FreeCAD.
Phase 0: probe environment and analyze selected part(s) without mutating the document.

This module intentionally avoids creating Path Jobs, Operations, or Toolpaths.
It is safe to import and run in any context. Later phases can add job creation
APIs guarded by feature flags.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CamProbeResult:
    available: bool
    modules: List[str]
    posts: List[str]
    notes: List[str]


@dataclass
class CamAnalyzeResult:
    success: bool
    message: str
    selected_objects: List[str]
    solids: int
    suggestions: List[str]
    candidate_ops: List[Dict[str, Any]]
    warnings: List[str]


def _try_imports() -> Tuple[bool, List[str], List[str], List[str]]:
    modules: List[str] = []
    posts: List[str] = []
    notes: List[str] = []
    try:
        import Path  # type: ignore
        modules.append("Path")
    except Exception as e:
        notes.append(f"Path import failed: {e}")
        return False, modules, posts, notes

    try:
        import PathScripts  # type: ignore
        modules.append("PathScripts")
    except Exception as e:
        notes.append(f"PathScripts import failed: {e}")

    # Try to discover post processors (best-effort; may vary by install)
    try:
        import PathScripts as PS  # type: ignore
        if hasattr(PS, "PostUtils"):
            try:
                posts = list(getattr(PS.PostUtils, "postList", lambda: [])())
            except Exception:
                # Fallback: common defaults
                posts = ["linuxcnc", "grbl", "mach3"]
        else:
            posts = ["linuxcnc", "grbl", "mach3"]
    except Exception:
        posts = ["linuxcnc", "grbl", "mach3"]

    return True, modules, posts, notes


def probe_environment() -> Dict[str, Any]:
    """Probe CAM (Path) availability and list common post processors.

    Returns a plain dict for easy logging/JSON.
    """
    available, modules, posts, notes = _try_imports()
    result = CamProbeResult(
        available=available,
        modules=modules,
        posts=posts,
        notes=notes,
    )
    return asdict(result)


# Helpers to introspect a FreeCAD document safely

def _get_active_doc():
    try:
        import FreeCAD
        return FreeCAD.ActiveDocument
    except Exception:
        return None


def _collect_solid_objects(doc, obj_names: Optional[List[str]] = None) -> Tuple[List[Any], List[str], List[str]]:
    solids = []
    names: List[str] = []
    warnings: List[str] = []
    if not doc:
        return solids, names, ["No active document"]

    candidates = []
    if obj_names:
        for n in obj_names:
            obj = getattr(doc, n, None)
            if obj is not None:
                candidates.append(obj)
            else:
                warnings.append(f"Object not found: {n}")
    else:
        candidates = list(getattr(doc, "Objects", []) or [])

    for obj in candidates:
        try:
            shape = getattr(obj, "Shape", None)
            if shape and hasattr(shape, "Solids") and len(shape.Solids) > 0:
                solids.append(obj)
                names.append(getattr(obj, "Name", "<unnamed>"))
        except Exception:
            continue

    if not solids:
        warnings.append("No solid objects detected in selection/document")
    return solids, names, warnings


def analyze_part(doc=None, obj_names: Optional[List[str]] = None, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Analyze selected solids and suggest CAM operations without modifying the document.

    - Identifies solids
    - Suggests basic operations: Profile, Pocket, Drilling based on simple heuristics
    - Estimates a starter workflow (Job -> Setup -> Ops) in a textual form
    """
    if options is None:
        options = {}

    env = probe_environment()
    if not env.get("available", False):
        return asdict(CamAnalyzeResult(
            success=False,
            message="CAM (Path) modules are not available in this FreeCAD session.",
            selected_objects=[],
            solids=0,
            suggestions=[],
            candidate_ops=[],
            warnings=env.get("notes", []),
        ))

    if doc is None:
        doc = _get_active_doc()

    solids, names, warnings = _collect_solid_objects(doc, obj_names)
    suggestions: List[str] = []
    ops: List[Dict[str, Any]] = []

    # Heuristics (very light, non-invasive)
    try:
        for obj in solids:
            shape = getattr(obj, "Shape", None)
            if not shape:
                continue

            faces = getattr(shape, "Faces", [])
            planar = 0
            circular = 0
            for f in faces:
                try:
                    surf = f.Surface
                    if getattr(surf, "typeId", "").lower().startswith("plane"):
                        planar += 1
                    # poor-man circular hole detection
                    # faces with single closed wire made of circle edges
                    edges = list(getattr(f, "Edges", []) or [])
                    if edges and all(getattr(e.Curve, "typeId", "").lower().startswith("circle") for e in edges if hasattr(e, "Curve")):
                        circular += 1
                except Exception:
                    continue

            if planar > 0:
                suggestions.append(f"{obj.Name}: Planar faces detected -> candidate for Pocket/Face milling")
                ops.append({
                    "type": "Pocket",
                    "target": obj.Name,
                    "strategy": "ZLevel",
                    "note": f"{planar} planar faces detected",
                })

            if circular > 0:
                suggestions.append(f"{obj.Name}: Circular features detected -> candidate for Drilling")
                ops.append({
                    "type": "Drilling",
                    "target": obj.Name,
                    "note": f"~{circular} circular regions detected",
                })

            # Outer profile is common
            suggestions.append(f"{obj.Name}: External contour -> candidate for Profile")
            ops.append({
                "type": "Profile",
                "target": obj.Name,
                "side": "Outside",
            })
    except Exception as e:
        warnings.append(f"Heuristic scan error: {e}")

    msg = "CAM analysis complete (read-only)."
    return asdict(CamAnalyzeResult(
        success=True,
        message=msg,
        selected_objects=names,
        solids=len(solids),
        suggestions=suggestions,
        candidate_ops=ops,
        warnings=warnings,
    ))
