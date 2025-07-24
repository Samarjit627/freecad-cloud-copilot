#!/usr/bin/env python3
"""
Test script to verify dynamic manufacturability analysis with different CAD models
"""
import json
import requests
import time
import sys
import logging
from pprint import pprint

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API endpoints
LOCAL_ENDPOINT = "http://localhost:8000/api/v1/enhanced-analysis-fixed"
CLOUD_ENDPOINT = "https://freecad-copilot-fixed-ue4roa4m4a-el.a.run.app/api/v1/enhanced-analysis-fixed"

# Choose which endpoint to use (local or cloud)
USE_CLOUD = True
API_ENDPOINT = CLOUD_ENDPOINT if USE_CLOUD else LOCAL_ENDPOINT
API_KEY = "test-api-key"  # Using the test key that's accepted by our modified backend

def create_test_cad_data(part_name, volume, surface_area, bounding_box):
    """Create test CAD data with different geometries"""
    return {
        "part_name": part_name,
        "volume": volume,
        "surface_area": surface_area,
        "bounding_box": bounding_box,
        "center_of_mass": {"x": 0, "y": 0, "z": 0},
        "holes": [],
        "thin_walls": []
    }

def test_analysis(cad_data, material="PLA", process="FDM_PRINTING"):
    """Test the analysis endpoint with the given CAD data"""
    payload = {
        "cad_data": cad_data,
        "material": material,
        "process": process,
        "production_volume": 100,
        "advanced_analysis": True
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    logger.info(f"Testing analysis for part: {cad_data['part_name']}")
    logger.info(f"Volume: {cad_data['volume']}, Surface Area: {cad_data['surface_area']}")
    
    try:
        response = requests.post(API_ENDPOINT, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Extract key information
        score = result.get("overall_manufacturability_score", 0)
        rating = result.get("overall_rating", "UNKNOWN")
        issues = result.get("manufacturing_issues", [])
        recommendations = result.get("expert_recommendations", [])
        
        logger.info(f"Analysis results for {cad_data['part_name']}:")
        logger.info(f"Score: {score}/100 ({rating})")
        logger.info(f"Found {len(issues)} manufacturing issues")
        
        if issues:
            logger.info("Issues:")
            for i, issue in enumerate(issues):
                logger.info(f"  {i+1}. {issue.get('message', '')} (Severity: {issue.get('severity', 'unknown')})")
                logger.info(f"     Recommendation: {issue.get('recommendation', 'None')}")
        
        if recommendations:
            logger.info("Recommendations:")
            for i, rec in enumerate(recommendations):
                logger.info(f"  {i+1}. {rec}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error testing analysis: {str(e)}")
        return None

def main():
    """Run tests with different CAD models"""
    # Test 1: Good part with reasonable dimensions
    good_part = create_test_cad_data(
        "good_part",
        volume=500.0,
        surface_area=300.0,
        bounding_box={"length": 100.0, "width": 80.0, "height": 60.0}
    )
    
    # Test 2: Part with thin walls (low volume to surface area ratio)
    thin_wall_part = create_test_cad_data(
        "thin_wall_part",
        volume=50.0,
        surface_area=300.0,  # Same surface area but much lower volume
        bounding_box={"length": 100.0, "width": 80.0, "height": 60.0}
    )
    
    # Test 3: Part with high aspect ratio
    high_aspect_ratio_part = create_test_cad_data(
        "high_aspect_ratio_part",
        volume=500.0,
        surface_area=300.0,
        bounding_box={"length": 200.0, "width": 10.0, "height": 5.0}  # Very long and thin
    )
    
    # Run tests
    logger.info("Starting dynamic analysis tests...")
    
    logger.info("\n\n=== TEST 1: GOOD PART ===")
    good_result = test_analysis(good_part)
    
    logger.info("\n\n=== TEST 2: THIN WALL PART ===")
    thin_wall_result = test_analysis(thin_wall_part)
    
    logger.info("\n\n=== TEST 3: HIGH ASPECT RATIO PART ===")
    aspect_ratio_result = test_analysis(high_aspect_ratio_part)
    
    # Compare results to verify dynamic behavior
    logger.info("\n\n=== COMPARISON OF RESULTS ===")
    logger.info(f"Good Part Score: {good_result.get('overall_manufacturability_score', 0)}")
    logger.info(f"Thin Wall Part Score: {thin_wall_result.get('overall_manufacturability_score', 0)}")
    logger.info(f"High Aspect Ratio Part Score: {aspect_ratio_result.get('overall_manufacturability_score', 0)}")
    
    logger.info(f"Good Part Issues: {len(good_result.get('manufacturing_issues', []))}")
    logger.info(f"Thin Wall Part Issues: {len(thin_wall_result.get('manufacturing_issues', []))}")
    logger.info(f"High Aspect Ratio Part Issues: {len(aspect_ratio_result.get('manufacturing_issues', []))}")

if __name__ == "__main__":
    main()
