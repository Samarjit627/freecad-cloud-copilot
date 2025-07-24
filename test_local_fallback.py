#!/usr/bin/env python3
"""
Test script for local fallback mechanism in the FreeCAD CoPilot cloud services
"""

import os
import sys
import json
import time

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the cloud service handler
from cloud_services.cloud_integration import CloudIntegration
from cloud_services.service_handler import CloudServiceHandler

def test_cloud_integration():
    """Test the cloud integration with local fallback"""
    print("Testing cloud integration with local fallback...")
    
    # Load the config file
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloud_config.json")
    
    # Print the current config
    with open(config_path, 'r') as f:
        config = json.load(f)
        print(f"Current config: {json.dumps(config, indent=2)}")
    
    # Initialize the cloud integration
    cloud_integration = CloudIntegration(config_path)
    
    # Test DFM analysis
    print("\n=== Testing DFM Analysis ===")
    dfm_result = cloud_integration.analyze_dfm(
        manufacturing_process="3d_printing",
        material="pla",
        production_volume=1,
        advanced_analysis=True
    )
    
    print(f"DFM Analysis Result: {json.dumps(dfm_result, indent=2)}")
    
    # Test cost estimation
    print("\n=== Testing Cost Estimation ===")
    cost_result = cloud_integration.estimate_cost(
        manufacturing_process="3d_printing",
        material="pla",
        quantity=1,
        region="global"
    )
    
    print(f"Cost Estimation Result: {json.dumps(cost_result, indent=2)}")
    
    # Test tool recommendation
    print("\n=== Testing Tool Recommendation ===")
    tool_result = cloud_integration.recommend_tools(
        manufacturing_process="cnc_machining",
        material="aluminum",
        machine_type=None
    )
    
    print(f"Tool Recommendation Result: {json.dumps(tool_result, indent=2)}")
    
    # Test direct service handler
    print("\n=== Testing Direct Service Handler ===")
    service_handler = CloudServiceHandler(config_path)
    
    # Test health endpoint
    print("\n=== Testing Health Endpoint ===")
    health_result = service_handler._make_api_call("/health", {})
    print(f"Health Endpoint Result: {json.dumps(health_result, indent=2)}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    test_cloud_integration()
