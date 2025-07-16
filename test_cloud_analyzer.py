#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for the cloud-based CAD analyzer with fallback mechanism
Run this script from within FreeCAD to test the cloud analyzer functionality
"""

import os
import sys
import time
import json

# Add the project directory to the Python path
script_dir = os.path.dirname(os.path.realpath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

# Try to import FreeCAD modules
try:
    import FreeCAD
    import Part
except ImportError:
    print("Error: Cannot import FreeCAD modules. This script must be run from within FreeCAD.")
    sys.exit(1)

# Import the cloud CAD analyzer and local analyzer
try:
    from macro import cloud_cad_analyzer
    from macro import local_cad_analyzer
    from macro import cloud_client
    from macro import config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure all required files are in the correct directories.")
    sys.exit(1)

def create_test_document():
    """Create a test document with some basic shapes for testing"""
    doc = FreeCAD.newDocument("TestModel")
    
    # Create a box
    box = doc.addObject("Part::Box", "Box")
    box.Length = 100.0
    box.Width = 50.0
    box.Height = 25.0
    
    # Create a cylinder
    cylinder = doc.addObject("Part::Cylinder", "Cylinder")
    cylinder.Radius = 20.0
    cylinder.Height = 50.0
    cylinder.Placement.Base = FreeCAD.Vector(150, 0, 0)
    
    # Create a sphere
    sphere = doc.addObject("Part::Sphere", "Sphere")
    sphere.Radius = 25.0
    sphere.Placement.Base = FreeCAD.Vector(0, 100, 0)
    
    # Create a cone
    cone = doc.addObject("Part::Cone", "Cone")
    cone.Radius1 = 20.0
    cone.Radius2 = 10.0
    cone.Height = 30.0
    cone.Placement.Base = FreeCAD.Vector(100, 100, 0)
    
    # Recompute the document
    doc.recompute()
    
    return doc

def test_cloud_analyzer():
    """Test the cloud-based CAD analyzer with fallback mechanism"""
    print("\n===== TESTING CLOUD-BASED CAD ANALYZER WITH FALLBACK =====")
    
    # Check cloud connection
    client = cloud_client.get_client()
    print(f"Cloud URL: {config.CLOUD_API_URL}")
    print(f"Connected: {client.connected}")
    
    # Create a test document if no document is open
    if not FreeCAD.ActiveDocument:
        print("Creating test document...")
        doc = create_test_document()
    else:
        doc = FreeCAD.ActiveDocument
        print(f"Using active document: {doc.Name}")
    
    # Initialize the cloud analyzer
    analyzer = cloud_cad_analyzer.get_analyzer()
    
    # Extract basic metadata (local operation)
    print("\nExtracting basic metadata locally...")
    metadata = analyzer._extract_basic_metadata(doc)
    print("Basic metadata:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    
    # Test the local analyzer directly
    print("\n===== TESTING LOCAL CAD ANALYZER =====")
    local_analyzer = local_cad_analyzer.get_analyzer()
    local_result = local_analyzer.analyze_document(doc)
    print("Local analysis result type:", local_result.get("analysis_type", "unknown"))
    print("Local analysis features detected:", len(local_result.get("features", {}).get("detected_features", [])))
    
    # Test the cloud analyzer with fallback
    print("\n===== TESTING CLOUD ANALYZER WITH FALLBACK =====")
    print("This will attempt cloud analysis first, then fall back to local if cloud fails")
    result = analyzer.analyze_document(doc)
    
    # Print analysis results
    print(f"\nAnalysis type: {result.get('analysis_type', 'unknown')}")
    
    if result.get('analysis_type') == 'local':
        print("Fallback to local analysis was triggered!")
        if 'cloud_error' in result:
            print(f"Cloud error: {result['cloud_error']}")
    
    # Print some key results
    if 'features' in result:
        features = result['features']
        print("\nDetected Features:")
        print(f"  Holes: {len(features.get('holes', []))}")
        print(f"  Fillets: {len(features.get('fillets', []))}")
        print(f"  Chamfers: {len(features.get('chamfers', []))}")
        print(f"  Ribs: {len(features.get('ribs', []))}")
        print(f"  Other detected features: {len(features.get('detected_features', []))}")
    
    # Save the result to a JSON file for inspection
    with open('analysis_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("\nAnalysis result saved to analysis_result.json")
    
    return True

def test_force_local_fallback():
    """Test forcing the local fallback by simulating a cloud error"""
    print("\n===== TESTING FORCED LOCAL FALLBACK =====")
    
    # Create a test document if no document is open
    if not FreeCAD.ActiveDocument:
        print("Creating test document...")
        doc = create_test_document()
    else:
        doc = FreeCAD.ActiveDocument
        print(f"Using active document: {doc.Name}")
    
    # Temporarily modify the cloud URL to force a connection error
    original_url = config.CLOUD_API_URL
    config.CLOUD_API_URL = "https://nonexistent-service-url.example.com"
    
    try:
        # Initialize a new cloud client with the bad URL
        client = cloud_client.CloudApiClient(config.CLOUD_API_URL, config.CLOUD_API_KEY)
        
        # Initialize the cloud analyzer with this client
        analyzer = cloud_cad_analyzer.CloudCADAnalyzer()
        analyzer.cloud_client = client
        
        print("Testing with invalid cloud URL to force fallback...")
        start_time = time.time()
        result = analyzer.analyze_document(doc)
        end_time = time.time()
        
        print(f"Analysis completed in {end_time - start_time:.2f} seconds")
        print(f"Analysis type: {result.get('analysis_type', 'unknown')}")
        
        if result.get('analysis_type') == 'local':
            print("✅ Successfully fell back to local analysis when cloud was unavailable")
            if 'cloud_error' in result:
                print(f"Cloud error: {result['cloud_error']}")
            return True
        else:
            print("❌ Failed to fall back to local analysis")
            return False
            
    finally:
        # Restore the original URL
        config.CLOUD_API_URL = original_url

def main():
    """Main function to run all tests"""
    print("\n===== FREECAD CLOUD ANALYZER TEST SUITE =====")
    print(f"Cloud URL: {config.CLOUD_API_URL}")
    
    # Test the cloud analyzer with fallback
    test_cloud_analyzer()
    
    # Test forced local fallback
    test_force_local_fallback()
    
    print("\n===== ALL TESTS COMPLETED =====")

if __name__ == "__main__":
    main()
