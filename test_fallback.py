#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple test script to verify the cloud client endpoint detection and fallback mechanism
This script doesn't require FreeCAD and can be run directly with Python
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error

# Add the project directory to the Python path
script_dir = os.path.dirname(os.path.realpath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

# Import configuration
try:
    from macro import config
except ImportError as e:
    print(f"Error importing config: {e}")
    sys.exit(1)

def test_cloud_endpoints():
    """Test various cloud endpoints to find which ones are available"""
    print("\n===== TESTING CLOUD ENDPOINTS =====")
    
    # Base URL from config
    base_url = config.CLOUD_API_URL
    print(f"Cloud URL: {base_url}")
    
    # List of endpoints to test
    endpoints = [
        "/",                # Root
        "/health",          # Health check
        "/agents",          # Agents list
        "/analysis",        # Analysis endpoint
        "/api/analysis",    # Analysis with /api prefix
        "/cad-analysis",    # Alternative name
        "/api/cad-analysis",# Alternative with prefix
        "/analyze"          # Another common name
    ]
    
    results = {}
    
    # Test each endpoint with GET
    print("\nTesting GET endpoints:")
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"Testing GET {url}...")
        
        try:
            request = urllib.request.Request(url, method="GET")
            response = urllib.request.urlopen(request, timeout=10)
            status = response.status
            content = response.read().decode('utf-8')
            
            print(f"  ✅ Status: {status}")
            results[f"GET {endpoint}"] = {
                "status": status,
                "content_length": len(content),
                "content_preview": content[:100] if len(content) > 0 else "Empty response"
            }
            
        except urllib.error.HTTPError as e:
            print(f"  ❌ HTTP Error: {e.code} - {e.reason}")
            results[f"GET {endpoint}"] = {
                "status": e.code,
                "error": e.reason
            }
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results[f"GET {endpoint}"] = {
                "status": "error",
                "error": str(e)
            }
    
    # Test each endpoint with POST
    print("\nTesting POST endpoints:")
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"Testing POST {url}...")
        
        # Simple test payload
        payload = {
            "metadata": {
                "name": "test_part",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            },
            "geometry": {
                "faces": [10],
                "edges": [20]
            }
        }
        
        try:
            data = json.dumps(payload).encode('utf-8')
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            request = urllib.request.Request(
                url, 
                data=data, 
                headers=headers, 
                method="POST"
            )
            
            response = urllib.request.urlopen(request, timeout=10)
            status = response.status
            content = response.read().decode('utf-8')
            
            print(f"  ✅ Status: {status}")
            results[f"POST {endpoint}"] = {
                "status": status,
                "content_length": len(content),
                "content_preview": content[:100] if len(content) > 0 else "Empty response"
            }
            
        except urllib.error.HTTPError as e:
            print(f"  ❌ HTTP Error: {e.code} - {e.reason}")
            results[f"POST {endpoint}"] = {
                "status": e.code,
                "error": e.reason
            }
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results[f"POST {endpoint}"] = {
                "status": "error",
                "error": str(e)
            }
    
    # Save results to a file
    with open('endpoint_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to endpoint_test_results.json")
    return results

def test_fallback_simulation():
    """Simulate the fallback mechanism by using an invalid cloud URL"""
    print("\n===== TESTING FALLBACK MECHANISM SIMULATION =====")
    
    # Save original URL
    original_url = config.CLOUD_API_URL
    
    try:
        # Set an invalid URL to force fallback
        print(f"Original cloud URL: {config.CLOUD_API_URL}")
        config.CLOUD_API_URL = "https://nonexistent-service-url.example.com"
        print(f"Modified cloud URL to force error: {config.CLOUD_API_URL}")
        
        # Create a simple payload
        metadata = {
            "name": "test_part",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        geometry_data = {
            "faces": [10],
            "edges": [20]
        }
        
        print("\nThis would trigger the fallback mechanism in the full FreeCAD environment")
        print("The CloudCADAnalyzer would catch the exception and use LocalCADAnalyzer instead")
        
    finally:
        # Restore original URL
        config.CLOUD_API_URL = original_url
        print(f"\nRestored original cloud URL: {config.CLOUD_API_URL}")

if __name__ == "__main__":
    # Test cloud endpoints
    test_cloud_endpoints()
    
    # Test fallback simulation
    test_fallback_simulation()
