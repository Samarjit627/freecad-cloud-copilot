#!/usr/bin/env python3
"""
Test script for the fixed enhanced analysis API endpoints.
This script tests both local and deployed endpoints.
"""

import os
import sys
import json
import uuid
import requests
import argparse
from datetime import datetime

# Add the app directory to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

# Try to import the models and integration manager
try:
    from app.models.dfm_models import CADGeometry, BoundingBox, Point3D
    from app.routers.enhanced_analysis_fixed import SimpleIntegrationManager
    LOCAL_IMPORTS = True
except ImportError:
    LOCAL_IMPORTS = False
    print("Warning: Could not import local modules. Only remote API testing will be available.")

# Default API key - replace with your actual key when running
DEFAULT_API_KEY = "your-real-api-key"

# Default endpoint URL - replace with your actual deployed endpoint
DEFAULT_ENDPOINT = "https://freecad-copilot-fixed-4cmxv2m7cq-el.a.run.app"

def create_test_cad_data():
    """Create a test CAD data payload"""
    return {
        "part_name": f"test_part_{uuid.uuid4().hex[:8]}",
        "volume": 125000.0,
        "surface_area": 15000.0,
        "bounding_box": {
            "length": 100.0,
            "width": 50.0,
            "height": 25.0
        },
        "center_of_mass": {
            "x": 50.0,
            "y": 25.0,
            "z": 12.5
        },
        "features": [
            {"type": "hole", "diameter": 10.0, "depth": 25.0},
            {"type": "fillet", "radius": 5.0},
            {"type": "thin_wall", "thickness": 2.0}
        ]
    }

def test_remote_api(endpoint_url, api_key):
    """Test the remote API endpoints"""
    print(f"\n=== Testing Remote API at {endpoint_url} ===\n")
    
    # Test health endpoint
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{endpoint_url}/health")
        if response.status_code == 200:
            print(f"✅ Health check successful: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
    
    # Test v1 analyze endpoint
    print("\nTesting /api/v1/analyze endpoint...")
    payload = {
        "cad_data": create_test_cad_data(),
        "material": "PLA",
        "process": "FDM_PRINTING",
        "production_volume": 100
    }
    
    try:
        response = requests.post(
            f"{endpoint_url}/api/v1/analyze",
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Analysis v1 successful: {response.status_code}")
            print(f"  Status: {result.get('status')}")
            print(f"  Message: {result.get('message')}")
            
            # Validate response data
            data = result.get('data', {})
            required_fields = [
                "analysis_id", "overall_manufacturability_score", 
                "overall_rating", "primary_process"
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
            else:
                print("✅ All required fields present")
                print(f"  Analysis ID: {data.get('analysis_id')}")
                print(f"  Score: {data.get('overall_manufacturability_score')}")
                print(f"  Rating: {data.get('overall_rating')}")
                print(f"  Process: {data.get('primary_process')}")
        else:
            print(f"❌ Analysis v1 failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Analysis v1 error: {str(e)}")
    
    # Test v2 analyze endpoint
    print("\nTesting /api/v2/analyze endpoint...")
    try:
        response = requests.post(
            f"{endpoint_url}/api/v2/analyze",
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Analysis v2 successful: {response.status_code}")
            print(f"  Status: {result.get('status')}")
            print(f"  Message: {result.get('message')}")
            
            # Validate response data
            data = result.get('data', {})
            required_fields = [
                "analysis_id", "overall_manufacturability_score", 
                "overall_rating", "primary_process"
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
            else:
                print("✅ All required fields present")
                print(f"  Analysis ID: {data.get('analysis_id')}")
                print(f"  Score: {data.get('overall_manufacturability_score')}")
                print(f"  Rating: {data.get('overall_rating')}")
                print(f"  Process: {data.get('primary_process')}")
        else:
            print(f"❌ Analysis v2 failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Analysis v2 error: {str(e)}")

def test_local_integration_manager():
    """Test the SimpleIntegrationManager directly"""
    if not LOCAL_IMPORTS:
        print("❌ Cannot test local integration manager: modules not available")
        return
    
    print("\n=== Testing Local Integration Manager ===\n")
    
    try:
        # Create a SimpleIntegrationManager instance
        integration_manager = SimpleIntegrationManager()
        
        # Create a test CAD geometry
        geometry = CADGeometry(
            part_name=f"test_part_{uuid.uuid4().hex[:8]}",
            volume=125000.0,
            surface_area=15000.0,
            bounding_box=BoundingBox(length=100.0, width=50.0, height=25.0),
            center_of_mass=Point3D(x=50.0, y=25.0, z=12.5)
        )
        
        # Create a custom request object
        class CustomRequest:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
                    
            def dict(self):
                return {k: v for k, v in self.__dict__.items()}
        
        # Create a request
        request = CustomRequest(
            cad_geometry=geometry,
            material="PLA",
            target_process="FDM_PRINTING",
            production_volume=100
        )
        
        # Process the request
        print("Processing direct analysis request...")
        response = integration_manager.process_analysis_request(request)
        
        # Check the response
        if response:
            print("✅ Direct analysis successful")
            
            # Check required fields
            required_fields = [
                "analysis_id", "overall_manufacturability_score", 
                "overall_rating", "primary_process"
            ]
            
            missing_fields = [field for field in required_fields if not hasattr(response, field)]
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
            else:
                print("✅ All required fields present")
                print(f"  Analysis ID: {getattr(response, 'analysis_id', None)}")
                print(f"  Score: {getattr(response, 'overall_manufacturability_score', None)}")
                print(f"  Rating: {getattr(response, 'overall_rating', None)}")
                print(f"  Process: {getattr(response, 'primary_process', None)}")
        else:
            print("❌ Direct analysis failed: No response")
    except Exception as e:
        print(f"❌ Direct analysis error: {str(e)}")
        import traceback
        print(traceback.format_exc())

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test the fixed enhanced analysis API")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="API endpoint URL")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="API key")
    parser.add_argument("--local-only", action="store_true", help="Only test local integration manager")
    parser.add_argument("--remote-only", action="store_true", help="Only test remote API")
    
    args = parser.parse_args()
    
    print(f"=== FreeCAD Manufacturing Co-Pilot API Test ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not args.local_only:
        test_remote_api(args.endpoint, args.api_key)
    
    if not args.remote_only and LOCAL_IMPORTS:
        test_local_integration_manager()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
