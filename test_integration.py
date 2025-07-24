#!/usr/bin/env python3
"""
Test script for the Text-to-CAD integration
This script tests the integration between the FreeCAD macro and the Text-to-CAD cloud service
"""

import os
import sys
import json
from text_to_cad_integration import TextToCADIntegration

def test_text_to_cad_integration():
    """Test the Text-to-CAD integration"""
    print("Testing Text-to-CAD integration...")
    
    # Initialize the Text-to-CAD integration with the correct config path
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cloud_config.json')
    print(f"Using config path: {config_path}")
    integration = TextToCADIntegration(config_path)
    
    # Check if the integration is connected
    if not integration.connected:
        print("Text-to-CAD integration is not connected")
        print(f"Cloud endpoint: {integration.endpoint if hasattr(integration, 'endpoint') else 'Not set'}")
        print(f"Last error: {integration.last_error}")
        return False
    
    # Test connection to the Text-to-CAD service
    print("Testing connection to Text-to-CAD service...")
    connection_success = integration.test_connection()
    
    if not connection_success:
        print("Connection test failed")
        return False
    
    print("Connection test successful")
    print(f"Connected to endpoint: {integration.config.get('text_to_cad_endpoint')}")
    print(f"Available capabilities: {integration.capabilities}")
    
    # Test detection of Text-to-CAD requests
    test_requests = [
        "Generate a 750ml water bottle",
        "Create a mountain bike frame",
        "Design a gear with 24 teeth",
        "What's the weather like today?",
        "Open the Part workbench",
        "Hello, how are you?"
    ]
    
    print("\nTesting Text-to-CAD request detection:")
    for request in test_requests:
        is_text_to_cad = integration.is_text_to_cad_request(request)
        print(f"  '{request}': {'✅ Text-to-CAD request' if is_text_to_cad else '❌ Not a Text-to-CAD request'}")
    
    # Test sending a Text-to-CAD request
    print("\nSending a test Text-to-CAD request...")
    
    def progress_callback(message):
        print(f"  Progress: {message}")
    
    result = integration.handle_text_to_cad_request("Generate a simple gear with 12 teeth", progress_callback)
    
    if result.get("success", False):
        print("✅ Text-to-CAD request successful!")
        print(f"Message: {result.get('message', '')}")
        if "engineering_analysis" in result:
            print("\nEngineering Analysis (truncated):")
            analysis = result["engineering_analysis"]
            print(analysis[:200] + "..." if len(analysis) > 200 else analysis)
        return True
    else:
        print(f"❌ Text-to-CAD request failed: {result.get('message', 'Unknown error')}")
        return False

if __name__ == "__main__":
    test_text_to_cad_integration()
