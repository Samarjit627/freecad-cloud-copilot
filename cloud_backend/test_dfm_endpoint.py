#!/usr/bin/env python3
"""
Test script for the DFM agent endpoint
"""
import requests
import json
import sys

# Configuration
API_URL = "http://localhost:8080/api/agents/dfm/check"
API_KEY = "dev_api_key_for_testing"  # Default development API key

# Test data
test_data = {
    "part_name": "TestCylinder",
    "material": "ABS",
    "min_wall_thickness_mm": 0.8,  # Below recommended 1.0mm to trigger violation
    "fillet_radius_mm": 0.3,       # Below recommended 0.5mm to trigger violation
    "draft_angle_deg": 0.5,        # Below recommended 1.0° to trigger violation
    "has_undercuts": True          # Will trigger undercut violation
}

def test_dfm_endpoint():
    """Test the DFM endpoint with sample data"""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    print(f"Sending request to {API_URL}")
    print(f"Request data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.post(API_URL, json=test_data, headers=headers)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\nDFM Check Result:")
            print(json.dumps(result, indent=2))
            
            # Count violations by severity
            violations = result.get("violations", [])
            critical_count = sum(1 for v in violations if v.get("severity") == "critical")
            warning_count = sum(1 for v in violations if v.get("severity") == "warning")
            
            print(f"\nFound {len(violations)} violations: {critical_count} critical, {warning_count} warnings")
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Request failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("DFM Endpoint Test")
    print("-" * 50)
    
    success = test_dfm_endpoint()
    
    if success:
        print("\nTest completed successfully!")
        sys.exit(0)
    else:
        print("\nTest failed!")
        sys.exit(1)
