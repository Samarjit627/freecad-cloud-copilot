"""
Test script for the simple_gearbox module.
This script can be run from within FreeCAD's Python console.
"""

import os
import sys
import traceback

# Define the script directory explicitly since __file__ is not available in FreeCAD console
script_dir = "/Users/samarjit/CascadeProjects/freecad-cloud-copilot"
macro_dir = os.path.join(script_dir, 'macro')
if macro_dir not in sys.path:
    sys.path.append(macro_dir)
    print(f"Added macro directory to path: {macro_dir}")

def test_simple_gearbox():
    """Test the simple_gearbox module"""
    print("Starting simple_gearbox test...")
    
    try:
        import FreeCAD
        print(f"FreeCAD version: {FreeCAD.Version()}")
    except ImportError:
        print("ERROR: FreeCAD modules not available. This script must be run from within FreeCAD.")
        return
    
    # Import the simple_gearbox module
    try:
        import simple_gearbox
        print("Successfully imported simple_gearbox module")
    except ImportError as e:
        print(f"Error importing simple_gearbox: {str(e)}")
        return
    
    # Test creating a gearbox
    try:
        print("\nTesting gearbox creation with ratio 10:1...")
        result = simple_gearbox.create_simple_gearbox(10.0, "NEMA17")
        
        if result and result.get('success'):
            print(f"SUCCESS: {result.get('message', 'Gearbox created successfully')}")
            print(f"Document: {result.get('document').Name if result.get('document') else 'N/A'}")
            if 'specs' in result:
                print(f"Specs: {result.get('specs')}")
        else:
            print(f"FAILED: {result.get('message', 'Unknown error')}")
    
    except Exception as e:
        print(f"Error creating gearbox: {str(e)}")
        traceback.print_exc()
    
    print("\nSimple gearbox test completed.")

# Run the test if executed directly
if __name__ == "__main__":
    test_simple_gearbox()
else:
    # When imported in FreeCAD console
    print("Run test_simple_gearbox() to test the gearbox functionality")
