#!/usr/bin/env python3
"""
Test script to simulate the FreeCAD plugin's interaction with the fixed backend.
This script will:
1. Load the cloud_config.json to get the API URL
2. Send a sample CAD data payload to the backend
3. Process the response as the FreeCAD plugin would
4. Display the results
"""

import json
import os
import sys
import requests
import pprint

# Add the FreeCAD plugin directory to the path so we can import its modules
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(SCRIPT_DIR, "freecad_plugin"))

# Try to import the DFM service module from the FreeCAD plugin
try:
    from dfm_service import DFMService
    USING_ACTUAL_PLUGIN = True
    print("Using actual FreeCAD plugin DFMService")
except ImportError:
    USING_ACTUAL_PLUGIN = False
    print("Could not import DFMService from FreeCAD plugin, using simulation")

# Load the cloud configuration
def load_cloud_config():
    config_path = os.path.join(SCRIPT_DIR, "cloud_config.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Error loading cloud config: {str(e)}")
        return {"cloud_api_url": "https://freecad-copilot-fixed-4cmxv2m7cq-el.a.run.app"}

# Create a sample CAD data payload
def create_sample_payload():
    return {
        "part_name": "Test Part",
        "volume": 125.0,  # cm³
        "surface_area": 150.0,  # cm²
        "bounding_box": {
            "x": 5.0,
            "y": 5.0,
            "z": 5.0
        },
        "material": "pla",
        "process": "fdm_printing",
        "production_volume": 100
    }

# Send the payload to the backend
def send_to_backend(url, payload):
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "test-api-key"
    }
    
    # Use the v2 API endpoint
    api_url = f"{url}/api/v2/analyze"
    print(f"Sending request to: {api_url}")
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error sending request: {str(e)}")
        if hasattr(response, 'text'):
            print(f"Response text: {response.text}")
        return None

# Process the response as the FreeCAD plugin would
class MockDFMService:
    def __init__(self):
        self.last_analysis = None
    
    def transform_response(self, response):
        """Simulate the FreeCAD plugin's response transformation"""
        transformed_data = {}
        
        # Extract design issues
        if "design_issues" in response:
            transformed_data["design_issues"] = response["design_issues"]
        else:
            transformed_data["design_issues"] = []
        
        # Extract manufacturing features
        if "manufacturing_features" in response:
            transformed_data["manufacturing_features"] = response["manufacturing_features"]
        else:
            transformed_data["manufacturing_features"] = {
                "manufacturability_score": 0,
                "overall_rating": "UNKNOWN"
            }
        
        # Extract process recommendations
        if "process_recommendations" in response:
            transformed_data["process_recommendations"] = response["process_recommendations"]
        else:
            transformed_data["process_recommendations"] = []
        
        # Extract material suggestions
        if "material_suggestions" in response:
            transformed_data["material_suggestions"] = response["material_suggestions"]
        else:
            transformed_data["material_suggestions"] = []
        
        # Store the transformed data
        self.last_analysis = transformed_data
        return transformed_data

# Main function
def main():
    # Load the cloud configuration
    config = load_cloud_config()
    cloud_api_url = config.get("cloud_api_url")
    print(f"Using cloud API URL: {cloud_api_url}")
    
    # Create a sample payload
    payload = create_sample_payload()
    print("Sample payload:")
    pprint.pprint(payload)
    
    # Send the payload to the backend
    print("\nSending request to backend...")
    response = send_to_backend(cloud_api_url, payload)
    
    if response:
        print("\nReceived response from backend:")
        pprint.pprint(response)
        
        # Process the response
        print("\nProcessing response...")
        if USING_ACTUAL_PLUGIN:
            # Use the actual FreeCAD plugin DFMService
            dfm_service = DFMService()
            transformed_data = dfm_service.transform_cloud_response(response)
        else:
            # Use our mock DFMService
            dfm_service = MockDFMService()
            transformed_data = dfm_service.transform_response(response)
        
        print("\nTransformed data (what the FreeCAD plugin would use):")
        pprint.pprint(transformed_data)
        
        # Display the manufacturability score
        if "manufacturing_features" in transformed_data:
            score = transformed_data["manufacturing_features"].get("manufacturability_score", 0)
            rating = transformed_data["manufacturing_features"].get("overall_rating", "UNKNOWN")
            print(f"\nManufacturability Score: {score}/100")
            print(f"Overall Rating: {rating}")
        
        # Display the design issues
        if "design_issues" in transformed_data:
            issues = transformed_data["design_issues"]
            print(f"\nDesign Issues: {len(issues)}")
            for i, issue in enumerate(issues):
                print(f"  {i+1}. {issue.get('title', 'Unknown Issue')}")
        
        # Display the process recommendations
        if "process_recommendations" in transformed_data:
            recommendations = transformed_data["process_recommendations"]
            print(f"\nProcess Recommendations: {len(recommendations)}")
            for i, rec in enumerate(recommendations):
                print(f"  {i+1}. {rec}")
        
        # Display the material suggestions
        if "material_suggestions" in transformed_data:
            materials = transformed_data["material_suggestions"]
            print(f"\nMaterial Suggestions: {len(materials)}")
            for i, mat in enumerate(materials):
                print(f"  {i+1}. {mat}")
        
        # Display the expert recommendations
        if "expert_recommendations" in response:
            expert_recs = response["expert_recommendations"]
            print(f"\nExpert Recommendations: {len(expert_recs)}")
            for i, rec in enumerate(expert_recs):
                print(f"  {i+1}. {rec}")
    else:
        print("No response received from backend")

if __name__ == "__main__":
    main()
