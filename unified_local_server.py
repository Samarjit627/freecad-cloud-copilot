#!/usr/bin/env python3
"""
FreeCAD Manufacturing Co-Pilot Local Server
Unified version that connects to the combined cloud server
"""

import http.server
import socketserver
import json
import urllib.request
import urllib.error
import sys
import os
import time
import logging
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default port
DEFAULT_PORT = 8090

# API Key for authentication
API_KEY = "test-api-key"

class UnifiedCloudProxy:
    """
    Proxy class for communicating with the unified cloud server
    Handles both DFM analysis and Text-to-CAD requests
    """
    
    def __init__(self, cloud_url: str = "http://localhost:8080"):
        """Initialize the cloud proxy with the unified server URL"""
        self.cloud_url = cloud_url
        self.api_key = API_KEY
        logger.info(f"Initialized unified cloud proxy with URL: {cloud_url}")
    
    def analyze_dfm(self, cad_data: Dict[str, Any], user_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send DFM analysis request to the unified cloud server
        
        Args:
            cad_data: CAD data including geometry, features, and metadata
            user_requirements: User requirements including material, process, etc.
            
        Returns:
            Dictionary with manufacturability score, issues, recommendations, cost, and lead time
        """
        logger.info("Sending DFM analysis request to unified cloud server")
        
        # Prepare request data
        request_data = {
            "user_requirements": user_requirements,
            "cad_data": cad_data
        }
        
        # Send request to cloud server
        try:
            response = self._send_request(
                endpoint="/api/v2/analyze",
                data=request_data
            )
            logger.info("Received DFM analysis response from unified cloud server")
            return response
        except Exception as e:
            logger.error(f"Error in DFM analysis request: {e}")
            raise
    
    def generate_text_to_cad(self, prompt: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send Text-to-CAD request to the unified cloud server
        
        Args:
            prompt: Text description of the design
            parameters: Optional parameters for the Text-to-CAD generation
            
        Returns:
            Dictionary with engineering analysis and FreeCAD code
        """
        logger.info(f"Sending Text-to-CAD request to unified cloud server: {prompt[:50]}...")
        
        # Prepare request data
        request_data = {
            "prompt": prompt,
            "parameters": parameters or {
                "detail_level": "medium",
                "output_format": "freecad_python"
            }
        }
        
        # Send request to cloud server
        try:
            response = self._send_request(
                endpoint="/api/v1/text-to-cad",
                data=request_data
            )
            logger.info("Received Text-to-CAD response from unified cloud server")
            return response
        except Exception as e:
            logger.error(f"Error in Text-to-CAD request: {e}")
            raise
    
    def check_health(self) -> Dict[str, Any]:
        """Check the health of the unified cloud server"""
        try:
            url = f"{self.cloud_url}/health"
            headers = {"X-API-Key": self.api_key}
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def _send_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a request to the unified cloud server
        
        Args:
            endpoint: API endpoint to call
            data: Request data
            
        Returns:
            Response data from the server
        """
        url = f"{self.cloud_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        # Convert data to JSON
        data_json = json.dumps(data).encode('utf-8')
        
        # Create request
        req = urllib.request.Request(url, data=data_json, headers=headers, method="POST")
        
        # Send request and get response
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                return response_data
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP error: {e.code} - {e.reason}")
            error_body = e.read().decode('utf-8')
            logger.error(f"Error response: {error_body}")
            raise Exception(f"Cloud server error: {error_body}")
        except urllib.error.URLError as e:
            logger.error(f"URL error: {e.reason}")
            raise Exception(f"Connection error: {e.reason}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

class SimplifiedDFMEngine:
    """
    Simplified DFM engine for local analysis
    Used as a fallback when cloud server is unavailable
    """
    
    def analyze(self, cad_data: Dict[str, Any], user_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform simplified DFM analysis locally
        
        Args:
            cad_data: CAD data including geometry, features, and metadata
            user_requirements: User requirements including material, process, etc.
            
        Returns:
            Dictionary with manufacturability score, issues, recommendations, cost, and lead time
        """
        logger.info("Performing simplified local DFM analysis")
        
        # Extract parameters
        material = user_requirements.get("material", "PLA")
        process = user_requirements.get("target_process", "fdm_printing")
        production_volume = user_requirements.get("production_volume", 100)
        
        # Calculate manufacturability score (simplified)
        score = 75  # Default score
        
        # Generate issues (simplified)
        issues = [
            {
                "type": "simplified_analysis",
                "severity": "low",
                "description": "This is a simplified local analysis. For detailed analysis, ensure cloud server is available."
            }
        ]
        
        # Add a thin walls issue if applicable
        if cad_data.get("geometry", {}).get("min_wall_thickness", 1.0) < 1.0:
            issues.append({
                "type": "thin_walls",
                "severity": "medium",
                "description": "Wall thickness may be too thin for selected process"
            })
        
        # Generate recommendations (simplified)
        recommendations = [
            {
                "type": "cloud_analysis",
                "description": "Use cloud analysis for more detailed recommendations"
            }
        ]
        
        # Calculate cost (simplified)
        volume_cm3 = cad_data.get("metadata", {}).get("volume_cm3", 100)
        unit_cost = volume_cm3 * 0.1  # Simplified cost calculation
        
        cost_estimate = {
            "unit_cost": round(unit_cost, 2),
            "total_cost": round(unit_cost * production_volume, 2),
            "breakdown": {
                "material_cost": round(unit_cost * 0.7, 2),
                "processing_cost": round(unit_cost * 0.3, 2)
            }
        }
        
        # Calculate lead time (simplified)
        lead_time = {
            "min_days": 3,
            "max_days": 7,
            "typical_days": 5
        }
        
        return {
            "manufacturability_score": score,
            "issues": issues,
            "recommendations": recommendations,
            "cost_estimate": cost_estimate,
            "lead_time": lead_time
        }

class SimplifiedTextToCADEngine:
    """
    Simplified Text-to-CAD engine for local generation
    Used as a fallback when cloud server is unavailable
    """
    
    def generate(self, prompt: str) -> Dict[str, Any]:
        """
        Generate simplified Text-to-CAD response locally
        
        Args:
            prompt: Text description of the design
            
        Returns:
            Dictionary with engineering analysis and FreeCAD code
        """
        logger.info("Generating simplified local Text-to-CAD response")
        
        # Generate simplified engineering analysis
        engineering_analysis = f"""# Engineering Analysis for {prompt}

## Overview
This is a simplified local analysis. For detailed analysis, ensure cloud server is available.

## Material Considerations
For this design, PLA would be an appropriate material choice based on the requirements.

## Structural Considerations
The design should be created with appropriate wall thickness and internal supports to ensure structural integrity.
"""
        
        # Generate simplified FreeCAD code
        freecad_code = """# FreeCAD Python code for a simple part
import FreeCAD as App
import Part

# Create a new document
doc = App.newDocument("SimplePart")

# Create a box
box = doc.addObject("Part::Box", "Box")
box.Length = 50.0
box.Width = 30.0
box.Height = 10.0

# Recompute the document
doc.recompute()
App.ActiveDocument = doc
App.ActiveDocument.recompute()

print("Simple part created successfully")
"""
        
        return {
            "prompt": prompt,
            "engineering_analysis": engineering_analysis,
            "freecad_code": freecad_code,
            "metadata": {
                "generated_locally": True,
                "simplified": True
            }
        }

class RequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for the local server"""
    
    def __init__(self, *args, **kwargs):
        # Initialize cloud proxy
        self.cloud_proxy = UnifiedCloudProxy()
        
        # Initialize fallback engines
        self.simplified_dfm_engine = SimplifiedDFMEngine()
        self.simplified_text_to_cad_engine = SimplifiedTextToCADEngine()
        
        # Call parent constructor
        super().__init__(*args, **kwargs)
    
    def _set_headers(self, status_code=200):
        """Set response headers"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-API-Key, Content-Type')
        self.end_headers()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self._set_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            # Health check endpoint
            self._set_headers()
            
            # Check cloud server health
            cloud_health = self.cloud_proxy.check_health()
            
            # Prepare response
            response = {
                "status": "healthy",
                "timestamp": time.time(),
                "local_server": {
                    "status": "healthy"
                },
                "cloud_server": cloud_health
            }
            
            self.wfile.write(json.dumps(response).encode())
        else:
            # Unknown endpoint
            self._set_headers(404)
            response = {"status": "error", "message": "Endpoint not found"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/v2/analyze':
            # DFM analysis endpoint
            self._handle_dfm_analysis()
        elif self.path == '/api/v1/text-to-cad':
            # Text-to-CAD endpoint
            self._handle_text_to_cad()
        else:
            # Unknown endpoint
            self._set_headers(404)
            response = {"status": "error", "message": "Endpoint not found"}
            self.wfile.write(json.dumps(response).encode())
    
    def _handle_dfm_analysis(self):
        """Handle DFM analysis requests"""
        # Verify API key
        api_key = self.headers.get('X-API-Key')
        if api_key != API_KEY:
            self._set_headers(401)
            response = {"status": "error", "message": "Invalid API key"}
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Parse request
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        request_data = json.loads(post_data.decode('utf-8'))
        
        # Extract data
        user_requirements = request_data.get("user_requirements", {})
        cad_data = request_data.get("cad_data", {})
        
        # Log request
        logger.info(f"Received DFM analysis request for material: {user_requirements.get('material')}")
        
        try:
            # Try to use cloud server
            result = self.cloud_proxy.analyze_dfm(cad_data, user_requirements)
            logger.info("Using cloud DFM analysis result")
        except Exception as e:
            # Fall back to simplified local analysis
            logger.warning(f"Cloud DFM analysis failed, using local fallback: {e}")
            result = self.simplified_dfm_engine.analyze(cad_data, user_requirements)
            result["cloud_error"] = str(e)
            result["using_fallback"] = True
        
        # Send response
        self._set_headers()
        self.wfile.write(json.dumps(result).encode())
    
    def _handle_text_to_cad(self):
        """Handle Text-to-CAD requests"""
        # Verify API key
        api_key = self.headers.get('X-API-Key')
        if api_key != API_KEY:
            self._set_headers(401)
            response = {"status": "error", "message": "Invalid API key"}
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Parse request
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        request_data = json.loads(post_data.decode('utf-8'))
        
        # Extract data
        prompt = request_data.get("prompt", "")
        parameters = request_data.get("parameters", {})
        
        # Log request
        logger.info(f"Received Text-to-CAD request: {prompt[:50]}...")
        
        try:
            # Try to use cloud server
            result = self.cloud_proxy.generate_text_to_cad(prompt, parameters)
            logger.info("Using cloud Text-to-CAD result")
        except Exception as e:
            # Fall back to simplified local generation
            logger.warning(f"Cloud Text-to-CAD failed, using local fallback: {e}")
            result = self.simplified_text_to_cad_engine.generate(prompt)
            result["cloud_error"] = str(e)
            result["using_fallback"] = True
        
        # Send response
        self._set_headers()
        self.wfile.write(json.dumps(result).encode())

def run_server(port=DEFAULT_PORT):
    """Run the local server on the specified port"""
    handler = lambda *args, **kwargs: RequestHandler(*args, **kwargs)
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        logger.info(f"Starting FreeCAD Manufacturing Co-Pilot Local Server on port {port}")
        logger.info(f"Unified server handles both DFM analysis and Text-to-CAD requests")
        logger.info(f"Press Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        finally:
            httpd.server_close()
            logger.info("Server closed")

if __name__ == "__main__":
    # Get port from command line arguments or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    
    # Run the server
    run_server(port)
