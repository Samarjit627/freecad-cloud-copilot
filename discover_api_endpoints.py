#!/usr/bin/env python3
"""
API Discovery Tool for FreeCAD Cloud Copilot Service
This script attempts to discover available API endpoints by testing common patterns
"""

import urllib.request
import urllib.error
import urllib.parse
import json
import sys
import os
import ssl
import time

# Add macro directory to path
MACRO_DIR = os.path.dirname(os.path.realpath(__file__))
if MACRO_DIR not in sys.path:
    sys.path.append(MACRO_DIR)

# Import config
try:
    from macro import config
except ImportError:
    print("Error importing config. Make sure the macro directory is in your path.")
    sys.exit(1)

# Common API endpoint patterns to test
ENDPOINT_PATTERNS = [
    # Root endpoints
    "/",
    "/api",
    "/v1",
    "/api/v1",
    
    # Analysis endpoints
    "/analysis",
    "/api/analysis",
    "/analyze",
    "/api/analyze",
    "/cad-analysis",
    "/api/cad-analysis",
    "/cad/analysis",
    "/api/cad/analysis",
    
    # Chat endpoints
    "/chat",
    "/api/chat",
    
    # Documentation endpoints
    "/docs",
    "/api/docs",
    "/swagger",
    "/openapi",
    
    # Known working endpoints
    "/health",
    "/agents"
]

def test_endpoint(endpoint, method="GET", payload=None):
    """Test if an endpoint exists on the cloud service"""
    url = f"{config.CLOUD_API_URL}{endpoint}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    
    print(f"\nTesting endpoint: {url}")
    print(f"Method: {method}")
    
    try:
        # Create SSL context
        context = ssl.create_default_context()
        
        # Prepare request
        req = urllib.request.Request(url, headers=headers, method=method)
        
        # Add payload for POST requests
        if method == "POST" and payload:
            print(f"With payload: {json.dumps(payload, indent=2)}")
            data = json.dumps(payload).encode('utf-8')
            req.data = data
        
        # Make request
        try:
            with urllib.request.urlopen(req, context=context) as response:
                status_code = response.getcode()
                print(f"✅ Status code: {status_code}")
                print(f"Response headers: {response.info()}")
                
                # Read and parse response
                response_data = response.read().decode('utf-8')
                try:
                    response_json = json.loads(response_data)
                    print(f"Response content: {json.dumps(response_json, indent=2)}")
                except:
                    print(f"Response content: {response_data[:200]}...")
                
                return {
                    "endpoint": endpoint,
                    "method": method,
                    "status": status_code,
                    "working": True
                }
                
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP Error: {e.code} - {e.reason}")
            return {
                "endpoint": endpoint,
                "method": method,
                "status": e.code,
                "working": False
            }
                
    except Exception as e:
        print(f"Error testing endpoint: {e}")
        return {
            "endpoint": endpoint,
            "method": method,
            "status": 0,
            "working": False
        }

def main():
    """Main function"""
    print(f"API Discovery for cloud service at: {config.CLOUD_API_URL}")
    print(f"Testing {len(ENDPOINT_PATTERNS)} endpoint patterns...")
    
    # Minimal test payload
    minimal_payload = {
        "metadata": {"name": "test_part"},
        "geometry": {"faces": [], "edges": []},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    # Test GET endpoints
    get_results = []
    for endpoint in ENDPOINT_PATTERNS:
        result = test_endpoint(endpoint, method="GET")
        get_results.append(result)
    
    # Test POST endpoints for analysis and chat
    post_results = []
    for endpoint in [ep for ep in ENDPOINT_PATTERNS if "analysis" in ep or "analyze" in ep or "chat" in ep]:
        result = test_endpoint(endpoint, method="POST", payload=minimal_payload)
        post_results.append(result)
    
    # Summarize results
    print("\n\n=== API DISCOVERY RESULTS ===")
    
    print("\nWorking GET Endpoints:")
    working_get = [r for r in get_results if r["working"]]
    for r in working_get:
        print(f"  ✅ {r['endpoint']} (Status: {r['status']})")
    
    print("\nWorking POST Endpoints:")
    working_post = [r for r in post_results if r["working"]]
    for r in working_post:
        print(f"  ✅ {r['endpoint']} (Status: {r['status']})")
    
    print("\nFailed Endpoints:")
    failed = [r for r in get_results + post_results if not r["working"]]
    for r in failed:
        print(f"  ❌ {r['method']} {r['endpoint']} (Status: {r['status']})")
    
    # Save results to file
    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cloud_api_url": config.CLOUD_API_URL,
        "working_get": working_get,
        "working_post": working_post,
        "failed": failed
    }
    
    with open("api_discovery_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to api_discovery_results.json")
    
    # Suggest next steps
    if working_post:
        print("\nSUGGESTED ENDPOINTS FOR CAD ANALYSIS:")
        for r in working_post:
            if "analysis" in r["endpoint"] or "analyze" in r["endpoint"]:
                print(f"  Use: {r['endpoint']}")
    else:
        print("\nNo working POST endpoints found for CAD analysis.")
        print("Consider checking if the cloud service API has been updated or deployed correctly.")

if __name__ == "__main__":
    main()
