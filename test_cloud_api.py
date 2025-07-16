#!/usr/bin/env python3
"""
Test script to check Google Cloud Run service endpoints and verify CAD analysis functionality
"""

import requests
import json
import time
import sys
import os
from pathlib import Path
from datetime import datetime

# Add macro directory to path
MACRO_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(MACRO_DIR)

# Import cloud client
try:
    from macro import cloud_client, config
except ImportError:
    import cloud_client, config

# List of possible endpoints to test
POSSIBLE_ENDPOINTS = [
    "/",                     # Root endpoint
    "/health",               # Health check endpoint
    "/api",                  # API root
    "/api/analysis",         # Analysis base endpoint
    "/api/analysis/cad",     # CAD analysis endpoint
    "/api/v1/analysis",      # Versioned analysis endpoint
    "/api/v1/analysis/cad",  # Versioned CAD analysis endpoint
    "/analysis",             # Direct analysis endpoint
    "/cad-analysis",         # Alternative name
    "/analyze",              # Another common name
    "/api/chat",             # Chat endpoint
    "/api/agents",           # Agents endpoint
    "/docs",                 # API documentation
    "/openapi.json"          # OpenAPI schema
]

def test_endpoint(endpoint, method="GET", payload=None, api_key=None):
    """Test if an endpoint exists on the cloud service"""
    url = f"{config.CLOUD_API_URL}{endpoint}"
    
    print(f"\nTesting endpoint: {url}")
    print(f"Method: {method}")
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Add API key if provided
    if api_key:
        headers['X-API-Key'] = api_key
        print("Using API key")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "HEAD":
            response = requests.head(url, headers=headers, timeout=5)
        elif method == "POST":
            if payload:
                print(f"With payload: {json.dumps(payload, indent=2)[:200]}..." if len(json.dumps(payload)) > 200 else json.dumps(payload, indent=2))
            response = requests.post(url, json=payload, headers=headers, timeout=15)
        else:
            return {"status": 0, "exists": False, "error": f"Unsupported method: {method}"}
        
        print(f"Status code: {response.status_code}")
        
        result = {
            "status": response.status_code,
            "exists": response.status_code != 404,
            "method": method,
            "url": url
        }
        
        # Try to parse response as JSON
        try:
            if response.text:
                json_response = response.json()
                result["response"] = json_response
                print(f"Response content: {json.dumps(json_response, indent=2)[:300]}..." if len(json.dumps(json_response)) > 300 else json.dumps(json_response, indent=2))
        except json.JSONDecodeError:
            result["response"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
            print(f"Response content (not JSON): {result['response']}")
            
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {str(e)}")
        return {"status": 0, "exists": False, "error": str(e), "method": method, "url": url}

def create_test_cad_payload():
    """Create a test CAD data payload"""
    return {
        "cad_data": {
            "dimensions": {
                "length": 100,
                "width": 50,
                "height": 25,
                "volume": 125000
            },
            "features": {
                "holes": 2,
                "fillets": 4,
                "chamfers": 1,
                "ribs": 0,
                "undercuts": 0,
                "thin_walls": 0,
                "sharp_corners": 8
            }
        },
        "user_requirements": {
            "application": "Automotive",
            "production_volume": "Small Batch (100-1,000 pieces)",
            "material_preferences": ["ABS", "Nylon"],
            "cost_sensitivity": "Medium"
        }
    }

def test_all_endpoints():
    """Test all possible endpoints with GET requests"""
    results = []
    
    print(f"Testing cloud service: {config.CLOUD_API_URL}")
    print(f"Testing {len(POSSIBLE_ENDPOINTS)} possible endpoints...")
    
    for endpoint in POSSIBLE_ENDPOINTS:
        result = test_endpoint(endpoint)
        results.append(result)
        time.sleep(1)  # Avoid rate limiting
    
    return results

def test_cad_analysis_endpoints():
    """Test CAD analysis endpoints with POST requests"""
    results = []
    
    # Create test payload
    payload = create_test_cad_payload()
    
    # Test only analysis endpoints
    analysis_endpoints = [ep for ep in POSSIBLE_ENDPOINTS if "analysis" in ep or "analyze" in ep or "cad" in ep]
    
    print(f"\nTesting {len(analysis_endpoints)} CAD analysis endpoints with POST requests...")
    
    for endpoint in analysis_endpoints:
        result = test_endpoint(endpoint, method="POST", payload=payload)
        results.append(result)
        time.sleep(1)  # Avoid rate limiting
    
    return results

def save_results(results, filename=None):
    """Save test results to a JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cloud_endpoint_test_results_{timestamp}.json"
    
    # Convert results to serializable format
    serializable_results = []
    for result in results:
        serializable_result = {}
        for key, value in result.items():
            if isinstance(value, (str, int, bool, list, dict, type(None))):
                serializable_result[key] = value
            else:
                serializable_result[key] = str(value)
        serializable_results.append(serializable_result)
    
    # Save to file
    with open(filename, "w") as f:
        json.dump(serializable_results, f, indent=2)
    
    print(f"\nResults saved to {filename}")
    return filename

def update_cloud_config(working_endpoints):
    """Update cloud_config.json with working endpoints"""
    config_file = Path(MACRO_DIR) / "cloud_config.json"
    
    if not config_file.exists():
        print(f"Creating new cloud config at {config_file}")
        cloud_config = {}
    else:
        try:
            with open(config_file, "r") as f:
                cloud_config = json.load(f)
        except json.JSONDecodeError:
            print(f"Error reading cloud config, creating new one")
            cloud_config = {}
    
    # Update with working endpoints
    if working_endpoints:
        # Set the first working endpoint as default
        cloud_config["default_analysis_endpoint"] = working_endpoints[0]
        
        # Add all working endpoints as fallbacks
        cloud_config["fallback_endpoints"] = working_endpoints
        
        # Save updated config
        with open(config_file, "w") as f:
            json.dump(cloud_config, f, indent=2)
        
        print(f"\nUpdated cloud config with working endpoints: {working_endpoints}")
    else:
        print("\nNo working endpoints found to update config")

def main():
    """Main function"""
    print("=== Testing Cloud Service Endpoints ===")
    print(f"Cloud API URL: {config.CLOUD_API_URL}")
    
    # Test all endpoints with GET requests
    print("\n=== Testing all endpoints with GET requests ===")
    get_results = test_all_endpoints()
    
    # Test CAD analysis endpoints with POST requests
    print("\n=== Testing CAD analysis endpoints with POST requests ===")
    post_results = test_cad_analysis_endpoints()
    
    # Combine results
    all_results = get_results + post_results
    
    # Save results
    results_file = save_results(all_results)
    
    # Find working endpoints for CAD analysis
    working_endpoints = []
    for result in post_results:
        if result.get("status") == 200 and result.get("exists", False):
            # Extract endpoint from URL
            url = result.get("url", "")
            endpoint = url.replace(config.CLOUD_API_URL, "")
            working_endpoints.append(endpoint)
    
    print("\n=== Summary ===")
    print(f"Total endpoints tested: {len(all_results)}")
    print(f"Working endpoints for CAD analysis: {working_endpoints}")
    
    # Update cloud config with working endpoints
    if working_endpoints:
        update_cloud_config(working_endpoints)
    
    return working_endpoints

if __name__ == "__main__":
    main()
