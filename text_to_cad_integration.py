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
                # Use X-API-Key header for authentication with the unified server
                headers['X-API-Key'] = api_key
                
            print(f"Testing connection to {endpoint}...")
                
            # Test health endpoint
            response = requests.get(f"{endpoint}/health", headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.connected = True
                print(f"Connected successfully to {endpoint}")
                
                # Get capabilities
                try:
                    print(f"Requesting capabilities from {endpoint}/list-capabilities")
                    print(f"Using headers: {headers}")
                    
                    capabilities_response = requests.get(f"{endpoint}/list-capabilities", headers=headers, timeout=10)
                    
                    print(f"Capabilities response status code: {capabilities_response.status_code}")
                    print(f"Capabilities response headers: {capabilities_response.headers}")
                    
                    if capabilities_response.status_code == 200:
                        try:
                            data = capabilities_response.json()
                            print(f"Capabilities response data: {data}")
                            self.capabilities = data.get('supported_parts', [])
                            return True
                        except Exception as e:
                            print(f"Error parsing capabilities response as JSON: {e}")
                            print(f"Raw capabilities response: {capabilities_response.text}")
                            return False
                    else:
                        print(f"Failed to get capabilities: Status code {capabilities_response.status_code}")
                        try:
                            print(f"Error response: {capabilities_response.text}")
                        except Exception:
                            pass
                        return False
                except Exception as e:
                    print(f"Error getting capabilities: {e}")
                    traceback.print_exc()
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
                'prompt': description,  # Change 'description' to 'prompt' to match server expectation
                'user_id': user_id,
                'client': 'freecad_macro',
                'timestamp': self._get_timestamp()
            }
            
            # Add X-API-Key header for authentication
            headers = {}
            api_key = self.config.get("text_to_cad_api_key")
            if api_key:
                headers['X-API-Key'] = api_key
            
            print(f"Sending request to {self.endpoint}/text-to-cad with payload: {payload}")
            print(f"Using headers: {headers}")
            
            response = self.session.post(
                f"{self.endpoint}/text-to-cad",
                json=payload,
                headers=headers,
                timeout=30  # 30 second timeout
            )
            
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            
            # Print response content for debugging
            try:
                response_content = response.json()
                print(f"Response content: {response_content}")
            except Exception as e:
                print(f"Error parsing response as JSON: {e}")
                print(f"Raw response: {response.text}")
            
            response.raise_for_status()
            response_data = response.json()
        
            # Add success flag to the response
            response_data['success'] = True
            return response_data
            
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
            error_message = f'HTTP error: {e.response.status_code}'
            try:
                error_detail = e.response.text
                print(f"HTTP Error details: {error_detail}")
                error_message = f'HTTP error {e.response.status_code}: {error_detail}'
            except Exception:
                pass
            
            self.last_error = error_message
            return {
                'success': False,
                'message': error_message,
                'fallback_available': True
            }
            
        except Exception as e:
            error_message = f'Unexpected error: {str(e)}'
            print(f"Detailed error: {error_message}")
            traceback.print_exc()
            self.last_error = error_message
            return {
                'success': False,
                'message': error_message,
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
        if progress_callback:
            progress_callback(" Executing CAD generation code...")
        
        # Clean the code
        freecad_code = self._clean_code(freecad_code)
        
        # Print the code for debugging
        print("Executing FreeCAD code:")
        print(freecad_code)
        
        try:
            # Create a globals dictionary with necessary imports
            exec_globals = {}
            
            # Add FreeCAD module
            try:
                import FreeCAD
                exec_globals['FreeCAD'] = FreeCAD
                exec_globals['App'] = FreeCAD  # Add App alias
            except ImportError as e:
                if progress_callback:
                    progress_callback(f" FreeCAD module not available: {str(e)}")
                return {
                    'success': False,
                    'message': f'Error executing FreeCAD code: FreeCAD module not available - {str(e)}'
                }
            
            # Add Part module
            try:
                import Part
                exec_globals['Part'] = Part
            except ImportError:
                pass
            
            # Add math module
            try:
                import math
                exec_globals['math'] = math
            except ImportError:
                pass
            
            # Try to add FreeCADGui if available
            try:
                import FreeCADGui
                exec_globals['FreeCADGui'] = FreeCADGui
                exec_globals['Gui'] = FreeCADGui  # Add Gui alias
            except ImportError:
                pass  # Headless mode
            
            # Ensure we have an active document
            if FreeCAD.ActiveDocument is None:
                FreeCAD.newDocument("TextToCADModel")
            
            # Make sure the document is active
            FreeCAD.setActiveDocument(FreeCAD.ActiveDocument.Name)
            
            # Add direct access to active document
            exec_globals['doc'] = FreeCAD.ActiveDocument
            
            # Define a function to update the GUI that will be called after execution
            def update_gui():
                try:
                    import FreeCADGui
                    
                    # Get the active document
                    if FreeCAD.ActiveDocument is None and len(FreeCAD.listDocuments()) > 0:
                        doc_name = list(FreeCAD.listDocuments().keys())[-1]
                        FreeCAD.setActiveDocument(doc_name)
                    
                    # Ensure document is recomputed
                    if FreeCAD.ActiveDocument:
                        FreeCAD.ActiveDocument.recompute()
                    
                    # Update the GUI if available
                    if hasattr(FreeCADGui, 'ActiveDocument') and FreeCADGui.ActiveDocument:
                        # Select all objects to make them visible
                        FreeCADGui.Selection.clearSelection()
                        for obj in FreeCAD.ActiveDocument.Objects:
                            try:
                                FreeCADGui.Selection.addSelection(obj)
                            except:
                                pass
                        
                        # Force view updates using multiple methods
                        FreeCADGui.ActiveDocument.ActiveView.fitAll()
                        FreeCADGui.updateGui()
                        FreeCADGui.SendMsgToActiveView("ViewFit")
                        
                        # Try additional view commands
                        try:
                            FreeCADGui.runCommand("Std_ViewFitAll")
                            FreeCADGui.runCommand("Std_ViewSelection")
                        except:
                            pass
                        
                        # Final update after a short delay
                        import time
                        time.sleep(0.2)
                        FreeCADGui.updateGui()
                        
                        print("GUI update completed successfully")
                except Exception as e:
                    print(f"GUI update error: {str(e)}")
            
            # Add the update function to the globals
            exec_globals['update_gui'] = update_gui
            
            # Append GUI update call to the code
            gui_update_code = """
# Update the GUI to ensure model is visible
try:
    update_gui()
except Exception as e:
    print(f"GUI update failed: {str(e)}")
"""
            
            # Execute the code with the GUI update appended
            exec(freecad_code + gui_update_code, exec_globals)
            
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
    
    def _clean_code(self, code: str) -> str:
        """Clean FreeCAD Python code to remove any problematic characters or content
        
        Args:
            code: The FreeCAD Python code to clean
            
        Returns:
            Cleaned code string
        """
        if not code:
            return ""
            
        # Remove any non-printable characters
        code = ''.join(c for c in code if c.isprintable() or c in '\n\r\t')
        
        # Remove any markdown code block markers
        code = code.replace('```python', '').replace('```', '')
        
        # Remove any trailing or leading whitespace
        code = code.strip()
        
        return code
    
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
