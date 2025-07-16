#!/usr/bin/env python3
"""
Test script for the FreeCAD Manufacturing Co-Pilot multi-agent system
This script tests the integration between the cloud backend and the FreeCAD frontend
"""

import sys
import os
import json
from pathlib import Path

# Add macro directory to path
SCRIPT_DIR = Path(__file__).parent
MACRO_DIR = SCRIPT_DIR / "macro"
sys.path.append(str(MACRO_DIR))

# Import required modules
import cloud_client
import ai_engine

def test_cloud_connection():
    """Test cloud API connection"""
    print("\n=== Testing Cloud Connection ===")
    client = cloud_client.get_client()
    connected = client.test_connection()
    print(f"Cloud connection: {'✅ Connected' if connected else '❌ Disconnected'}")
    return connected

def test_agent_listing():
    """Test fetching available agents"""
    print("\n=== Testing Agent Listing ===")
    engine = ai_engine.ManufacturingIntelligenceEngine()
    agents = engine.get_available_agents()
    
    if not agents:
        print("❌ No agents available (could be using fallback)")
    else:
        print(f"✅ Found {len(agents)} agents:")
        for i, agent in enumerate(agents, 1):
            print(f"  {i}. {agent.get('name', 'Unknown')} (ID: {agent.get('id', 'unknown')})")
            print(f"     {agent.get('description', 'No description')}")
    
    return agents

def test_agent_query(agent_id, query="What manufacturing process would you recommend for this part?"):
    """Test querying a specific agent"""
    print(f"\n=== Testing Agent Query: {agent_id} ===")
    print(f"Query: '{query}'")
    
    engine = ai_engine.ManufacturingIntelligenceEngine()
    response = engine.query_agent(agent_id, query, {})
    
    print("\nResponse:")
    print_formatted_response(response)
    
    return response

def test_agent_orchestration(agent_ids, query="What are the trade-offs between different manufacturing processes for this part?"):
    """Test orchestrating multiple agents"""
    print(f"\n=== Testing Agent Orchestration: {', '.join(agent_ids)} ===")
    print(f"Query: '{query}'")
    
    engine = ai_engine.ManufacturingIntelligenceEngine()
    response = engine.orchestrate_agents(query, {}, agent_ids)
    
    print("\nResponse:")
    print_formatted_response(response)
    
    return response

def print_formatted_response(response):
    """Print a formatted response with line wrapping"""
    width = 80
    lines = []
    
    # Handle dictionary response
    if isinstance(response, dict):
        if 'response' in response:
            response_text = response['response']
        elif 'summary' in response:
            response_text = response['summary']
        else:
            response_text = str(response)
    else:
        response_text = str(response)
    
    for line in response_text.split("\n"):
        while len(line) > width:
            # Find the last space before the width limit
            space_pos = line[:width].rfind(" ")
            if space_pos == -1:  # No space found, just cut at width
                space_pos = width
            
            lines.append(line[:space_pos])
            line = line[space_pos:].lstrip()
        
        lines.append(line)
    
    print("\n".join(lines))

def main():
    """Main test function"""
    print("FreeCAD Manufacturing Co-Pilot Multi-Agent System Test")
    print("=====================================================")
    
    # Test cloud connection
    connected = test_cloud_connection()
    if not connected:
        print("\n⚠️  Warning: Cloud is disconnected, will use fallback responses")
    
    # Test agent listing
    agents = test_agent_listing()
    
    if not agents:
        print("\n❌ Cannot test agent queries without available agents")
        return
    
    # Test individual agent query
    agent_id = agents[0].get('id')
    test_agent_query(agent_id)
    
    # Test orchestration if multiple agents available
    if len(agents) >= 2:
        agent_ids = [agent.get('id') for agent in agents[:2]]
        test_agent_orchestration(agent_ids)
    else:
        print("\n⚠️  Not enough agents for orchestration test")

if __name__ == "__main__":
    main()
