#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for the CAD analyzer module.
This script can be run from within FreeCAD to test the analyzer functionality.
"""

import os
import sys
import FreeCAD
import FreeCADGui

# Add project directory to path
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

# Import our modules
from analysis import CADAnalyzer, FeatureVisualizer

def test_analyzer():
    """Test the CAD analyzer with the active document"""
    # Check if there's an active document
    if not FreeCAD.ActiveDocument:
        print("No active document. Please open a CAD model first.")
        return False
    
    print("Starting CAD analysis...")
    
    # Create analyzer
    analyzer = CADAnalyzer(FreeCAD.ActiveDocument)
    
    # Run analysis
    try:
        results = analyzer.analyze()
        print("Analysis complete!")
        
        # Print basic results
        print("\n=== Basic Metadata ===")
        print(f"Part name: {results['metadata'].get('name', 'Unknown')}")
        print(f"Volume: {results['metadata'].get('volume', 0):.2f} cm³")
        print(f"Surface area: {results['metadata'].get('surface_area', 0):.2f} cm²")
        dimensions = results['metadata'].get('dimensions', [0, 0, 0])
        print(f"Dimensions: {dimensions[0]:.2f} × {dimensions[1]:.2f} × {dimensions[2]:.2f} mm")
        
        # Print feature counts
        print("\n=== Feature Counts ===")
        print(f"Holes: {len(results['features']['holes'])}")
        print(f"Fillets: {len(results['features']['fillets'])}")
        print(f"Chamfers: {len(results['features']['chamfers'])}")
        print(f"Ribs: {len(results['features']['ribs'])}")
        
        # Print wall thickness if available
        if 'min_wall_thickness' in results['metadata']:
            print("\n=== Wall Thickness ===")
            print(f"Minimum: {results['metadata']['min_wall_thickness']:.2f} mm")
            print(f"Maximum: {results['metadata']['max_wall_thickness']:.2f} mm")
            print(f"Average: {results['metadata']['avg_wall_thickness']:.2f} mm")
        
        # Create visualizer
        print("\n=== Creating Visualizations ===")
        visualizer = FeatureVisualizer(FreeCAD.ActiveDocument, analyzer)
        
        # Show wall thickness
        print("Showing wall thickness visualization...")
        visualizer.show_wall_thickness()
        
        print("\nTest completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_analyzer()
