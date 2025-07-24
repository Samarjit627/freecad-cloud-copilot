#!/usr/bin/env python3
"""
Test script to verify the deployed backend with a properly formatted request
"""
import json
import requests
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL
BACKEND_URL = "https://freecad-copilot-fixed-4cmxv2m7cq-el.a.run.app/api/v2/analyze"
API_KEY = "test-api-key"

def load_test_request(file_path):
    """Load test request from JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading test request: {str(e)}")
        return None

def send_request(data):
    """Send request to backend API"""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    try:
        logger.info(f"Sending request to {BACKEND_URL}...")
        start_time = time.time()
        response = requests.post(BACKEND_URL, json=data, headers=headers, timeout=30)
        elapsed_time = time.time() - start_time
        
        logger.info(f"Request completed in {elapsed_time:.2f} seconds")
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error response: {response.text}")
            return None
    except requests.exceptions.Timeout:
        logger.error("Request timed out after 30 seconds")
        return None
    except Exception as e:
        logger.error(f"Error sending request: {str(e)}")
        return None

def analyze_response(response):
    """Analyze and log the response"""
    if not response:
        logger.error("No response to analyze")
        return
    
    logger.info("Response analysis:")
    logger.info(f"Status: {response.get('status', 'unknown')}")
    
    if response.get('status') == 'error':
        logger.error(f"Error message: {response.get('message', 'No error message')}")
    
    data = response.get('data', {})
    logger.info(f"Manufacturability score: {data.get('manufacturability_score', 0)}")
    
    issues = data.get('manufacturing_issues', [])
    logger.info(f"Found {len(issues)} manufacturing issues")
    
    if issues:
        logger.info("Manufacturing issues:")
        for i, issue in enumerate(issues):
            logger.info(f"  {i+1}. {issue.get('message', '')} (Severity: {issue.get('severity', 'unknown')})")
            logger.info(f"     Recommendation: {issue.get('recommendation', 'None')}")
    
    recommendations = data.get('recommendations', [])
    if recommendations:
        logger.info("Recommendations:")
        for i, rec in enumerate(recommendations):
            logger.info(f"  {i+1}. {rec}")
    
    # Print the full response for debugging
    logger.info("\nFull response:")
    logger.info(json.dumps(response, indent=2))

def main():
    """Main function"""
    # Load test request
    test_data = load_test_request("test_request.json")
    if not test_data:
        return
    
    # Send request
    response = send_request(test_data)
    
    # Analyze response
    analyze_response(response)

if __name__ == "__main__":
    main()
