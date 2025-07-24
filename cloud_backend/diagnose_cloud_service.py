#!/usr/bin/env python3
"""
Diagnostic tool for FreeCAD Cloud Copilot service
This script tests connectivity and functionality of the cloud service
"""

import os
import sys
import json
import time
import argparse
import requests
from urllib.parse import urljoin

def test_service_health(base_url, api_key=None):
    """Test the health endpoint of the service"""
    health_url = urljoin(base_url, "/health")
    print(f"Testing health endpoint: {health_url}")
    
    try:
        start_time = time.time()
        response = requests.get(health_url, timeout=10)
        elapsed = time.time() - start_time
        
        print(f"Status code: {response.status_code}")
        print(f"Response time: {elapsed:.2f} seconds")
        
        if response.status_code == 200:
            print("✅ Health check successful")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Health check timed out")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - service may be down or unreachable")
        return False
    except Exception as e:
        print(f"❌ Error testing health endpoint: {str(e)}")
        return False

def test_dfm_endpoint(base_url, api_key):
    """Test the DFM analysis endpoint with a simple request"""
    dfm_url = urljoin(base_url, "/api/v2/analysis/dfm")
    print(f"Testing DFM endpoint: {dfm_url}")
    
    # Simple test payload
    payload = {
        "cad_data": {
            "part_name": "test_part",
            "vertices": [[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]],
            "faces": [[0, 1, 2, 3]],
            "volume": 100.0,
            "surface_area": 400.0,
            "bounding_box": [10, 10, 0]
        },
        "material": "ABS",
        "production_volume": 100,
        "advanced_analysis": True
    }
    
    headers = {"X-API-Key": api_key}
    
    try:
        start_time = time.time()
        response = requests.post(dfm_url, json=payload, headers=headers, timeout=30)
        elapsed = time.time() - start_time
        
        print(f"Status code: {response.status_code}")
        print(f"Response time: {elapsed:.2f} seconds")
        
        if response.status_code == 200:
            print("✅ DFM test successful")
            result = response.json()
            print(f"Manufacturability score: {result.get('data', {}).get('manufacturability_score', 'N/A')}")
            return True
        else:
            print(f"❌ DFM test failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing DFM endpoint: {str(e)}")
        return False

def load_config():
    """Load cloud configuration from config file"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cloud_config.json")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config
    except Exception as e:
        print(f"Error loading config: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Diagnose FreeCAD Cloud Copilot service")
    parser.add_argument("--url", help="Base URL of the cloud service")
    parser.add_argument("--api-key", help="API key for authentication")
    parser.add_argument("--test-dfm", action="store_true", help="Test DFM endpoint")
    args = parser.parse_args()
    
    # Load config if URL or API key not provided
    config = None
    if not args.url or not args.api_key:
        config = load_config()
        if not config:
            print("Error: Could not load configuration and no URL/API key provided")
            return 1
    
    # Use provided URL or from config
    base_url = args.url if args.url else config.get("cloud_api_url")
    api_key = args.api_key if args.api_key else config.get("cloud_api_key")
    
    if not base_url:
        print("Error: No service URL provided")
        return 1
    
    print(f"Testing cloud service at: {base_url}")
    
    # Test health endpoint
    health_ok = test_service_health(base_url, api_key)
    
    # Test DFM endpoint if requested and health check passed
    if args.test_dfm and health_ok and api_key:
        test_dfm_endpoint(base_url, api_key)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
