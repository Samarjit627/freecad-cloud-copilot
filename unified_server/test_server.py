#!/usr/bin/env python3
"""
Test script for the FreeCAD Manufacturing Co-Pilot Unified Server
Tests both DFM Analysis and Text-to-CAD endpoints
"""

import requests
import json
import sys
import time

# Configuration
BASE_URL = "http://localhost:8090"
API_KEY = "test-api-key"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def test_health():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check Endpoint ===")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Health check successful")
            return True
        else:
            print("❌ Health check failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_dfm_analysis():
    """Test the DFM analysis endpoint"""
    print("\n=== Testing DFM Analysis Endpoint ===")
    
    # Sample request data
    data = {
        "user_requirements": {
            "material": "PLA",
            "target_process": "fdm_printing",
            "production_volume": 100,
            "use_advanced_dfm": True
        },
        "cad_data": {
            "geometry": {
                "volume_cm3": 125.0,
                "surface_area_cm2": 250.0,
                "min_wall_thickness": 0.8,
                "min_feature_size": 0.3,
                "overhangs": True
            },
            "features": [
                {
                    "type": "hole",
                    "diameter": 5.0,
                    "depth": 10.0
                },
                {
                    "type": "fillet",
                    "radius": 2.0
                }
            ],
            "metadata": {
                "volume_cm3": 125.0,
                "name": "test_part",
                "units": "mm"
            }
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/v2/analyze",
            headers=HEADERS,
            json=data
        )
        elapsed_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print("\nManufacturability Score:", result.get("manufacturability_score"))
            print(f"Issues Found: {len(result.get('issues', []))}")
            print(f"Recommendations: {len(result.get('recommendations', []))}")
            print(f"Cost Estimate: ${result.get('cost_estimate', {}).get('unit_cost', 0):.2f} per unit")
            print(f"Lead Time: {result.get('lead_time', {}).get('typical_days', 0)} days")
            print("✅ DFM Analysis test successful")
            return True
        else:
            print(f"❌ DFM Analysis test failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_text_to_cad():
    """Test the Text-to-CAD endpoint"""
    print("\n=== Testing Text-to-CAD Endpoint ===")
    
    # Sample request data
    data = {
        "prompt": "Create a simple bracket with two mounting holes that can hold a 40mm fan",
        "parameters": {
            "detail_level": "medium",
            "output_format": "freecad_python"
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/v1/text-to-cad",
            headers=HEADERS,
            json=data
        )
        elapsed_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print("\nPrompt:", result.get("prompt"))
            
            # Print engineering analysis (first 100 chars)
            analysis = result.get("engineering_analysis", "")
            print(f"Engineering Analysis: {analysis[:100]}...")
            
            # Print FreeCAD code (first 100 chars)
            code = result.get("freecad_code", "")
            print(f"FreeCAD Code: {code[:100]}...")
            
            # Print code length
            print(f"Code Length: {len(code)} characters")
            
            print("✅ Text-to-CAD test successful")
            return True
        else:
            print(f"❌ Text-to-CAD test failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function to run all tests"""
    print("=== FreeCAD Manufacturing Co-Pilot Unified Server Tests ===")
    
    # Run tests
    health_ok = test_health()
    dfm_ok = test_dfm_analysis()
    text_to_cad_ok = test_text_to_cad()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"DFM Analysis: {'✅ PASS' if dfm_ok else '❌ FAIL'}")
    print(f"Text-to-CAD: {'✅ PASS' if text_to_cad_ok else '❌ FAIL'}")
    
    # Return exit code
    if health_ok and dfm_ok and text_to_cad_ok:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
