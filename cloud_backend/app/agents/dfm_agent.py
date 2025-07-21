from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class DFMInput(BaseModel):
    part_name: str
    material: str
    min_wall_thickness_mm: float
    fillet_radius_mm: Optional[float] = None
    draft_angle_deg: Optional[float] = None
    has_undercuts: Optional[bool] = False

class DFMViolation(BaseModel):
    rule: str
    message: str
    severity: str  # e.g., "warning", "critical"

class DFMOutput(BaseModel):
    part_name: str
    violations: List[DFMViolation]

@router.post("/dfm/check", response_model=DFMOutput)
def check_dfm(input: DFMInput):
    violations = []

    if input.min_wall_thickness_mm < 1.0:
        violations.append(DFMViolation(
            rule="Minimum Wall Thickness",
            message=f"Wall thickness {input.min_wall_thickness_mm}mm is below the 1.0mm recommended minimum.",
            severity="critical"
        ))

    if input.fillet_radius_mm is not None and input.fillet_radius_mm < 0.5:
        violations.append(DFMViolation(
            rule="Fillet Radius",
            message=f"Fillet radius {input.fillet_radius_mm}mm is too small for typical machining.",
            severity="warning"
        ))

    if input.draft_angle_deg is not None and input.draft_angle_deg < 1.0:
        violations.append(DFMViolation(
            rule="Draft Angle",
            message=f"Draft angle {input.draft_angle_deg}° is insufficient for mold release.",
            severity="warning"
        ))

    if input.has_undercuts:
        violations.append(DFMViolation(
            rule="Undercuts",
            message="Part contains undercuts that complicate tooling.",
            severity="warning"
        ))

    return DFMOutput(part_name=input.part_name, violations=violations)
