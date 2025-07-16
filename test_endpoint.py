#!/usr/bin/env python3
import json
import requests
import sys

def test_cloud_connection():
    """Test connection to the cloud API"""
    try:
        # Load config
        with open('cloud_config.json', 'r') as f:
            config = json.load(f)
        
        # Get API URL and key
        api_url = config.get('cloud_api_url')
        api_key = config.get('cloud_api_key')
        default_endpoint = config.get('default_analysis_endpoint')
        fallback_endpoints = config.get('fallback_endpoints', [])
        
        print(f"Testing connection to: {api_url}")
        print(f"Default endpoint: {default_endpoint}")
        print(f"Fallback endpoints: {fallback_endpoints}")
        
        # Test health endpoint
        print("\n=== Testing health endpoint ===")
        health_url = f"{api_url}/health"
        print(f"URL: {health_url}")
        
        headers = {
            'Authorization': f"Bearer {api_key}",
            'X-API-Key': api_key
        }
        
        health_response = requests.get(health_url, headers=headers, timeout=5)
        print(f"Status: {health_response.status_code}")
        print(f"Response: {health_response.text}")
        
        # Test all endpoints
        endpoints = [default_endpoint] + fallback_endpoints
        
        for endpoint in endpoints:
            print(f"\n=== Testing endpoint: {endpoint} ===")
            full_url = f"{api_url}{endpoint}"
            print(f"URL: {full_url}")
            
            payload = {
                'message': 'Test message from FreeCAD Co-Pilot',
                'timestamp': '2025-07-15T23:42:16',
                'mode': 'general'
            }
            
            try:
                response = requests.post(
                    full_url, 
                    json=payload, 
                    headers=headers, 
                    timeout=10
                )
                
                print(f"Status: {response.status_code}")
                print(f"Response preview: {response.text[:200]}...")
                
                if response.status_code == 200:
                    print("✅ Endpoint working!")
                else:
                    print("❌ Endpoint returned error status")
            
            except Exception as e:
                print(f"❌ Error testing endpoint: {e}")
        
        return True
    
    except Exception as e:
        print(f"Error testing cloud connection: {e}")
        return False

if __name__ == "__main__":
    test_cloud_connection()
