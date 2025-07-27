#!/usr/bin/env python3
"""
Comprehensive Test Script for FreeCAD Manufacturing Co-Pilot Unified Server
Tests both DFM analysis and Text-to-CAD endpoints
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8091"  # Local proxy server
API_KEY = "test-api-key"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def print_json(data):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=2))

def test_health():
    """Test the health endpoint"""
    print_section("Testing Health Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print_json(response.json())
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_dfm_analysis():
    """Test the DFM analysis endpoint"""
    print_section("Testing DFM Analysis Endpoint")
    
    # Sample DFM analysis request
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
                {"type": "hole", "diameter": 5.0, "depth": 10.0},
                {"type": "fillet", "radius": 2.0}
            ],
            "metadata": {
                "volume_cm3": 125.0,
                "name": "test_part",
                "units": "mm"
            }
        }
    }
    
    try:
        print("Sending request to /api/v2/analyze...")
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/v2/analyze", headers=HEADERS, json=data)
        elapsed_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print_json(result)
            
            # Verify key elements in the response
            print("\nVerification:")
            print(f"- Manufacturability Score: {result.get('manufacturability_score', 'Missing')}")
            print(f"- Issues Count: {len(result.get('issues', []))}")
            print(f"- Recommendations Count: {len(result.get('recommendations', []))}")
            print(f"- Cost Estimate Present: {'Yes' if 'cost_estimate' in result else 'No'}")
            print(f"- Lead Time Present: {'Yes' if 'lead_time' in result else 'No'}")
            print(f"- Using Fallback: {result.get('using_fallback', 'Unknown')}")
            
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_text_to_cad():
    """Test the Text-to-CAD endpoint"""
    print_section("Testing Text-to-CAD Endpoint")
    
    # Sample Text-to-CAD request
    data = {
        "prompt": "Create a simple bracket with two mounting holes that can hold a 40mm fan",
        "parameters": {
            "detail_level": "medium",
            "output_format": "freecad_python"
        }
    }
    
    try:
        print("Sending request to /api/v1/text-to-cad...")
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/v1/text-to-cad", headers=HEADERS, json=data)
        elapsed_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {elapsed_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            
            # Print key parts of the response
            print("\nPrompt:")
            print(result.get("prompt", "Missing"))
            
            print("\nEngineering Analysis (excerpt):")
            analysis = result.get("engineering_analysis", "Missing")
            print(analysis[:200] + "..." if len(analysis) > 200 else analysis)
            
            print("\nFreeCAD Code (excerpt):")
            code = result.get("freecad_code", "Missing")
            print(code[:200] + "..." if len(code) > 200 else code)
            
            print("\nMetadata:")
            print_json(result.get("metadata", {}))
            
            print(f"\nUsing Fallback: {result.get('using_fallback', 'Unknown')}")
            
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

def main():
    """Run all tests"""
    print_section("FreeCAD Manufacturing Co-Pilot Unified Server Test")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    
    # Run tests
    health_ok = test_health()
    dfm_ok = test_dfm_analysis()
    text_to_cad_ok = test_text_to_cad()
    
    # Summary
    print_section("Test Summary")
    print(f"Health Endpoint: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"DFM Analysis Endpoint: {'✅ PASS' if dfm_ok else '❌ FAIL'}")
    print(f"Text-to-CAD Endpoint: {'✅ PASS' if text_to_cad_ok else '❌ FAIL'}")
    
    # Overall result
    if health_ok and dfm_ok and text_to_cad_ok:
        print("\n✅ All tests passed successfully!")
        return 0
    else:
        print("\n❌ Some tests failed. See details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
