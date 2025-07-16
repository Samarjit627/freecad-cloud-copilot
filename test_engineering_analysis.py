#!/usr/bin/env python
"""
Test script for the engineering analysis functionality in the FreeCAD Manufacturing Co-Pilot macro.
This script can be run directly to test the engineering analysis functionality without the FreeCAD UI.
"""

import os
import sys
import json
import traceback

# Add macro directory to path
MACRO_DIR = os.path.dirname(os.path.realpath(__file__))
if MACRO_DIR not in sys.path:
    sys.path.append(MACRO_DIR)

# Try to import FreeCAD
try:
    import FreeCAD
    import Part
except ImportError:
    print("Error: FreeCAD module not found. This script must be run with FreeCAD's Python interpreter.")
    print("Try running: freecadcmd test_engineering_analysis.py")
    sys.exit(1)

# Import our modules
try:
    from macro import cloud_cad_analyzer
    from macro import engineering_analyzer
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure all required files are in the macro directory.")
    sys.exit(1)

def create_test_document():
    """Create a simple test document with a box shape"""
    doc = FreeCAD.newDocument("TestDocument")
    
    # Create a box
    box = doc.addObject("Part::Box", "Box")
    box.Length = 100
    box.Width = 50
    box.Height = 25
    
    # Add some fillets to test feature detection
    try:
        # Create a second box with fillets
        box2 = doc.addObject("Part::Box", "BoxWithFillets")
        box2.Length = 80
        box2.Width = 40
        box2.Height = 20
        box2.Placement.Base = FreeCAD.Vector(150, 0, 0)
        
        # Add fillets to the box edges
        fillet = doc.addObject("Part::Fillet", "Fillet")
        fillet.Base = box2
        edges = []
        for i in range(1, 13):  # 12 edges in a box
            edges.append((i, 5.0, 5.0))  # (edge_index, radius, radius)
        fillet.Edges = edges
    except Exception as e:
        print(f"Warning: Could not create fillets: {e}")
    
    doc.recompute()
    return doc

def run_test():
    """Run the engineering analysis test"""
    print("\n=== ENGINEERING ANALYSIS TEST ===\n")
    
    try:
        # Create test document
        print("Creating test document...")
        doc = create_test_document()
        
        # Get the analyzer
        analyzer = cloud_cad_analyzer.get_analyzer()
        
        # Run engineering analysis only
        print("\nRunning engineering analysis...")
        result = analyzer.analyze_engineering_only(doc)
        
        # Print results
        print("\nEngineering Analysis Results:")
        print(json.dumps(result, indent=2, default=str))
        
        # Test visualization
        print("\nTesting visualization...")
        analyzer.run_engineering_analysis(doc, visualize=True)
        
        print("\n=== TEST COMPLETED SUCCESSFULLY ===\n")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        traceback.print_exc()
        print("\n=== TEST FAILED ===\n")

if __name__ == "__main__":
    run_test()
