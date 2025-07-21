#!/usr/bin/env python3
"""
Standalone DFM test that doesn't require FastAPI
"""

class DFMViolation:
    def __init__(self, rule, message, severity):
        self.rule = rule
        self.message = message
        self.severity = severity

class DFMOutput:
    def __init__(self, part_name, violations):
        self.part_name = part_name
        self.violations = violations

def check_dfm_standalone(part_name, material, min_wall_thickness_mm, 
                        fillet_radius_mm=None, draft_angle_deg=None, 
                        has_undercuts=False):
    """
    Standalone version of the DFM check function that doesn't require FastAPI
    """
    violations = []

    if min_wall_thickness_mm < 1.0:
        violations.append(DFMViolation(
            rule="Minimum Wall Thickness",
            message=f"Wall thickness {min_wall_thickness_mm}mm is below the 1.0mm recommended minimum.",
            severity="critical"
        ))

    if fillet_radius_mm is not None and fillet_radius_mm < 0.5:
        violations.append(DFMViolation(
            rule="Fillet Radius",
            message=f"Fillet radius {fillet_radius_mm}mm is too small for typical machining.",
            severity="warning"
        ))

    if draft_angle_deg is not None and draft_angle_deg < 1.0:
        violations.append(DFMViolation(
            rule="Draft Angle",
            message=f"Draft angle {draft_angle_deg}° is insufficient for mold release.",
            severity="warning"
        ))

    if has_undercuts:
        violations.append(DFMViolation(
            rule="Undercuts",
            message="Part contains undercuts that complicate tooling.",
            severity="warning"
        ))

    return DFMOutput(part_name=part_name, violations=violations)

def main():
    """Test the standalone DFM check function"""
    print("DFM Standalone Test")
    print("-" * 50)
    
    # Test parameters
    part_name = "TestCylinder"
    material = "ABS"
    min_wall_thickness = 0.8  # Below recommended 1.0mm to trigger violation
    fillet_radius = 0.3       # Below recommended 0.5mm to trigger violation
    draft_angle = 0.5         # Below recommended 1.0° to trigger violation
    has_undercuts = True      # Will trigger undercut violation
    
    print(f"Testing part: {part_name}")
    print(f"Material: {material}")
    print(f"Wall thickness: {min_wall_thickness}mm")
    print(f"Fillet radius: {fillet_radius}mm")
    print(f"Draft angle: {draft_angle}°")
    print(f"Has undercuts: {has_undercuts}")
    print("-" * 50)
    
    # Run the DFM check
    result = check_dfm_standalone(
        part_name=part_name,
        material=material,
        min_wall_thickness_mm=min_wall_thickness,
        fillet_radius_mm=fillet_radius,
        draft_angle_deg=draft_angle,
        has_undercuts=has_undercuts
    )
    
    # Display the results
    print("\nDFM Analysis Results:")
    print(f"Part: {result.part_name}")
    print("\nViolations:")
    
    if not result.violations:
        print("✅ No manufacturability issues detected!")
    else:
        for v in result.violations:
            emoji = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(v.severity, "")
            print(f"{emoji} {v.rule}: {v.message}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()
