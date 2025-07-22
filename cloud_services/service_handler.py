"""
Cloud Service Handler for FreeCAD CoPilot
Handles communication with cloud services for DFM, cost estimation, and tool features
"""

import os
import sys
import json
import time
import traceback
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional, Union

class CloudServiceHandler:
    """Handler for cloud-based manufacturing intelligence services"""
    
    def __init__(self, config_path=None):
        """Initialize the cloud service handler with configuration"""
        # Initialize debug_mode with default value before loading config
        self.debug_mode = False
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Set attributes from config
        self.base_url = self.config.get("cloud_api_url", "https://freecad-copilot-service.run.app")
        self.api_key = self.config.get("cloud_api_key", "")
        self.timeout = self.config.get("connection_timeout", 30)
        self.retry_count = self.config.get("retry_count", 3)
        self.debug_mode = self.config.get("enable_debug_mode", False)
        
    def _load_config(self, config_path=None) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            # Default config path
            if config_path is None:
                # Try to find the config file relative to this file
                this_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(this_dir)
                config_path = os.path.join(parent_dir, "cloud_config.json")
            
            # Load the config file
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            if self.debug_mode:
                print(f"Loaded cloud configuration from {config_path}")
                
            return config
            
        except Exception as e:
            print(f"Error loading cloud configuration: {str(e)}")
            # Return default configuration
            return {
                "cloud_api_url": "https://freecad-copilot-service.run.app",
                "cloud_api_key": "",
                "connection_timeout": 30,
                "retry_count": 3,
                "enable_debug_mode": False
            }
    
    def call_service(self, service_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a cloud service with the provided payload
        
        Args:
            service_name: Name of the service to call (dfm, cost, tool_recommendation)
            payload: Data to send to the service
            
        Returns:
            Dict containing the service response or error information
        """
        # Get the appropriate endpoint
        endpoint = self._get_endpoint_for_service(service_name)
        
        # Add metadata to payload
        enriched_payload = self._enrich_payload(payload, service_name)
        
        # Call the service
        return self._make_api_call(endpoint, enriched_payload)
    
    def _get_endpoint_for_service(self, service_name: str) -> str:
        """Get the appropriate endpoint for a service"""
        service_endpoints = {
            "dfm": self.config.get("dfm_endpoint", "/api/analysis/dfm"),
            "cost": self.config.get("cost_endpoint", "/api/analysis/cost"),
            "tool_recommendation": self.config.get("tool_endpoint", "/api/tools/recommend"),
            "general_analysis": self.config.get("default_analysis_endpoint", "/api/analysis/cad")
        }
        
        # Get the endpoint or fall back to the default
        endpoint = service_endpoints.get(
            service_name, 
            self.config.get("default_analysis_endpoint", "/api/analysis/cad")
        )
        
        return endpoint
    
    def _enrich_payload(self, payload: Dict[str, Any], service_name: str) -> Dict[str, Any]:
        """Add metadata to the payload"""
        # Create a copy to avoid modifying the original
        enriched = payload.copy() if payload else {}
        
        # Add metadata
        enriched.update({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "source": "freecad_copilot",
            "service_requested": service_name,
            "client_version": "1.1.0"
        })
        
        return enriched
    
    def _make_api_call(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make the actual API call to the cloud service"""
        full_url = f"{self.base_url}{endpoint}"
        
        if self.debug_mode:
            print(f"Calling cloud service: {full_url}")
            
        # Try to make the request with retries
        for attempt in range(self.retry_count + 1):
            try:
                # Convert payload to JSON
                data = json.dumps(payload).encode('utf-8')
                
                # Create request with headers
                headers = {
                    'Content-Type': 'application/json',
                    'User-Agent': 'FreeCAD-CoPilot/1.1.0'
                }
                
                # Add API key if available
                if self.api_key:
                    # Use X-API-Key header for authentication
                    headers['X-API-Key'] = self.api_key
                    
                    if self.debug_mode:
                        print("Using X-API-Key authentication")
                
                # Create the request
                req = urllib.request.Request(
                    full_url,
                    data=data,
                    headers=headers
                )
                
                # Make the request
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    response_data = response.read().decode('utf-8')
                    result = json.loads(response_data)
                
                if self.debug_mode:
                    print(f"✅ Cloud service call successful: {endpoint}")
                    
                return {
                    "success": True,
                    "data": result,
                    "service": endpoint,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                }
                
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    error_msg = f"Authentication failed: Please verify your API key is correct"
                    print(f"❌ Authentication error: {error_msg}")
                    # Don't retry authentication errors
                    return {
                        "success": False,
                        "error": error_msg,
                        "service": endpoint,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                    }
                elif e.code == 404:
                    error_msg = f"Endpoint not found: {endpoint}"
                    print(f"❌ Endpoint error: {error_msg}")
                    # Don't retry 404 errors
                    return {
                        "success": False,
                        "error": error_msg,
                        "service": endpoint,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                    }
                else:
                    error_msg = f"HTTP Error {e.code}: {e.reason}"
                    print(f"❌ HTTP error calling service (attempt {attempt+1}/{self.retry_count+1}): {error_msg}")
                    
                    # If we've reached max retries, return error
                    if attempt == self.retry_count:
                        return {
                            "success": False,
                            "error": error_msg,
                            "service": endpoint,
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                        }
                    
                    # Otherwise wait and retry
                    time.sleep(1)
                
            except urllib.error.URLError as e:
                error_msg = f"Connection error: {str(e.reason)}"
                print(f"❌ Connection error calling service (attempt {attempt+1}/{self.retry_count+1}): {error_msg}")
                
                # If we've reached max retries, return error
                if attempt == self.retry_count:
                    return {
                        "success": False,
                        "error": error_msg,
                        "service": endpoint,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                    }
                    
                # Otherwise wait and retry
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                print(f"❌ Unexpected error calling service: {error_msg}")
                traceback.print_exc()
                
                return {
                    "success": False,
                    "error": error_msg,
                    "service": endpoint,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                }
