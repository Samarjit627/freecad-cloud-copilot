#!/usr/bin/env python3
"""
Direct test for DFM agent functionality without starting the FastAPI server
"""

# Import the DFM agent models and function directly
from app.agents.dfm_agent import DFMInput, DFMOutput, check_dfm

def test_dfm_direct():
    """Test the DFM check function directly"""
    print("Testing DFM agent directly...")
    
    # Create a test input
    test_input = DFMInput(
        part_name="TestCylinder",
        material="ABS",
        min_wall_thickness_mm=0.8,  # Below recommended 1.0mm to trigger violation
        fillet_radius_mm=0.3,       # Below recommended 0.5mm to trigger violation
        draft_angle_deg=0.5,        # Below recommended 1.0° to trigger violation
        has_undercuts=True          # Will trigger undercut violation
    )
    
    # Call the function directly
    print(f"Input: {test_input}")
    result = check_dfm(test_input)
    
    # Format and display the result
    print("\nDFM Analysis Result:")
    print(f"Part: {result.part_name}")
    print("\nViolations:")
    
    if not result.violations:
        print("✅ No manufacturability issues detected!")
    else:
        for v in result.violations:
            emoji = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(v.severity, "")
            print(f"{emoji} {v.rule}: {v.message}")
    
    return result

if __name__ == "__main__":
    print("DFM Agent Direct Test")
    print("-" * 50)
    
    result = test_dfm_direct()
    
    print("\nTest completed!")
