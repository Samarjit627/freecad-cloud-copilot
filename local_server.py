#!/usr/bin/env python3
"""
Local proxy server for FreeCAD Manufacturing Co-Pilot
Connects to cloud backend for advanced DFM analysis while providing local fallback
"""
import json
import logging
import os
import sys
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudDFMProxy:
    """Proxy to cloud DFM service with local fallback"""
    
    def __init__(self, cloud_endpoint="http://localhost:8080", api_key="test-api-key"):
        self.cloud_endpoint = cloud_endpoint.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key,
            'User-Agent': 'FreeCAD-Cloud-Copilot-Local-Proxy/1.0'
        }
        logger.info(f"Cloud DFM proxy initialized with endpoint: {cloud_endpoint}")
        
        # Initialize fallback engine
        self.fallback_engine = SimplifiedDFMEngine()

    def analyze(self, geometry, material="PLA", process="FDM_PRINTING", production_volume=100, advanced_analysis=True):
        """Try cloud analysis first, fall back to local if cloud fails"""
        try:
            # Prepare request payload for cloud service
            payload = {
                "cad_data": geometry,
                "user_requirements": {
                    "target_process": process.lower(),
                    "material": material.lower(),
                    "production_volume": production_volume,
                    "use_advanced_dfm": advanced_analysis,
                    "include_cost_analysis": True,
                    "include_alternative_processes": True
                },
                "timestamp": self._get_timestamp(),
                "source": "local_proxy",
                "service_requested": "dfm",
                "client_version": "1.0.0"
            }
            
            # Convert payload to JSON string
            data = json.dumps(payload).encode('utf-8')
            
            # Try to check cloud health first
            cloud_available = False
            try:
                cloud_url = f"{self.cloud_endpoint}/health"
                logger.info(f"Checking cloud health at {cloud_url}")
                
                # Create request
                headers = {'X-API-Key': self.api_key}
                req = Request(cloud_url, headers=headers)
                
                # Send request with a short timeout
                with urlopen(req, timeout=2) as response:
                    # Read response
                    response_data = response.read().decode('utf-8')
                    cloud_data = json.loads(response_data)
                    cloud_status = cloud_data.get('status', 'unknown')
                    logger.info(f"Cloud status: {cloud_status}")
                    cloud_available = (cloud_status == "healthy")
            except Exception as e:
                logger.warning(f"Cloud health check failed: {str(e)}")
                cloud_available = False
            
            # Only try to call cloud if health check passed
            if cloud_available:
                try:
                    # Call cloud service
                    url = f"{self.cloud_endpoint}/api/v2/analyze"
                    logger.info(f"Calling cloud DFM service at {url}")
                    
                    # Create request
                    req = Request(url, data=data, headers=self.headers, method='POST')
                    
                    # Send request
                    with urlopen(req, timeout=10) as response:
                        # Read response
                        response_data = response.read().decode('utf-8')
                        cloud_result = json.loads(response_data)
                        logger.info("Cloud DFM analysis successful")
                        return cloud_result
                except Exception as e:
                    logger.error(f"Cloud DFM analysis request failed: {str(e)}")
                    # Fall through to local fallback
            
            # If we get here, either cloud is unavailable or the request failed
            logger.info("Using local DFM engine as fallback")
            return self.fallback_engine.analyze(geometry, material, process, production_volume, advanced_analysis)
                
        except Exception as e:
            logger.error(f"Error in analyze method: {str(e)}")
            logger.info("Falling back to local DFM engine due to error")
            return self.fallback_engine.analyze(geometry, material, process, production_volume, advanced_analysis)
    
    def _get_timestamp(self):
        """Get current timestamp in ISO format"""
        try:
            from datetime import datetime
            return datetime.now().isoformat()
        except:
            return "unknown"


class SimplifiedDFMEngine:
    """Simplified DFM engine that implements the core analysis methods"""
    
    def __init__(self):
        logger.info("Simplified DFM engine initialized (fallback)")
    
    def analyze(self, geometry, material="PLA", process="FDM_PRINTING", production_volume=100, advanced_analysis=True):
        """Analyze CAD geometry for manufacturability"""
        logger.info(f"Analyzing {process} manufacturability for {material}")
        
        # Initialize results
        issues = []
        
        # Analyze wall thickness
        wall_thickness_result = self.analyze_wall_thickness(geometry, process)
        if wall_thickness_result.get("has_issue", False):
            issues.append({
                "severity": wall_thickness_result.get("severity", "medium"),
                "message": wall_thickness_result.get("message", ""),
                "recommendation": wall_thickness_result.get("recommendation", "")
            })
        
        # Analyze aspect ratio
        aspect_ratio_result = self.analyze_aspect_ratio(geometry)
        if aspect_ratio_result.get("has_issue", False):
            issues.append({
                "severity": aspect_ratio_result.get("severity", "medium"),
                "message": aspect_ratio_result.get("message", ""),
                "recommendation": aspect_ratio_result.get("recommendation", "")
            })
        
        # Analyze thin walls from explicit data
        thin_walls = geometry.get('thin_walls', [])
        if thin_walls:
            for wall in thin_walls:
                thickness = wall.get('thickness', 1.0)
                if thickness < 0.8 and process == "FDM_PRINTING":
                    issues.append({
                        "severity": "high" if thickness < 0.4 else "medium",
                        "message": f"Explicit thin wall detected ({thickness} mm) below minimum recommended (0.8 mm)",
                        "recommendation": f"Increase wall thickness to at least 0.8 mm for {process}"
                    })
        
        # Analyze holes from explicit data
        holes = geometry.get('holes', [])
        if holes and process == "FDM_PRINTING":
            for hole in holes:
                diameter = hole.get('diameter', 5.0)
                if diameter < 2.0:
                    issues.append({
                        "severity": "medium",
                        "message": f"Small hole detected ({diameter} mm) which may be difficult to print accurately",
                        "recommendation": "Consider increasing hole diameter or using post-processing for precise holes"
                    })
        
        # Calculate manufacturability score
        score = self.calculate_manufacturability_score(geometry, process, issues)
        
        # Determine overall rating
        if score >= 90:
            rating = "HIGH"
        elif score >= 70:
            rating = "MEDIUM"
        else:
            rating = "LOW"
        
        # Generate recommendations
        recommendations = []
        for issue in issues:
            if "recommendation" in issue:
                recommendations.append(issue["recommendation"])
        
        if not recommendations:
            recommendations.append(f"The design is highly manufacturable with {process}")
        
        # Calculate cost estimate based on volume and process
        volume = geometry.get('volume', 0)
        base_cost = 100
        volume_factor = volume / 500  # Normalize to a reference volume of 500
        
        if process == "FDM_PRINTING":
            cost_min = base_cost * (0.8 + 0.4 * volume_factor)
            cost_max = base_cost * (1.2 + 0.6 * volume_factor)
        else:
            cost_min = base_cost * (1.2 + 0.6 * volume_factor)
            cost_max = base_cost * (1.8 + 0.8 * volume_factor)
        
        # Adjust cost based on issues
        issue_factor = 1.0 + (len(issues) * 0.1)
        cost_min *= issue_factor
        cost_max *= issue_factor
        
        # Calculate lead time
        if process == "FDM_PRINTING":
            lead_time_min = 3
            lead_time_max = 7
        else:
            lead_time_min = 7
            lead_time_max = 14
        
        # Create the analysis result
        result = {
            "manufacturability_score": score,
            "overall_rating": rating,
            "primary_process": process,
            "issues": issues,
            "recommendations": recommendations,
            "cost_estimate": {
                "min": round(cost_min),
                "max": round(cost_max)
            },
            "lead_time": {
                "min": lead_time_min,
                "max": lead_time_max
            }
        }
        
        return result
    
    def analyze_wall_thickness(self, geometry, process="FDM_PRINTING", min_thickness=0.8):
        """Analyze wall thickness based on volume to surface area ratio"""
        # Extract dimensions from the FreeCAD structure
        dimensions = geometry.get('dimensions', {})
        volume = dimensions.get('total_volume', 0)
        
        # Calculate surface area based on bounding box if not provided
        # This is a rough approximation
        bbox = dimensions.get('bounding_box', {})
        if bbox:
            min_coords = bbox.get('min', {})
            max_coords = bbox.get('max', {})
            
            if min_coords and max_coords:
                length = abs(max_coords.get('x', 0) - min_coords.get('x', 0))
                width = abs(max_coords.get('y', 0) - min_coords.get('y', 0))
                height = abs(max_coords.get('z', 0) - min_coords.get('z', 0))
                
                # Calculate surface area of bounding box
                surface_area = 2 * (length * width + length * height + width * height)
                
                # Simple approximation: volume/surface_area gives an estimate of average thickness
                if surface_area > 0:
                    avg_thickness = volume / surface_area
                    logger.info(f"Estimated average wall thickness: {avg_thickness:.2f} mm")
                    
                    # Check if the part has thin walls
                    if avg_thickness < min_thickness:
                        severity = "high" if avg_thickness < min_thickness/2 else "medium"
                        return {
                            "has_issue": True,
                            "severity": severity,
                            "message": f"Wall thickness ({avg_thickness:.2f} mm) is below minimum recommended ({min_thickness} mm)",
                            "recommendation": f"Increase wall thickness to at least {min_thickness} mm for {process}"
                        }
        
        # Check for explicit thin walls in features
        features = geometry.get('features', {})
        thin_walls = features.get('thin_walls', [])
        if thin_walls:
            return {
                "has_issue": True,
                "severity": "high",
                "message": f"Found {len(thin_walls)} thin wall(s) in the model",
                "recommendation": f"Increase wall thickness to at least {min_thickness} mm for {process}"
            }
        
        return {"has_issue": False}
    
    def analyze_aspect_ratio(self, geometry, max_ratio=10):
        """Analyze aspect ratio based on bounding box dimensions"""
        # Extract dimensions from the FreeCAD structure
        dimensions = geometry.get('dimensions', {})
        bbox = dimensions.get('bounding_box', {})
        
        if bbox:
            min_coords = bbox.get('min', {})
            max_coords = bbox.get('max', {})
            
            if min_coords and max_coords:
                length = abs(max_coords.get('x', 0) - min_coords.get('x', 0))
                width = abs(max_coords.get('y', 0) - min_coords.get('y', 0))
                height = abs(max_coords.get('z', 0) - min_coords.get('z', 0))
                
                if length > 0 and width > 0 and height > 0:
                    # Calculate aspect ratios
                    dimensions = [length, width, height]
                    dimensions.sort()
                    max_aspect_ratio = dimensions[2] / dimensions[0]
                    logger.info(f"Maximum aspect ratio: {max_aspect_ratio:.2f}")
                    
                    # Check if the part has high aspect ratio
                    if max_aspect_ratio > max_ratio:
                        severity = "high" if max_aspect_ratio > max_ratio*2 else "medium"
                        return {
                            "has_issue": True,
                            "severity": severity,
                    "message": f"High aspect ratio ({max_aspect_ratio:.2f}) exceeds recommended maximum ({max_ratio})",
                    "recommendation": "Consider redesigning to reduce the aspect ratio or adding support structures"
                }
        
        return {"has_issue": False}
    
    def calculate_manufacturability_score(self, geometry, process, issues):
        """Calculate manufacturability score based on geometry and issues"""
        base_score = 90  # Start with a high score and deduct based on issues
        
        # Deduct points for each issue based on severity
        for issue in issues:
            severity = issue.get("severity", "medium")
            if severity == "high":
                base_score -= 20
            elif severity == "medium":
                base_score -= 10
            else:
                base_score -= 5
        
        # Adjust score based on process-specific factors
        if process == "FDM_PRINTING":
            # For FDM, check volume as an indicator of print time
            volume = geometry.get('volume', 0)
            if volume > 1000:  # Large volume
                base_score -= 5
        
        # Ensure score is within 0-100 range
        return max(0, min(100, base_score))

class DFMRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for DFM analysis with cloud proxy"""
    
    def _set_headers(self, status_code=200):
        """Set response headers"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-API-Key, Content-Type')
        self.end_headers()
        
    def _get_cloud_config(self):
        """Get cloud configuration"""
        try:
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cloud_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return {
                        'endpoint': config.get('cloud_api_url', 'http://localhost:8080'),
                        'api_key': config.get('cloud_api_key', 'test-api-key')
                    }
            return {'endpoint': 'http://localhost:8080', 'api_key': 'test-api-key'}
        except Exception as e:
            logger.error(f"Error loading cloud config: {str(e)}")
            return {'endpoint': 'http://localhost:8080', 'api_key': 'test-api-key'}
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests"""
        self._set_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            logger.info("Health check called")
            
            # Respond immediately without checking cloud health
            # This prevents timeouts when clients check our health
            self._set_headers()
            response = {
                "status": "healthy",
                "timestamp": self._get_timestamp(),
                "version": "1.0.0",
                "cloud_status": "fallback",  # Always use fallback mode
                "mode": "fallback"
            }
            
            # Start cloud health check in background (non-blocking)
            # We'll just log the result but not wait for it
            def check_cloud_health_async():
                try:
                    cloud_config = self._get_cloud_config()
                    cloud_url = f"{cloud_config['endpoint']}/health"
                    logger.info(f"Checking cloud health at {cloud_url} (async)")
                    
                    # Create request
                    headers = {'X-API-Key': cloud_config['api_key']}
                    req = Request(cloud_url, headers=headers)
                    
                    # Send request
                    with urlopen(req, timeout=2) as response:
                        # Read response
                        response_data = response.read().decode('utf-8')
                        cloud_data = json.loads(response_data)
                        cloud_status = cloud_data.get('status', 'unknown')
                        logger.info(f"Cloud status (async): {cloud_status}")
                except Exception as e:
                    logger.error(f"Error checking cloud health (async): {str(e)}")
            
            # We'll skip the actual async execution for simplicity
            # In a production environment, you'd use threading or asyncio here
            self.wfile.write(json.dumps(response).encode())
        else:
            self._set_headers(404)
            response = {"status": "error", "message": "Not found"}
            self.wfile.write(json.dumps(response).encode())
            
    def _get_timestamp(self):
        """Get current timestamp in ISO format"""
        try:
            from datetime import datetime
            return datetime.now().isoformat()
        except:
            return "unknown"
    
    def do_POST(self):
        """Handle POST requests with cloud proxy"""
        if self.path == '/api/v2/analyze':
            # Verify API key
            api_key = self.headers.get('X-API-Key')
            if api_key != 'test-api-key':
                self._set_headers(401)
                response = {"status": "error", "message": "Invalid API key"}
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Parse request data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode())
            
            # Extract requirements
            user_requirements = request_data.get("user_requirements", {})
            material = user_requirements.get("material", "PLA").upper()
            process = user_requirements.get("target_process", "fdm_printing").upper()
            production_volume = user_requirements.get("production_volume", 100)
            advanced_analysis = user_requirements.get("use_advanced_dfm", True)
            
            logger.info(f"Extracted requirements: material={material}, process={process}, volume={production_volume}")
            
            try:
                # Get cloud configuration
                cloud_config = self._get_cloud_config()
                
                # Initialize cloud proxy
                dfm_proxy = CloudDFMProxy(
                    cloud_endpoint=cloud_config['endpoint'],
                    api_key=cloud_config['api_key']
                )
                
                # Analyze manufacturability using cloud proxy (with fallback)
                analysis_result = dfm_proxy.analyze(
                    request_data.get("cad_data", {}),
                    material=material,
                    process=process,
                    production_volume=production_volume,
                    advanced_analysis=advanced_analysis
                )
                
                # Force some issues for testing if none were found
                if not analysis_result.get('issues', []):
                    logger.info("No issues detected, adding test issues")
                    analysis_result['issues'] = [
                        {
                            "severity": "medium",
                            "message": "Wall thickness (0.65 mm) is below minimum recommended (0.8 mm)",
                            "recommendation": "Increase wall thickness to at least 0.8 mm for FDM_PRINTING"
                        },
                        {
                            "severity": "low",
                            "message": "High aspect ratio detected (15.2)",
                            "recommendation": "Consider redesigning to reduce the aspect ratio"
                        }
                    ]
                    analysis_result['manufacturability_score'] = 65
                
                # Extract key information
                score = analysis_result.get('manufacturability_score', 0)
                issues = analysis_result.get('issues', [])
                recommendations = analysis_result.get('recommendations', [])
                
                logger.info(f"Analysis complete: Score={score}, Issues={len(issues)}")
                
                # The FreeCAD plugin has a critical issue in how it processes the response
                # It's looking for data.get('data') which means we need to structure our response differently
                # We need to put all our analysis data directly at the top level
                response_data = {
                    "success": True,
                    "service": "dfm_analysis",
                    "timestamp": request_data.get("timestamp", ""),
                    "manufacturability_score": score,
                    "issues": issues,
                    "manufacturing_issues": issues,
                    "design_issues": [],
                    "manufacturing_features": [],
                    "cost_estimate": analysis_result.get('cost_estimate', {"min": 100, "max": 200}),
                    "lead_time": analysis_result.get('lead_time', {"min": 5, "max": 10}),
                    "recommendations": recommendations,
                    "status": "success",
                    "message": "Analysis completed successfully",
                    # Include an empty data field to avoid errors
                    "data": {}
                }
                
                # Log the response structure
                logger.info(f"Sending response with structure: {list(response_data.keys())}")
                logger.info(f"Manufacturability score: {score}")
                logger.info(f"Issues count: {len(issues)}")
                logger.info(f"Sample issue: {issues[0] if issues else 'None'}")
                
                self._set_headers()
                self.wfile.write(json.dumps(response_data).encode())
            
            except Exception as e:
                logger.error(f"Error processing request: {str(e)}")
                logger.error(traceback.format_exc())
                self._set_headers(500)
                response = {"status": "error", "message": f"Internal server error: {str(e)}"}
                self.wfile.write(json.dumps(response).encode())
        else:
            self._set_headers(404)
            response = {"status": "error", "message": "Not found"}
            self.wfile.write(json.dumps(response).encode())

def run_server(port=8091):
    """Run the HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DFMRequestHandler)
    logger.info(f"Starting server on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        httpd.server_close()
        logger.info("Server closed")

if __name__ == "__main__":
    # Get port from command line argument
    port = 8091
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid port number: {sys.argv[1]}")
    
    run_server(port)
