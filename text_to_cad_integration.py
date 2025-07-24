"""
Text-to-CAD Integration Module for FreeCAD Cloud Co-Pilot
Handles integration between the StandaloneCoPilot.FCMacro and the Text-to-CAD cloud service
"""

import os
import json
import time
import traceback
import requests
from typing import Dict, Any, Optional, List, Tuple, Callable

class TextToCADIntegration:
    """
    Text-to-CAD Integration for FreeCAD Cloud Co-Pilot
    Handles communication with the Text-to-CAD cloud service and processes responses
    """
    
    def __init__(self, config_path: Optional[str] = None, cloud_client=None):
        """Initialize the Text-to-CAD integration
        
        Args:
            config_path: Path to configuration file
            cloud_client: Existing cloud client instance (optional)
        """
        self.config_path = config_path
        self.cloud_client = cloud_client
        self.config = {}
        self.connected = False
        self.last_error = None
        self.capabilities = []
        self.endpoint = None
        self.session = requests.Session()
        
        # Load configuration
        self._load_configuration()
        
        # Test connection
        self.test_connection()
        
        print(f"Text-to-CAD Integration initialized, connected: {self.connected}")
    
    def _load_configuration(self):
        """Load configuration from file"""
        try:
            if self.config_path and os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                print("Text-to-CAD configuration loaded successfully")
            else:
                print("No configuration file found, using defaults")
                self.config = {
                    "text_to_cad_endpoint": "https://text-to-cad-agent-xxx-uc.a.run.app",
                    "text_to_cad_api_key": None
                }
        except Exception as e:
            print(f"Error loading Text-to-CAD configuration: {str(e)}")
            traceback.print_exc()
    
    def test_connection(self) -> bool:
        """Test connection to the Text-to-CAD cloud service
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        if self.cloud_client and hasattr(self.cloud_client, 'connected') and self.cloud_client.connected:
            # Use existing cloud client if available
            self.connected = True
            return True
            
        try:
            endpoint = self.config.get("text_to_cad_endpoint", "https://text-to-cad-agent-xxx-uc.a.run.app")
            api_key = self.config.get("text_to_cad_api_key")
            
            self.endpoint = endpoint  # Store endpoint for reference
            
            headers = {}
            if api_key:
                headers['Authorization'] = f"Bearer {api_key}"
                
            print(f"Testing connection to {endpoint}...")
                
            # Test health endpoint
            response = requests.get(f"{endpoint}/health", headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.connected = True
                print(f"Connected successfully to {endpoint}")
                
                # Get capabilities
                try:
                    capabilities_response = requests.get(f"{endpoint}/list-capabilities", headers=headers, timeout=10)
                    if capabilities_response.status_code == 200:
                        data = capabilities_response.json()
                        self.capabilities = data.get('supported_parts', [])
                        return True
                    else:
                        print(f"Failed to get capabilities: Status code {capabilities_response.status_code}")
                        return False
                except Exception as e:
                    print(f"Error getting capabilities: {e}")
                    return False
            else:
                self.last_error = f"Failed to connect to {endpoint}: Status code {response.status_code}"
                print(self.last_error)
                return False
        except Exception as e:
            self.last_error = f"Error connecting to Text-to-CAD service: {e}"
            print(self.last_error)
            return False
    
    def _test_connection(self) -> bool:
        """Test the connection to the Text-to-CAD cloud service
        
        Returns:
            True if the connection is successful, False otherwise
        """
        if not self.cloud_endpoint:
            return False
        
        try:
            response = self.session.get(
                f"{self.cloud_endpoint}/health",
                timeout=5
            )
            
            return response.status_code == 200
        except Exception as e:
            print(f"Error testing connection to Text-to-CAD service: {e}")
            return False
    
    def is_text_to_cad_request(self, text: str) -> bool:
        """Detect if user input is a text-to-CAD request
        
        Args:
            text: User input text
            
        Returns:
            True if this should be routed to text-to-CAD agent
        """
        cad_indicators = [
            # Creation verbs
            'create', 'make', 'generate', 'build', 'design', 'model',
            
            # Object types
            'bicycle', 'bike', 'chassis', 'frame',
            'bottle', 'water bottle', 'flask',
            'gear', 'cog', 'sprocket',
            'bracket', 'mount', 'holder', 'housing',
            'shaft', 'pipe', 'tube', 'cylinder',
            'box', 'cube', 'sphere', 'cone',
            
            # CAD terms
            '3d', 'cad', 'model', 'part', 'component', 'assembly'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in cad_indicators)
    
    def send_request(self, description: str, user_id: str = "freecad_user") -> Dict:
        """Send text-to-CAD request to cloud service
        
        Args:
            description: Natural language description
            user_id: User identifier
            
        Returns:
            Dict containing response from cloud service
        """
        if not self.connected or not self.endpoint:
            return {
                "success": False,
                "message": "Not connected to Text-to-CAD service",
                "fallback_available": True
            }
            
        try:
            payload = {
                'description': description,
                'user_id': user_id,
                'client': 'freecad_macro',
                'timestamp': self._get_timestamp()
            }
            
            response = self.session.post(
                f"{self.endpoint}/text-to-cad",
                json=payload,
                timeout=30  # 30 second timeout
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': 'Request timeout - cloud service not responding',
                'fallback_available': True
            }
            
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'message': 'Cannot connect to cloud service',
                'fallback_available': True
            }
            
        except requests.exceptions.HTTPError as e:
            return {
                'success': False,
                'message': f'HTTP error: {e.response.status_code}',
                'fallback_available': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
                'fallback_available': True
            }
    
    def execute_freecad_code(self, freecad_code: str, progress_callback: Optional[Callable] = None) -> Dict:
        """Execute FreeCAD Python code returned from cloud service
        
        Args:
            freecad_code: Python code to execute in FreeCAD
            progress_callback: Optional function to call for progress updates
            
        Returns:
            Dict with execution results
        """
        try:
            if progress_callback:
                progress_callback(" Executing CAD generation code...")
            
            # Create a safe execution environment
            exec_globals = {
                'print': print
            }
            
            # Try to import FreeCAD module - this should be available within FreeCAD environment
            try:
                # When running inside FreeCAD, the FreeCAD module should already be in the global namespace
                # First check if it's already available in globals
                if 'FreeCAD' in globals():
                    exec_globals['FreeCAD'] = globals()['FreeCAD']
                else:
                    # Try importing it
                    import FreeCAD
                    exec_globals['FreeCAD'] = FreeCAD
            except ImportError as e:
                if progress_callback:
                    progress_callback(f" FreeCAD module not available: {str(e)}")
                return {
                    'success': False,
                    'message': f'Error executing FreeCAD code: FreeCAD module not available - {str(e)}'
                }
            
            # Try to import Part module
            try:
                # Check if Part is already in globals (should be when running in FreeCAD)
                if 'Part' in globals():
                    exec_globals['Part'] = globals()['Part']
                else:
                    import Part
                    exec_globals['Part'] = Part
            except ImportError as e:
                if progress_callback:
                    progress_callback(f" Part module not available: {str(e)}")
                # Don't return error here as the code might not need Part module
            
            # Try to import FreeCADGui if available (for visualization)
            try:
                if 'FreeCADGui' in globals():
                    exec_globals['FreeCADGui'] = globals()['FreeCADGui']
                else:
                    import FreeCADGui
                    exec_globals['FreeCADGui'] = FreeCADGui
            except ImportError:
                # FreeCADGui might not be available in headless mode
                pass
                
            # Add other commonly used modules
            for module_name in ['math', 'random', 'time']:
                try:
                    module = __import__(module_name)
                    exec_globals[module_name] = module
                except ImportError:
                    pass
            
            # Execute the generated code
            exec(freecad_code, exec_globals)
            
            if progress_callback:
                progress_callback(" CAD model generated successfully!")
            
            return {
                'success': True,
                'message': 'FreeCAD code executed successfully'
            }
            
        except Exception as e:
            error_msg = f"Error executing FreeCAD code: {str(e)}"
            
            if progress_callback:
                progress_callback(f" {error_msg}")
            
            return {
                'success': False,
                'message': error_msg,
                'traceback': traceback.format_exc()
            }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        try:
            from datetime import datetime
            return datetime.now().isoformat()
        except:
            return "unknown"
            
    def handle_text_to_cad_request(self, text: str, progress_callback: Optional[Callable] = None) -> Dict:
        """Process user message with potential text-to-CAD routing
        
        Args:
            text: User's natural language input
            progress_callback: Function to call for progress updates
            
        Returns:
            Dict with processing results
        """
        if progress_callback:
            progress_callback(" Processing Text-to-CAD request...")
        
        # Send to cloud service
        cloud_response = self.send_request(text)
        
        if cloud_response.get('success'):
            # Display engineering analysis
            if progress_callback and 'engineering_analysis' in cloud_response:
                progress_callback(cloud_response['engineering_analysis'])
            
            # Execute FreeCAD code
            if 'freecad_code' in cloud_response:
                if progress_callback:
                    progress_callback(" Generating 3D model...")
                
                exec_result = self.execute_freecad_code(
                    cloud_response['freecad_code'],
                    progress_callback
                )
                
                return {
                    'success': exec_result.get('success', False),
                    'message': exec_result.get('message', 'Unknown result'),
                    'engineering_analysis': cloud_response.get('engineering_analysis', ''),
                    'part_type': cloud_response.get('part_type', 'unknown')
                }
            else:
                return {
                    'success': False,
                    'message': 'No FreeCAD code returned from cloud service'
                }
        else:
            # Cloud service failed
            error_msg = cloud_response.get('message', 'Unknown error')
            if progress_callback:
                progress_callback(f" Cloud service error: {error_msg}")
            
            return {
                'success': False,
                'message': error_msg,
                'fallback_available': cloud_response.get('fallback_available', False)
            }
