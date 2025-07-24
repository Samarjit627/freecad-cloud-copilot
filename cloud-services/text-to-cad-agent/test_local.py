#!/usr/bin/env python3
"""
Test script for the Text-to-CAD agent
Sends a test request to the local server
"""

import json
import requests
import time
import sys

# Configuration
SERVER_URL = "http://localhost:8070"
TEST_PROMPT = "Design a simple gear with 20 teeth and 5mm module"

def test_text_to_cad():
    """Test the text-to-CAD endpoint"""
    print(f"Sending test request to {SERVER_URL}/text-to-cad")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{SERVER_URL}/text-to-cad",
            json={
                "prompt": TEST_PROMPT,
                "parameters": {
                    "detail_level": "medium",
                    "output_format": "freecad_python"
                }
            },
            headers={"Content-Type": "application/json"}
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Response received in {elapsed:.2f} seconds")
            print("\nEngineering Analysis:")
            print(result.get("engineering_analysis", "No analysis provided"))
            
            print("\nFreeCAD Python Code (first 10 lines):")
            code_lines = result.get("freecad_code", "").split("\n")
            for i, line in enumerate(code_lines[:10]):
                print(f"{i+1}: {line}")
            
            if len(code_lines) > 10:
                print(f"... and {len(code_lines) - 10} more lines")
        else:
            print(f"❌ Error: Status code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = test_text_to_cad()
    sys.exit(0 if success else 1)
