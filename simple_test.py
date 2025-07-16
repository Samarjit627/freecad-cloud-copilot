#!/usr/bin/env python3
"""
Simple test script to verify cloud client error handling and fallback mechanism
"""

import os
import sys
import json

# Mock the necessary modules
class MockResponse:
    def __init__(self, status_code=404, text="Not Found"):
        self.status_code = status_code
        self.text = text
        self._json = {"error": "Not Found"}
        
    def json(self):
        return self._json

class MockRequests:
    def get(self, url, **kwargs):
        if "/health" in url:
            return MockResponse(200, "OK")
        return MockResponse(404, "Not Found")
        
    def post(self, url, **kwargs):
        return MockResponse(404, "Not Found")

# Create mock modules
sys.modules['requests'] = type('MockRequests', (), {'get': MockRequests().get, 'post': MockRequests().post})

# Create a simplified version of the cloud client
class SimpleCloudClient:
    def __init__(self):
        self.api_url = "https://example.com/api"
        self.api_key = "test_key"
        self.last_successful_endpoint = None
        
    def _make_request(self, endpoint, payload=None, method="POST"):
        import requests
        
        url = f"{self.api_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        print(f"Making {method} request to {url}")
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        else:
            response = requests.post(url, json=payload, headers=headers)
            
        if response.status_code != 200:
            print(f"Request failed with status {response.status_code}: {response.text}")
            raise Exception(f"API request failed: {response.text}")
            
        return response.json()
        
    def analyze_cad(self, metadata, geometry_data):
        payload = {
            "metadata": metadata,
            "geometry": geometry_data
        }
        
        endpoints_to_try = [
            "/analysis",           # Standard name
            "/api/analysis",       # With API prefix
            "/cad-analysis",       # Alternative name
            "/api/cad-analysis",   # Alternative with prefix
            "/analyze"             # Another common name
        ]
        
        last_error = None
        for endpoint in endpoints_to_try:
            try:
                print(f"Trying endpoint: {endpoint}")
                response = self._make_request(endpoint, payload=payload)
                print(f"Success with endpoint: {endpoint}")
                
                # Store the successful endpoint
                self.last_successful_endpoint = endpoint
                
                # Mark this as cloud analysis
                response["analysis_type"] = "cloud"
                return response
                
            except Exception as e:
                print(f"Failed with endpoint {endpoint}: {str(e)}")
                last_error = e
                continue
        
        # If we get here, all endpoints failed
        print("All cloud analysis endpoints failed. Raising exception...")
        raise Exception(f"All cloud analysis endpoints failed. Last error: {str(last_error)}")

# Create a simplified version of the cloud analyzer with fallback
class SimpleCloudAnalyzer:
    def __init__(self):
        self.cloud_client = SimpleCloudClient()
        
    def analyze_document(self, document):
        # Basic metadata that would normally come from the document
        basic_metadata = {
            "name": "Test Part",
            "object_count": 1,
            "x_length": 100.0,
            "y_length": 50.0,
            "z_length": 25.0
        }
        
        # Simple geometry data
        geometry_data = {
            "vertices": [[0, 0, 0], [100, 0, 0], [100, 50, 0], [0, 50, 0]],
            "faces": [[0, 1, 2, 3]]
        }
        
        try:
            print("Attempting cloud-based CAD analysis...")
            analysis_result = self.cloud_client.analyze_cad(basic_metadata, geometry_data)
            analysis_result["analysis_type"] = "cloud"
            print("✅ Cloud analysis successful!")
            if hasattr(self.cloud_client, 'last_successful_endpoint') and self.cloud_client.last_successful_endpoint:
                print(f"Used endpoint: {self.cloud_client.last_successful_endpoint}")
            
            return analysis_result
            
        except Exception as cloud_error:
            print(f"Error in cloud CAD analysis: {str(cloud_error)}")
            print("⚠️ Falling back to local CAD analysis...")
            
            # Simulate local analysis
            local_result = {
                "analysis_type": "local",
                "cloud_error": str(cloud_error),
                "note": "Cloud analysis unavailable. Using limited local analysis.",
                "metadata": basic_metadata,
                "features": {
                    "holes": [],
                    "fillets": [],
                    "chamfers": []
                }
            }
            
            return local_result

def main():
    print("\n===== Testing Cloud Client Fallback =====")
    
    # Create analyzer
    analyzer = SimpleCloudAnalyzer()
    
    # Test analyze_document
    print("\nTesting analyze_document with fallback...")
    result = analyzer.analyze_document(None)  # Document not needed for this test
    
    # Print results
    print("\nAnalysis result:")
    print(f"Analysis type: {result.get('analysis_type', 'unknown')}")
    
    if "cloud_error" in result:
        print(f"Cloud error: {result['cloud_error']}")
        
    if "note" in result:
        print(f"Note: {result['note']}")
        
    return result

if __name__ == "__main__":
    main()
