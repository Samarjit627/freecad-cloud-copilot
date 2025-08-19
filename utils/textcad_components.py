#!/usr/bin/env python3
"""
Text-to-CAD component recipes (non-invasive helpers)
- Detects target component from user prompt
- Builds a stricter prompt with generation constraints for robust FreeCAD code

Safe by default: if anything fails, caller falls back to original prompt.
"""
from __future__ import annotations
from typing import Optional
import re

# Component IDs
ALLOY_WHEEL = "alloy_wheel"
BRAKE_ROTOR = "brake_rotor"

# Simple keyword maps
_COMPONENT_KEYWORDS = {
    ALLOY_WHEEL: [r"alloy\s*wheel", r"\brim\b", r"wheel rim", r"car\s*wheel", r"wheel\b"],
    BRAKE_ROTOR: [r"disc\s*brake", r"brake\s*rotor", r"brake\s*disc"],
}


def detect_component(prompt: str) -> Optional[str]:
    """Return a component id if the prompt clearly targets one of our recipes."""
    try:
        if not prompt:
            return None
        low = prompt.lower()
        for comp, patterns in _COMPONENT_KEYWORDS.items():
            for pat in patterns:
                if re.search(pat, low):
                    return comp
        return None
    except Exception:
        return None


def _wheel_recipe_block() -> str:
    return (
        "Generate FreeCAD Python code to model a parametric alloy wheel (automotive rim).\n"
        "Hard requirements:\n"
        "- Use Part/PartDesign primitives, sketches, revolve, polar patterns. Units in mm.\n"
        "- Parameters (with safe defaults if missing): rim_diameter_mm (e.g., 432=17in), rim_width_mm (178=7in), center_bore_mm (66.6), pcd_count (5), pcd_dia_mm (114.3), offset_mm (35), spokes_count (5..10), spoke_style ('straight' or 'y').\n"
        "- Method: revolve rim barrel profile; create hub/hat; create one spoke sketch/profile and make polar pattern (spokes_count); cut bolt circle holes (pcd_count at pcd_dia_mm); add small fillets/chamfers; fuse to a single solid.\n"
        "- Do not use external files, images, or network. No os/subprocess/requests.\n"
        "- Recompute and ensure result is visible in the active document.\n"
        "- Name the main object 'AlloyWheel'.\n"
    )


def _rotor_recipe_block() -> str:
    return (
        "Generate FreeCAD Python code to model a parametric brake rotor (disc).\n"
        "Hard requirements:\n"
        "- Use Part primitives and sketch cuts. Units in mm.\n"
        "- Parameters (with safe defaults if missing): outer_dia_mm (280), inner_dia_mm (72), thickness_mm (25), pcd_count (5), pcd_dia_mm (114.3), vent_holes_count (20), vent_hole_dia_mm (6), slot_count (0 or 6).\n"
        "- Method: create annulus by subtracting cylinder (inner) from outer; add bolt circle holes; pattern vent holes (polar); optional slots as sketch cuts; chamfer edges.\n"
        "- Recompute and ensure visibility; name main object 'BrakeRotor'.\n"
        "- No external I/O or network.\n"
    )


def build_component_prompt(base_prompt: str, component_id: Optional[str]) -> str:
    """Append strict recipe constraints to the prompt if a known component is requested."""
    try:
        if not component_id:
            return base_prompt
        if component_id == ALLOY_WHEEL:
            return f"{base_prompt}\n\nConstraints:\n{_wheel_recipe_block()}"
        if component_id == BRAKE_ROTOR:
            return f"{base_prompt}\n\nConstraints:\n{_rotor_recipe_block()}"
        return base_prompt
    except Exception:
        return base_prompt


# --- Parameter parsing helpers -------------------------------------------------
def _extract_number_list(text: str) -> list:
    return [float(x) for x in re.findall(r"\d+\.\d+|\d+", text or "")]

def parse_alloy_wheel_params(prompt: str) -> dict:
    """Extract common alloy wheel params from a natural prompt.
    Returns dict with mm units where applicable.
    """
    try:
        p = (prompt or "").lower()
        out = {}
        # Diameter x width like 17x7 or 17 x 7 inch
        m = re.search(r"(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)\s*(in|inch|inches)?", p)
        if m:
            dia_in = float(m.group(1))
            wid_in = float(m.group(2))
            out['rim_diameter_mm'] = round(dia_in * 25.4, 1)
            out['rim_width_mm'] = round(wid_in * 25.4, 1)
        # PCD like 5x114.3
        m = re.search(r"(\d+)\s*[xX]\s*(\d+(?:\.\d+)?)\s*(mm)?", p)
        if m:
            out['pcd_count'] = int(m.group(1))
            out['pcd_dia_mm'] = float(m.group(2))
        # Center bore
        m = re.search(r"center\s*bore\s*(\d+(?:\.\d+)?)\s*mm", p)
        if m:
            out['center_bore_mm'] = float(m.group(1))
        # Offset
        m = re.search(r"offset\s*(\d+(?:\.\d+)?)\s*mm", p)
        if m:
            out['offset_mm'] = float(m.group(1))
        # Spokes
        m = re.search(r"(\d+)\s*-?\s*spoke", p)
        if m:
            out['spokes_count'] = int(m.group(1))
        if 'y' in p and 'spoke' in p:
            out['spoke_style'] = 'y'
        elif 'straight' in p and 'spoke' in p:
            out['spoke_style'] = 'straight'
        return out
    except Exception:
        return {}
