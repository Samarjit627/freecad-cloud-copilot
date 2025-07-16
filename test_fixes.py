#!/usr/bin/env python3
"""
Test script to verify fixes to cloud analyzer fallback mechanism
"""

import sys
import os
import json
from typing import Dict, Any

# Add the macro directory to the path
macro_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "macro")
sys.path.append(macro_dir)

# Create mock modules for dependencies that might be missing
class MockModule:
    def __init__(self, name):
        self.__name__ = name
        
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

# Mock FreeCAD and related modules if not available
try:
    import FreeCAD
except ImportError:
    sys.modules['FreeCAD'] = MockModule('FreeCAD')
    sys.modules['Part'] = MockModule('Part')
    sys.modules['Mesh'] = MockModule('Mesh')
    sys.modules['MeshPart'] = MockModule('MeshPart')

# Mock requests if not available
try:
    import requests
except ImportError:
    class MockRequests:
        def __init__(self):
            pass
            
        def get(self, *args, **kwargs):
            class MockResponse:
                status_code = 404
                text = "Not Found"
                
                def json(self):
                    return {"error": "Not Found"}
                    
            return MockResponse()
            
        def post(self, *args, **kwargs):
            class MockResponse:
                status_code = 404
                text = "Not Found"
                
                def json(self):
                    return {"error": "Not Found"}
                    
            return MockResponse()
    
    sys.modules['requests'] = MockRequests()

# Now import our modules
from cloud_client import CloudApiClient
from cloud_cad_analyzer import CloudCADAnalyzer, get_analyzer
from local_cad_analyzer import LocalCADAnalyzer

def test_cloud_client_fallback():
    """Test the cloud client fallback mechanism"""
    print("\n===== Testing Cloud Client Fallback =====")
    
    # Create a cloud client
    client = CloudApiClient(api_url="https://example.com/api", api_key="test_key")
    
    # Test connection
    print(f"\nTesting connection to {client.api_url}...")
    connected = client.test_connection()
    print(f"Connected: {connected}")
    
    # Create sample data for analysis
    metadata = {
        "name": "Test Part",
        "object_count": 1,
        "x_length": 100.0,
        "y_length": 50.0,
        "z_length": 25.0,
        "volume": 125000.0,
        "surface_area": 15000.0
    }
    
    geometry_data = {
        "vertices": [[0, 0, 0], [100, 0, 0], [100, 50, 0], [0, 50, 0], 
                     [0, 0, 25], [100, 0, 25], [100, 50, 25], [0, 50, 25]],
        "faces": [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], 
                  [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    }
    
    # Test cloud analysis with fallback
    print("\n----- Testing cloud analysis with fallback -----")
    try:
        print("Attempting direct cloud analysis (expecting failure)...")
        result = client.analyze_cad(metadata, geometry_data)
        print("Unexpected success! Cloud analysis worked:")
        print(json.dumps(result, indent=2))
        print(f"Used endpoint: {client.last_successful_endpoint}")
    except Exception as e:
        print(f"Expected failure: {str(e)}")
        
        # Now test with the cloud analyzer that has fallback
        print("\n----- Testing cloud analyzer with fallback -----")
        analyzer = get_analyzer()
        
        # Create a mock document for testing
        class MockDocument:
            def __init__(self, name):
                self.Name = name
                self.Objects = []
                
            def getBoundBox(self):
                class BoundBox:
                    def __init__(self):
                        self.XLength = 100.0
                        self.YLength = 50.0
                        self.ZLength = 25.0
                return BoundBox()
                
        mock_doc = MockDocument("TestPart")
        
        # Test analyze_document
        print("Testing analyze_document with fallback...")
        result = analyzer.analyze_document(mock_doc)
        
        # Print results
        print("\nAnalysis result:")
        print(f"Analysis type: {result.get('analysis_type', 'unknown')}")
        
        if "cloud_error" in result:
            print(f"Cloud error: {result['cloud_error']}")
            
        if "note" in result:
            print(f"Note: {result['note']}")
            
        print("\nMetadata:")
        if "metadata" in result:
            for key, value in result["metadata"].items():
                print(f"  {key}: {value}")
                
        print("\nFeatures:")
        if "features" in result:
            for key, value in result["features"].items():
                if isinstance(value, list):
                    print(f"  {key}: {len(value)} items")
                else:
                    print(f"  {key}: {value}")
        
        return result

if __name__ == "__main__":
    test_cloud_client_fallback()
