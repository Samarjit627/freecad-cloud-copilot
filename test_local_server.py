#!/usr/bin/env python3
"""
Test script to directly call the local server and verify response format
"""
import json
import urllib.request
import urllib.error

# Test data similar to what FreeCAD sends
test_data = {
    "cad_data": {
        "dimensions": {
            "overall_length": 64.0,
            "overall_width": 150.13,
            "overall_height": 8.0,
            "total_volume": 18871.73,
            "bounding_box": {
                "min": {
                    "x": -23.0,
                    "y": -34.37,
                    "z": -8.0
                },
                "max": {
                    "x": 41.0,
                    "y": 115.77,
                    "z": 0.0
                }
            }
        },
        "features": {}
    },
    "user_requirements": {
        "target_process": "fdm_printing",
        "material": "pla",
        "production_volume": 100,
        "use_advanced_dfm": True,
        "include_cost_analysis": True,
        "include_alternative_processes": True
    },
    "timestamp": "2025-07-24T18:35:00",
    "source": "test_script",
    "service_requested": "dfm",
    "client_version": "1.0.0"
}

# Send request to local server
url = "http://localhost:8090/api/v2/analyze"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "test-api-key"
}

print(f"Sending request to {url}")

# Convert data to JSON string and encode as bytes
data = json.dumps(test_data).encode('utf-8')

# Create request object
req = urllib.request.Request(url, data=data, headers=headers, method='POST')

try:
    # Send request and get response
    with urllib.request.urlopen(req) as response:
        status_code = response.status
        response_headers = dict(response.getheaders())
        response_body = response.read().decode('utf-8')
        
        print(f"Response status code: {status_code}")
        print(f"Response headers: {response_headers}")
        
        # Parse JSON response
        response_data = json.loads(response_body)
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.reason}")
    print(f"Response: {e.read().decode('utf-8')}")
    exit(1)
except Exception as e:
    print(f"Error: {e}")
    exit(1)

# Headers and status code are printed in the try block above

# Parse and print response
# Response data is already parsed in the try block above
print(f"Response structure: {json.dumps(response_data, indent=2)}")

# Check for expected fields
print("\nChecking response structure:")
if "success" in response_data:
    print(f"- success: {response_data['success']}")
else:
    print("- Missing 'success' field")

# Check for manufacturability_score at the top level
if "manufacturability_score" in response_data:
    print(f"- manufacturability_score: {response_data['manufacturability_score']}")
else:
    print("- Missing 'manufacturability_score' field at top level")
    
# Check for issues at the top level
if "issues" in response_data:
    issues = response_data["issues"]
    print(f"- issues: {len(issues)}")
    for i, issue in enumerate(issues):
        print(f"  Issue {i+1}: {issue.get('message', 'No message')}")
else:
    print("- Missing 'issues' field at top level")
    
# Check for recommendations at the top level
if "recommendations" in response_data:
    recommendations = response_data["recommendations"]
    print(f"- recommendations: {len(recommendations)}")
    for i, rec in enumerate(recommendations):
        print(f"  Recommendation {i+1}: {rec}")
else:
    print("- Missing 'recommendations' field at top level")
