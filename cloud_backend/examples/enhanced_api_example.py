#!/usr/bin/env python3
"""
Enhanced API Example Script

This script demonstrates how to use the enhanced CAD analysis API endpoints
for both single part analysis and batch processing.
"""

import requests
import json
import time
import argparse
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default API base URL
DEFAULT_API_URL = "http://localhost:8000/api/v2"


def load_sample_cad_data(filename):
    """
    Load sample CAD data from a JSON file
    
    Args:
        filename: Path to JSON file
        
    Returns:
        CAD data dictionary
    """
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading sample data: {e}")
        raise


def analyze_single_part(api_url, cad_data, material="ALUMINUM", volume=100):
    """
    Analyze a single part using the enhanced DFM analysis endpoint
    
    Args:
        api_url: API base URL
        cad_data: CAD geometry data
        material: Material type
        volume: Production volume
        
    Returns:
        Analysis response
    """
    logger.info(f"Analyzing part: {cad_data.get('part_name', 'unknown')}")
    
    # Create request payload
    payload = {
        "cad_data": cad_data,
        "material": material,
        "production_volume": volume,
        "processes": ["CNC_MILLING", "INJECTION_MOLDING", "FDM_PRINTING"]
    }
    
    # Send request
    try:
        response = requests.post(f"{api_url}/analysis/dfm", json=payload)
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        logger.info(f"Analysis complete. Manufacturability score: {result.get('manufacturability_score')}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        raise


def analyze_with_legacy_endpoint(api_url, legacy_data, material="ALUMINUM", volume=100):
    """
    Analyze a part using the legacy CAD analysis endpoint with enhanced capabilities
    
    Args:
        api_url: API base URL
        legacy_data: Legacy CAD data
        material: Material type
        volume: Production volume
        
    Returns:
        Analysis response
    """
    logger.info(f"Analyzing part with legacy endpoint: {legacy_data.get('part_name', 'unknown')}")
    
    # Send request
    try:
        response = requests.post(
            f"{api_url}/analysis/cad",
            json=legacy_data,
            params={"material": material, "volume": volume}
        )
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        logger.info(f"Analysis complete. Manufacturability score: {result.get('manufacturability_score')}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        raise


def process_batch(api_url, cad_data_list, material="ALUMINUM", volume=100):
    """
    Process multiple parts in batch
    
    Args:
        api_url: API base URL
        cad_data_list: List of CAD geometry data
        material: Material type
        volume: Production volume
        
    Returns:
        Batch processing result
    """
    logger.info(f"Processing batch of {len(cad_data_list)} parts")
    
    # Create request payload
    requests_data = []
    for cad_data in cad_data_list:
        requests_data.append({
            "cad_data": cad_data,
            "material": material,
            "production_volume": volume,
            "processes": ["CNC_MILLING", "INJECTION_MOLDING"]
        })
    
    payload = {
        "requests": requests_data,
        "callback_url": "https://example.com/api/callback"  # Replace with actual callback URL if needed
    }
    
    # Send request
    try:
        response = requests.post(f"{api_url}/analysis/batch", json=payload)
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        batch_id = result.get("batch_id")
        logger.info(f"Batch processing started with ID: {batch_id}")
        
        # Poll for batch status (in a real application, you might use the callback instead)
        status = poll_batch_status(api_url, batch_id)
        
        return status
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        raise


def poll_batch_status(api_url, batch_id, max_attempts=10, delay=2):
    """
    Poll for batch processing status
    
    Args:
        api_url: API base URL
        batch_id: Batch ID
        max_attempts: Maximum number of polling attempts
        delay: Delay between attempts in seconds
        
    Returns:
        Final batch status
    """
    logger.info(f"Polling for batch status: {batch_id}")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{api_url}/analysis/batch/{batch_id}")
            response.raise_for_status()
            
            status = response.json()
            current_status = status.get("status")
            
            logger.info(f"Batch status: {current_status} ({status.get('message')})")
            
            if current_status in ["completed", "failed"]:
                return status
                
            time.sleep(delay)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Status check failed: {e}")
            time.sleep(delay)
    
    logger.warning(f"Max polling attempts reached for batch {batch_id}")
    return {"status": "unknown", "message": "Max polling attempts reached"}


def get_system_performance(api_url):
    """
    Get system performance metrics
    
    Args:
        api_url: API base URL
        
    Returns:
        Performance metrics
    """
    logger.info("Retrieving system performance metrics")
    
    try:
        response = requests.get(f"{api_url}/system/performance")
        response.raise_for_status()
        
        metrics = response.json()
        logger.info(f"Performance metrics: {json.dumps(metrics, indent=2)}")
        
        return metrics
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get performance metrics: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        raise


def create_sample_cad_data(part_name="sample_part"):
    """
    Create sample CAD data for testing
    
    Args:
        part_name: Part name
        
    Returns:
        Sample CAD data
    """
    return {
        "part_name": part_name,
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


def create_sample_legacy_data(part_name="sample_part"):
    """
    Create sample legacy CAD data for testing
    
    Args:
        part_name: Part name
        
    Returns:
        Sample legacy CAD data
    """
    return {
        "part_name": part_name,
        "dimensions": {
            "length": 100.0,
            "width": 50.0,
            "height": 25.0
        },
        "volume": 125000.0,
        "surface_area": 15000.0,
        "center_of_mass": {
            "x": 50.0,
            "y": 25.0,
            "z": 12.5
        },
        "features": {
            "holes": [
                {
                    "diameter": 10.0,
                    "depth": 25.0,
                    "position": {"x": 25.0, "y": 25.0, "z": 0.0}
                }
            ],
            "thin_walls": [
                {
                    "thickness": 2.0,
                    "area": 500.0,
                    "position": {"x": 50.0, "y": 0.0, "z": 12.5}
                }
            ]
        }
    }


def save_result(result, filename):
    """
    Save analysis result to a JSON file
    
    Args:
        result: Analysis result
        filename: Output filename
    """
    try:
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Result saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving result: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Enhanced API Example Script")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="API base URL")
    parser.add_argument("--mode", choices=["single", "legacy", "batch", "performance"], 
                      default="single", help="Analysis mode")
    parser.add_argument("--material", default="ALUMINUM", help="Material type")
    parser.add_argument("--volume", type=int, default=100, help="Production volume")
    parser.add_argument("--input", help="Input JSON file (optional)")
    parser.add_argument("--output", help="Output JSON file (optional)")
    parser.add_argument("--batch-size", type=int, default=3, help="Batch size for batch mode")
    
    args = parser.parse_args()
    
    try:
        # Load input data if provided
        if args.input:
            cad_data = load_sample_cad_data(args.input)
        else:
            if args.mode == "legacy":
                cad_data = create_sample_legacy_data()
            else:
                cad_data = create_sample_cad_data()
        
        # Process according to mode
        if args.mode == "single":
            result = analyze_single_part(args.api_url, cad_data, args.material, args.volume)
        elif args.mode == "legacy":
            result = analyze_with_legacy_endpoint(args.api_url, cad_data, args.material, args.volume)
        elif args.mode == "batch":
            # Create multiple sample parts
            cad_data_list = [
                create_sample_cad_data(f"sample_part_{i}") 
                for i in range(args.batch_size)
            ]
            result = process_batch(args.api_url, cad_data_list, args.material, args.volume)
        elif args.mode == "performance":
            result = get_system_performance(args.api_url)
        
        # Save result if output file specified
        if args.output:
            save_result(result, args.output)
            
        # Print summary
        print("\nAnalysis Summary:")
        if args.mode in ["single", "legacy"]:
            print(f"Part: {cad_data.get('part_name')}")
            print(f"Manufacturability Score: {result.get('manufacturability_score')}")
            if "process_suitability" in result and result["process_suitability"]:
                top_process = result["process_suitability"][0]
                print(f"Recommended Process: {top_process.get('process')}")
                print(f"Estimated Unit Cost: ${top_process.get('estimated_unit_cost')}")
            elif "recommended_processes" in result and result["recommended_processes"]:
                top_process = result["recommended_processes"][0]
                print(f"Recommended Process: {top_process.get('process')}")
                print(f"Estimated Unit Cost: ${top_process.get('cost_estimate')}")
        elif args.mode == "batch":
            print(f"Batch ID: {result.get('batch_id')}")
            print(f"Status: {result.get('status')}")
            print(f"Message: {result.get('message')}")
        elif args.mode == "performance":
            metrics = result.get("metrics", {})
            print(f"Total Requests: {metrics.get('total_requests')}")
            print(f"Success Rate: {metrics.get('successful_requests', 0) / max(1, metrics.get('total_requests', 1)):.2%}")
            print(f"Average Processing Time: {metrics.get('average_processing_time')} seconds")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    exit(main())
