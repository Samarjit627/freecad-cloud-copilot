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
        # Check if local fallback is enabled and skip cloud call entirely
        if self.config.get("use_local_fallback", False):
            print("⚠️ Using local fallback mode - skipping cloud API call")
            return self._generate_local_fallback_response(endpoint, payload)
            
        # Check if cloud backend is disabled
        if not self.config.get("use_cloud_backend", True):
            print("⚠️ Cloud backend is disabled - skipping cloud API call")
            return self._generate_local_fallback_response(endpoint, payload)
            
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
                    if self.config.get("use_local_fallback", False):
                        print("⚠️ Using local fallback due to authentication error")
                        return self._generate_local_fallback_response(endpoint, payload)
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
                    if self.config.get("use_local_fallback", False):
                        print("⚠️ Using local fallback due to endpoint not found")
                        return self._generate_local_fallback_response(endpoint, payload)
                    return {
                        "success": False,
                        "error": error_msg,
                        "service": endpoint,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                    }
                elif e.code == 503:
                    error_msg = f"Service unavailable: {endpoint}"
                    print(f"❌ Service unavailable (attempt {attempt+1}/{self.retry_count+1}): {error_msg}")
                    
                    # If we've reached max retries, use local fallback if enabled
                    if attempt == self.retry_count:
                        if self.config.get("use_local_fallback", False):
                            print("⚠️ Using local fallback due to service unavailability")
                            return self._generate_local_fallback_response(endpoint, payload)
                        return {
                            "success": False,
                            "error": error_msg,
                            "service": endpoint,
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                        }
                    # Otherwise wait and retry
                    time.sleep(1)
                else:
                    error_msg = f"HTTP Error {e.code}: {e.reason}"
                    print(f"❌ HTTP error calling service (attempt {attempt+1}/{self.retry_count+1}): {error_msg}")
                    
                    # If we've reached max retries, use local fallback if enabled
                    if attempt == self.retry_count:
                        if self.config.get("use_local_fallback", False):
                            print("⚠️ Using local fallback due to HTTP error")
                            return self._generate_local_fallback_response(endpoint, payload)
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
                
                # If we've reached max retries, use local fallback if enabled
                if attempt == self.retry_count:
                    if self.config.get("use_local_fallback", False):
                        print("⚠️ Using local fallback due to connection error")
                        return self._generate_local_fallback_response(endpoint, payload)
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
                
                if self.config.get("use_local_fallback", False):
                    print("⚠️ Using local fallback due to unexpected error")
                    return self._generate_local_fallback_response(endpoint, payload)
                return {
                    "success": False,
                    "error": error_msg,
                    "service": endpoint,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                }
                
    def _generate_local_fallback_response(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a local fallback response when cloud service is unavailable"""
        print(f"Generating local fallback response for endpoint: {endpoint}")
        
        # Determine which type of response to generate based on the endpoint
        if "/api/analysis/dfm" in endpoint or "/api/v2/analysis/dfm" in endpoint:
            return self._generate_dfm_fallback(payload)
        elif "/api/analysis/cost" in endpoint:
            return self._generate_cost_fallback(payload)
        elif "/api/tools/recommend" in endpoint:
            return self._generate_tool_fallback(payload)
        elif "/health" in endpoint:
            return {
                "success": True,
                "data": {"status": "ok", "mode": "local_fallback"},
                "service": endpoint,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
        else:
            # Generic fallback for unknown endpoints
            return {
                "success": True,
                "data": {
                    "message": "Using local fallback mode",
                    "endpoint": endpoint,
                    "status": "processed_locally"
                },
                "service": endpoint,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
    
    def _generate_dfm_fallback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a fallback DFM analysis response"""
        # Extract basic information from payload
        manufacturing_process = payload.get("manufacturing_process", "3d_printing")
        material = payload.get("material", "pla")
        
        # Generate a basic DFM response with generic recommendations
        return {
            "success": True,
            "data": {
                "manufacturability_score": 75.0,
                "issues": [
                    {
                        "severity": "medium",
                        "title": "Thin walls detected (local analysis)",
                        "description": f"Some walls may be too thin for {manufacturing_process} with {material}.",
                        "recommendation": "Consider increasing wall thickness to improve structural integrity."
                    },
                    {
                        "severity": "low",
                        "title": "Sharp corners (local analysis)",
                        "description": "Sharp corners may cause stress concentration.",
                        "recommendation": "Add fillets to reduce stress concentration."
                    }
                ],
                "recommendations": [
                    {
                        "description": "Increase minimum wall thickness",
                        "impact": "medium",
                        "details": f"For {manufacturing_process}, a minimum wall thickness of 1.5mm is recommended."
                    },
                    {
                        "description": "Add draft angles to vertical faces",
                        "impact": "low",
                        "details": "Adding 1-2° draft angles can improve manufacturability."
                    }
                ],
                "cost_analysis": {
                    "total_cost": 45.0,
                    "material_cost": 15.0,
                    "labor_cost": 20.0,
                    "setup_cost": 10.0,
                    "lead_time": "3-5 days"
                },
                "alternative_processes": [
                    {
                        "process": "CNC_MACHINING",
                        "suitability_score": 65.0,
                        "estimated_cost": 120.0,
                        "lead_time_days": 5,
                        "advantages": ["Better surface finish", "Higher precision"],
                        "limitations": ["Higher cost", "Limited internal geometries"]
                    },
                    {
                        "process": "INJECTION_MOLDING",
                        "suitability_score": 40.0,
                        "estimated_cost": 2000.0,
                        "lead_time_days": 15,
                        "advantages": ["Low per-unit cost at scale", "Excellent repeatability"],
                        "limitations": ["High initial tooling cost", "Only economical for high volumes"]
                    }
                ],
                "analysis_mode": "local_fallback",
                "note": "This is a simplified local analysis. For detailed analysis, please ensure cloud connectivity.",
                "local_fallback": True
            },
            "service": "dfm_analysis",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
    
    def _generate_cost_fallback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a fallback cost estimation response"""
        # Extract basic information from payload
        manufacturing_process = payload.get("manufacturing_process", "3d_printing")
        material = payload.get("material", "pla")
        quantity = payload.get("quantity", 1)
        
        # Calculate basic cost estimate based on process and quantity
        base_cost = 30.0
        if manufacturing_process == "cnc_machining":
            base_cost = 80.0
        elif manufacturing_process == "injection_molding":
            base_cost = 1500.0
        
        # Apply quantity discount
        if quantity > 10:
            unit_cost = base_cost * 0.9
        elif quantity > 100:
            unit_cost = base_cost * 0.7
        else:
            unit_cost = base_cost
            
        total_cost = unit_cost * quantity
        
        return {
            "success": True,
            "data": {
                "total_cost": total_cost,
                "unit_cost": unit_cost,
                "quantity": quantity,
                "breakdown": {
                    "material": unit_cost * 0.3,
                    "labor": unit_cost * 0.4,
                    "overhead": unit_cost * 0.2,
                    "profit": unit_cost * 0.1
                },
                "lead_time": "5-7 business days",
                "analysis_mode": "local_fallback",
                "note": "This is an estimated cost generated locally. For accurate pricing, please ensure cloud connectivity.",
                "local_fallback": True
            },
            "service": "cost_estimation",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
    
    def _generate_tool_fallback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a fallback tool recommendation response"""
        # Extract basic information from payload
        manufacturing_process = payload.get("manufacturing_process", "cnc_machining")
        material = payload.get("material", "aluminum")
        
        # Generate generic tool recommendations based on process and material
        tools = []
        
        if manufacturing_process == "cnc_machining":
            if material in ["aluminum", "brass"]:
                tools = [
                    {"name": "End Mill", "diameter": 6.0, "flutes": 2, "material": "HSS", "coating": "TiAlN"},
                    {"name": "Ball Nose", "diameter": 4.0, "flutes": 2, "material": "Carbide", "coating": "None"},
                    {"name": "Drill Bit", "diameter": 5.0, "flutes": 2, "material": "HSS", "coating": "TiN"}
                ]
            else:  # Steel or other harder materials
                tools = [
                    {"name": "End Mill", "diameter": 6.0, "flutes": 4, "material": "Carbide", "coating": "TiAlN"},
                    {"name": "Ball Nose", "diameter": 4.0, "flutes": 4, "material": "Carbide", "coating": "AlTiN"},
                    {"name": "Drill Bit", "diameter": 5.0, "flutes": 2, "material": "Carbide", "coating": "TiN"}
                ]
        
        return {
            "success": True,
            "data": {
                "recommended_tools": tools,
                "machine_settings": {
                    "spindle_speed": "10000 RPM",
                    "feed_rate": "1000 mm/min",
                    "step_down": "0.5 mm"
                },
                "analysis_mode": "local_fallback",
                "note": "These are generic tool recommendations. For optimized tooling, please ensure cloud connectivity.",
                "local_fallback": True
            },
            "service": "tool_recommendation",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
