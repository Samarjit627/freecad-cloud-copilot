#!/usr/bin/env python
"""
Test script to verify cloud endpoints are working correctly
"""

import sys
import os
import json
import time
import requests

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Try to import from the macro package
    from macro import cloud_client, config
except ImportError:
    # If that fails, try direct import
    import cloud_client
    import config

def test_cloud_connection():
    """Test the connection to the cloud service"""
    print("\n=== Testing Cloud Connection ===")
    client = cloud_client.get_client()
    print(f"Cloud URL: {client.api_url}")
    print(f"Connected: {client.connected}")
    
    if client.connected:
        print("✅ Successfully connected to Cloud Service")
    else:
        print(f"❌ Connection failed: {client.last_error}")
    
    return client.connected

def test_health_endpoint(client):
    """Test the health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    try:
        response = client._make_request("/health", method="GET")
        print(f"Health endpoint response: {json.dumps(response, indent=2)}")
        print("✅ Health endpoint is working")
        return True
    except Exception as e:
        print(f"❌ Health endpoint failed: {str(e)}")
        return False

def test_analysis_endpoints(client):
    """Test all possible analysis endpoints"""
    print("\n=== Testing Analysis Endpoints ===")
    
    # Create a minimal test payload - wrap in cad_data as expected by the API
    test_payload = {
        "cad_data": {
            "metadata": {
                "name": "Test Part",
                "description": "Test analysis request"
            },
            "geometry": {
                "dimensions": {
                    "length": 100,
                    "width": 50,
                    "height": 25
                },
                "features": {
                    "holes": 2,
                    "fillets": 4
                }
            },
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
    }
    
    # List of endpoints to try
    endpoints = [
        "/api/analysis/cad",   # Correct endpoint from FastAPI app
        "/api/analysis",       # Base endpoint
        "/api/cad-analysis",   # Alternative with prefix
        "/api/v1/analysis",    # Version-specific endpoint
        "/analysis",           # Direct endpoint
        "/cad-analysis",       # Alternative name
        "/analyze"             # Another common name
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints:
        print(f"\nTrying endpoint: {endpoint}")
        try:
            # Try a HEAD request first to check if endpoint exists
            try:
                client._make_request(endpoint, method="HEAD")
                print(f"✅ Endpoint exists: {endpoint}")
            except Exception as e:
                if "404" in str(e):
                    print(f"❌ Endpoint not found: {endpoint}")
                    continue
            
            # Try a POST request with test payload
            try:
                response = client._make_request(endpoint, payload=test_payload)
                print(f"✅ Successfully called endpoint: {endpoint}")
                print(f"Response: {json.dumps(response, indent=2)}")
                working_endpoints.append(endpoint)
            except Exception as e:
                print(f"❌ POST request failed: {str(e)}")
        except Exception as e:
            print(f"❌ Error testing endpoint {endpoint}: {str(e)}")
    
    if working_endpoints:
        print(f"\n✅ Found {len(working_endpoints)} working endpoints: {', '.join(working_endpoints)}")
        return working_endpoints
    else:
        print("\n❌ No working endpoints found")
        return []

def main():
    """Main function"""
    print("=== Cloud Endpoint Test ===")
    
    # Test connection
    connected = test_cloud_connection()
    if not connected:
        print("❌ Cloud connection failed. Exiting.")
        return
    
    # Get client
    client = cloud_client.get_client()
    
    # Test health endpoint
    health_ok = test_health_endpoint(client)
    if not health_ok:
        print("⚠️ Health endpoint failed, but continuing with analysis endpoint tests.")
    
    # Test analysis endpoints
    working_endpoints = test_analysis_endpoints(client)
    
    # Save results to file
    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cloud_url": client.api_url,
        "connected": client.connected,
        "health_endpoint_working": health_ok,
        "working_analysis_endpoints": working_endpoints
    }
    
    with open("cloud_endpoint_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nTest results saved to cloud_endpoint_test_results.json")
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Cloud Connection: {'✅ Working' if connected else '❌ Failed'}")
    print(f"Health Endpoint: {'✅ Working' if health_ok else '❌ Failed'}")
    print(f"Analysis Endpoints: {'✅ Found ' + str(len(working_endpoints)) if working_endpoints else '❌ None working'}")
    
    if working_endpoints:
        print(f"Working endpoints: {', '.join(working_endpoints)}")
        print("\nRecommended endpoint to use: " + working_endpoints[0])
    else:
        print("\n❌ No working analysis endpoints found. The cloud service may not be properly configured.")
        print("   Please check with the cloud service team to confirm the correct endpoints.")

if __name__ == "__main__":
    main()
