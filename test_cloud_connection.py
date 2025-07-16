#!/usr/bin/env python3
"""
Test script to verify connection to the FreeCAD Manufacturing Co-Pilot Cloud Service
"""

import sys
import os
import json

# Add the macro directory to the path so we can import modules
script_dir = os.path.dirname(os.path.abspath(__file__))
macro_dir = os.path.join(script_dir, "macro")
sys.path.append(macro_dir)

# Import the cloud client
import cloud_client
import config

def main():
    print(f"Testing connection to cloud service at: {config.CLOUD_API_URL}")
    
    # Get client instance
    client = cloud_client.get_client()
    
    # Test connection
    print(f"Connected: {client.connected}")
    if not client.connected:
        print(f"Connection error: {client.last_error}")
        return
    
    # Test health endpoint
    try:
        print("\nTesting /health endpoint...")
        response = client._make_request("/health", method="GET")
        print(f"Health check response: {json.dumps(response, indent=2)}")
    except Exception as e:
        print(f"Health check error: {e}")
    
    # Test agents endpoint
    try:
        print("\nTesting /agents endpoint...")
        response = client.get_available_agents()
        print(f"Available agents: {json.dumps(response, indent=2)}")
    except Exception as e:
        print(f"Agents error: {e}")
    
    # Test query endpoint with a sample query
    try:
        print("\nTesting /query endpoint...")
        agent_id = "machining-expert"  # Use one of the available agent IDs
        query = "How do I optimize a milling operation?"
        response = client.query_agent(agent_id, query, {})
        print(f"Query response: {json.dumps(response, indent=2)}")
    except Exception as e:
        print(f"Query error: {e}")

if __name__ == "__main__":
    main()
