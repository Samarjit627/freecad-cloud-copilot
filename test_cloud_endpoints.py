#!/usr/bin/env python3
"""Test script to discover working endpoints on the Google Cloud Run service"""

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
                print("Endpoint not found (404)")
            
            try:
                error_data = e.read().decode('utf-8')
                print(f"Error response: {error_data}")
            except:
                pass
                
            return False
    
    except Exception as e:
        print(f"Error testing endpoint: {e}")
        return False

def main():
    """Main function"""
    print(f"Testing cloud service at: {config.CLOUD_API_URL}")
    
    # Test health endpoint
    test_endpoint("/health")
    
    # Test analysis endpoint with minimal payload
    minimal_payload = {
        "metadata": {"name": "test_part"},
        "geometry": {"faces": [], "edges": []},
        "timestamp": "2023-07-12T12:00:00"
    }
    test_endpoint("/api/analysis", method="POST", payload=minimal_payload)
    
    # Test analysis endpoint without /api prefix
    test_endpoint("/analysis", method="POST", payload=minimal_payload)
    
    # Test the old endpoint to confirm it doesn't exist
    test_endpoint("/api/cad-analysis", method="POST", payload=minimal_payload)
    
    # Test other endpoints
    test_endpoint("/api/chat", method="POST", payload={"query": "What is manufacturing?"})
    test_endpoint("/agents")

if __name__ == "__main__":
    main()
