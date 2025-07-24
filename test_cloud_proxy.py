#!/usr/bin/env python3
"""
Test script for the cloud proxy integration
Tests both direct cloud connection and local server proxy
"""

import json
import logging
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
LOCAL_SERVER_URL = "http://localhost:8090/api/v2/analyze"
CLOUD_SERVER_URL = "http://localhost:8080/api/v2/analyze"
API_KEY = "test-api-key"

def test_server(url, api_key, test_name="Unknown"):
    """Test a server endpoint with a sample request"""
    logger.info(f"=== STARTING {test_name} TEST ===")
    logger.info(f"Testing server at: {url}")
    
    # Create a sample request payload
    payload = {
        "cad_data": {
            "dimensions": {
                "total_volume": 125000,  # 5cm x 5cm x 5cm cube
                "bounding_box": {
                    "min_x": 0, "min_y": 0, "min_z": 0,
                    "max_x": 50, "max_y": 50, "max_z": 50
                }
            },
            "features": {
                "holes": [
                    {"diameter": 5, "depth": 10},
                    {"diameter": 2, "depth": 20}
                ],
                "thin_walls": [
                    {"thickness": 0.5, "area": 100}
                ]
            }
        },
        "user_requirements": {
            "target_process": "fdm_printing",
            "material": "PLA",
            "production_volume": 100,
            "use_advanced_dfm": True,
            "include_cost_analysis": True
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "test_script"
    }
    
    try:
        # Create request
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
        
        # Convert payload to JSON string
        data = json.dumps(payload).encode('utf-8')
        
        # Create request
        logger.info("Sending request...")
        req = Request(url, data=data, headers=headers, method='POST')
        
        # Send request
        with urlopen(req, timeout=30) as response:
            # Read response
            response_data = response.read().decode('utf-8')
            response_json = json.loads(response_data)
            
            # Log status
            logger.info(f"Response status code: 200")
            
            # Print response structure
            logger.info("Response structure:")
            logger.info(f"Keys: {list(response_json.keys())}")
            
            # Check for manufacturability score
            score = response_json.get("manufacturability_score")
            if score is not None:
                logger.info(f"Manufacturability score: {score}")
            else:
                logger.warning("No manufacturability score found in response")
            
            # Check for issues
            issues = response_json.get("issues", [])
            logger.info(f"Issues count: {len(issues)}")
            if issues:
                logger.info("Sample issues:")
                for i, issue in enumerate(issues[:3]):  # Show up to 3 issues
                    logger.info(f"  Issue {i+1}: {issue.get('message')} (Severity: {issue.get('severity')})")
            
            # Check for recommendations
            recommendations = response_json.get("recommendations", [])
            logger.info(f"Recommendations count: {len(recommendations)}")
            if recommendations:
                logger.info("Sample recommendations:")
                for i, rec in enumerate(recommendations[:3]):  # Show up to 3 recommendations
                    logger.info(f"  Recommendation {i+1}: {rec}")
            
            # Check for cost estimate
            cost = response_json.get("cost_estimate", {})
            if cost:
                logger.info(f"Cost estimate: Min={cost.get('min')}, Max={cost.get('max')}")
            
            # Check for lead time
            lead_time = response_json.get("lead_time", {})
            if lead_time:
                logger.info(f"Lead time: Min={lead_time.get('min')}, Max={lead_time.get('max')}")
            
            # Check if this is from cloud or fallback
            if "cloud_status" in response_json:
                logger.info(f"Response source: Cloud (Status: {response_json.get('cloud_status')})")
            else:
                source = "Cloud" if "process_suitability" in response_json else "Local fallback"
                logger.info(f"Response source: {source}")
            
            return True, response_json
    
    except HTTPError as e:
        logger.error(f"Request failed with status code {e.code}")
        logger.error(f"Response: {e.read().decode('utf-8')}")
        return False, None
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False, None

def main():
    """Main function"""
    # First test the local proxy server
    success_local, data_local = test_server(
        LOCAL_SERVER_URL,
        API_KEY,
        "LOCAL PROXY SERVER"
    )
    
    print("\n" + "="*50 + "\n")
    
    # Then test the cloud server directly
    success_cloud, data_cloud = test_server(
        CLOUD_SERVER_URL,
        API_KEY,
        "DIRECT CLOUD SERVER"
    )
    
    print("\n" + "="*50 + "\n")
    
    # Compare results
    if success_local and success_cloud:
        logger.info("COMPARISON: Both servers responded successfully")
        
        # Compare manufacturability scores
        score_local = data_local.get("manufacturability_score")
        score_cloud = data_cloud.get("manufacturability_score")
        if score_local == score_cloud:
            logger.info(f"MATCH: Both servers returned the same manufacturability score: {score_local}")
        else:
            logger.info(f"DIFFERENCE: Local score: {score_local}, Cloud score: {score_cloud}")
        
        # Compare issue counts
        issues_local = len(data_local.get("issues", []))
        issues_cloud = len(data_cloud.get("issues", []))
        if issues_local == issues_cloud:
            logger.info(f"MATCH: Both servers returned the same number of issues: {issues_local}")
        else:
            logger.info(f"DIFFERENCE: Local issues: {issues_local}, Cloud issues: {issues_cloud}")
    
    elif success_local:
        logger.info("Only the local proxy server responded successfully")
    elif success_cloud:
        logger.info("Only the direct cloud server responded successfully")
    else:
        logger.error("Both servers failed to respond")

if __name__ == "__main__":
    main()
