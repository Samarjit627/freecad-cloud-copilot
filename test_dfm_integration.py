#!/usr/bin/env python3
"""
End-to-End Test Script for FreeCAD DFM Analysis Integration

This script simulates the interaction between the FreeCAD plugin and the backend API
for advanced DFM analysis. It sends a sample CAD model for analysis and displays the results.
"""

import requests
import json
import time
import logging
from pprint import pprint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API configuration
API_URL = "http://localhost:8000/api/v2/analysis/dfm"
API_KEY = "dev_api_key_for_testing"  # Default development API key

def create_sample_cad_data():
    """Create a sample CAD model for testing"""
    return {
        "part_name": "test_bracket",
        "volume": 125000.0,
        "surface_area": 15000.0,
        "bounding_box": {
            "length": 100.0,
            "width": 50.0,
            "height": 25.0
        },
        "center_of_mass": {
            "x": 50.0,
            "y": 25.0,
            "z": 12.5
        },
        "holes": [
            {
                "diameter": 10.0,
                "depth": 25.0,
                "position": {"x": 25.0, "y": 25.0, "z": 0.0}
            },
            {
                "diameter": 5.0,
                "depth": 10.0,
                "position": {"x": 75.0, "y": 25.0, "z": 0.0}
            }
        ],
        "thin_walls": [
            {
                "thickness": 2.0,
                "area": 500.0,
                "position": {"x": 50.0, "y": 0.0, "z": 12.5}
            }
        ],
        "faces": 24
    }

def create_dfm_request(cad_data, material="ALUMINUM", volume=100):
    """Create a DFM analysis request"""
    return {
        "cad_data": cad_data,
        "material": material,
        "production_volume": volume,
        "processes": ["CNC_MILLING", "INJECTION_MOLDING", "FDM_PRINTING"]
    }

def send_dfm_request(request_data):
    """Send DFM analysis request to API"""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    logger.info(f"Sending DFM analysis request for {request_data['cad_data']['part_name']}")
    
    try:
        response = requests.post(API_URL, json=request_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        raise

def display_results(results):
    """Display DFM analysis results in a user-friendly format"""
    print("\n" + "="*50)
    print(f"DFM ANALYSIS RESULTS FOR: {results['cad_data']['part_name']}")
    print("="*50)
    
    # Overall manufacturability
    print(f"\nMANUFACTURABILITY SCORE: {results.get('manufacturability_score', 'N/A')}/100")
    
    # Issues
    if 'issues' in results and results['issues']:
        print("\nMANUFACTURING ISSUES:")
        for issue in results['issues']:
            print(f"  • [{issue['severity'].upper()}] {issue['message']}")
            if 'recommendation' in issue:
                print(f"    → Recommendation: {issue['recommendation']}")
    else:
        print("\nNo manufacturing issues detected.")
    
    # Process recommendations
    if 'process_suitability' in results and results['process_suitability']:
        print("\nPROCESS RECOMMENDATIONS:")
        for i, process in enumerate(results['process_suitability'], 1):
            print(f"\n{i}. {process['process'].replace('_', ' ')} - Score: {process['suitability_score']}/100")
            print(f"   Manufacturability: {process['manufacturability']}")
            print(f"   Estimated Cost: ${process.get('estimated_unit_cost', 'N/A')}")
            print(f"   Lead Time: {process.get('estimated_lead_time', 'N/A')} days")
            
            if 'advantages' in process and process['advantages']:
                print("   Advantages:")
                for adv in process['advantages']:
                    print(f"    ✓ {adv}")
                    
            if 'limitations' in process and process['limitations']:
                print("   Limitations:")
                for lim in process['limitations']:
                    print(f"    ✗ {lim}")
    
    # Complexity analysis
    if 'metadata' in results and 'complexity_score' in results['metadata']:
        print(f"\nCOMPLEXITY ANALYSIS:")
        print(f"  • Overall Complexity: {results['metadata']['complexity_rating']} ({results['metadata']['complexity_score']}/100)")
        
        if 'complexity_factors' in results['metadata']:
            factors = results['metadata']['complexity_factors']
            print("  • Complexity Factors:")
            for factor, value in factors.items():
                print(f"    - {factor.replace('_', ' ').title()}: {value}")
    
    # Machining time
    if 'metadata' in results and 'machining_time' in results['metadata']:
        times = results['metadata']['machining_time']
        print(f"\nESTIMATED MACHINING TIME:")
        print(f"  • Total Time: {times.get('total_time_minutes', 'N/A')} minutes")
        print(f"  • Setup Time: {times.get('setup_time_minutes', 'N/A')} minutes")
        print(f"  • Rough Machining: {times.get('rough_machining_minutes', 'N/A')} minutes")
        print(f"  • Finish Machining: {times.get('finish_machining_minutes', 'N/A')} minutes")
        print(f"  • Hole Operations: {times.get('hole_operations_minutes', 'N/A')} minutes")
    
    print("\n" + "="*50)

def main():
    """Main function"""
    try:
        # Create sample CAD data
        cad_data = create_sample_cad_data()
        
        # Create DFM request
        request = create_dfm_request(cad_data)
        
        # Send request to API
        start_time = time.time()
        results = send_dfm_request(request)
        end_time = time.time()
        
        # Display results
        display_results(results)
        
        # Display performance
        print(f"\nRequest completed in {end_time - start_time:.2f} seconds")
        
        return 0
    except Exception as e:
        logger.error(f"Error in main: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
