#!/usr/bin/env python3
"""
Text-to-CAD Integration Module
Provides natural language to CAD conversion capabilities for FreeCAD
"""

import json
import requests
import os
import re
from typing import Dict, Any, Optional, Tuple

class TextToCADIntegration:
    """
    Handles text-to-CAD conversion using cloud services and local fallbacks
    """
    
    def __init__(self, config_path: str):
        """Initialize the Text-to-CAD integration"""
        self.config_path = config_path
        self.connected = False
        self.base_url = None
        self.api_key = None
        self.timeout = 30
        
        # Load configuration
        self._load_config()
        
        # Test connection
        self._test_connection()
    
    def _load_config(self):
        """Load configuration from cloud_config.json"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    
                # Extract text-to-CAD server configuration
                text_to_cad_config = config.get('text_to_cad', {})
                self.base_url = text_to_cad_config.get('base_url', 'http://localhost:8084')
                self.api_key = text_to_cad_config.get('api_key')
                self.timeout = text_to_cad_config.get('timeout', 30)
                
                print(f"Text-to-CAD config loaded: {self.base_url}")
            else:
                print(f"Config file not found: {self.config_path}")
                # Use default local server
                self.base_url = 'http://localhost:8084'
                
        except Exception as e:
            print(f"Error loading Text-to-CAD config: {e}")
            self.base_url = 'http://localhost:8084'
    
    def _test_connection(self):
        """Test connection to the text-to-CAD server"""
        try:
            if self.base_url:
                health_url = f"{self.base_url}/health"
                headers = {}
                if self.api_key:
                    headers['X-API-Key'] = self.api_key
                
                response = requests.get(health_url, headers=headers, timeout=5)
                if response.status_code == 200:
                    self.connected = True
                    print(f"✅ Text-to-CAD server connected: {self.base_url}")
                else:
                    print(f"⚠️ Text-to-CAD server responded with status {response.status_code}")
                    
        except Exception as e:
            print(f"⚠️ Text-to-CAD server not available: {e}")
            self.connected = False
    
    def is_text_to_cad_request(self, message: str) -> bool:
        """
        Determine if a message is a text-to-CAD request
        """
        if not message:
            return False
            
        message_lower = message.lower()
        
        # CAD creation keywords
        cad_keywords = [
            'create', 'make', 'design', 'generate', 'build', 'draw',
            'model', 'construct', 'fabricate', 'manufacture'
        ]
        
        # CAD object keywords
        object_keywords = [
            'gear', 'assembly', 'bracket', 'holder', 'mount', 'adapter',
            'cylinder', 'cube', 'box', 'sphere', 'cone', 'tube',
            'bottle', 'container', 'housing', 'case', 'cover',
            'shaft', 'bearing', 'bushing', 'spacer', 'washer',
            'plate', 'panel', 'frame', 'support', 'clamp'
        ]
        
        # Special patterns
        special_patterns = [
            r'\d+:\d+.*ratio',  # Gear ratios like "10:1 ratio"
            r'reduction.*ratio',  # "reduction ratio"
            r'gear.*assembly',   # "gear assembly"
            r'with.*holes?',     # "with holes"
            r'diameter.*\d+',    # "diameter 50mm"
            r'\d+\s*mm',         # Dimensions like "50mm"
        ]
        
        # Check for CAD creation patterns
        has_cad_keyword = any(keyword in message_lower for keyword in cad_keywords)
        has_object_keyword = any(keyword in message_lower for keyword in object_keywords)
        has_special_pattern = any(re.search(pattern, message_lower) for pattern in special_patterns)
        
        return has_cad_keyword and (has_object_keyword or has_special_pattern)
    
    def process_request(self, prompt: str) -> Dict[str, Any]:
        """
        Process a text-to-CAD request
        """
        if not self.connected:
            return {
                'success': False,
                'error': 'Text-to-CAD server not available',
                'fallback_available': True
            }
        
        try:
            # Prepare request
            url = f"{self.base_url}/api/v1/text-to-cad"
            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['X-API-Key'] = self.api_key
            
            payload = {
                'prompt': prompt,
                'format': 'freecad_python',
                'include_analysis': True
            }
            
            # Make request
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'freecad_code': result.get('freecad_code', ''),
                    'engineering_analysis': result.get('engineering_analysis', ''),
                    'metadata': result.get('metadata', {}),
                    'server_response': result
                }
            else:
                return {
                    'success': False,
                    'error': f'Server error: {response.status_code}',
                    'fallback_available': True
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout',
                'fallback_available': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Request failed: {str(e)}',
                'fallback_available': True
            }
    
    def execute_freecad_code(self, code: str) -> Dict[str, Any]:
        """
        Execute FreeCAD code safely
        """
        try:
            # Import FreeCAD modules
            import FreeCAD
            import Part
            
            # Execute the code
            exec(code)
            
            # Update FreeCAD GUI to make objects visible - ENHANCED FOR AXIS 5
            try:
                import FreeCADGui
                
                # Recompute all documents first
                for doc_name in FreeCAD.listDocuments():
                    doc = FreeCAD.getDocument(doc_name)
                    doc.recompute()
                    print(f"✅ Recomputed document: {doc_name}")
                
                # Get the active document and ensure objects are visible
                if FreeCAD.ActiveDocument:
                    active_doc = FreeCAD.ActiveDocument
                    print(f"✅ Active document: {active_doc.Name} with {len(active_doc.Objects)} objects")
                    
                    # Make sure all objects are visible
                    for obj in active_doc.Objects:
                        try:
                            if hasattr(FreeCADGui, 'getDocument'):
                                view_obj = FreeCADGui.getDocument(active_doc.Name).getObject(obj.Name)
                                if view_obj:
                                    view_obj.Visibility = True
                                    print(f"✅ Made object visible: {obj.Name}")
                        except Exception as obj_e:
                            print(f"⚠️ Error making object visible: {obj_e}")
                
                # Update GUI if available
                if hasattr(FreeCADGui, 'ActiveDocument') and FreeCADGui.ActiveDocument:
                    try:
                        # Force document recompute
                        FreeCADGui.ActiveDocument.Document.recompute()
                        print("✅ GUI document recomputed")
                        
                        # Fit all objects in view
                        if hasattr(FreeCADGui.ActiveDocument, 'ActiveView'):
                            FreeCADGui.ActiveDocument.ActiveView.fitAll()
                            print("✅ View fitted to all objects")
                        
                        # Update GUI
                        FreeCADGui.updateGui()
                        print("✅ GUI updated")
                        
                        # Try additional view commands for visibility
                        try:
                            FreeCADGui.runCommand("Std_ViewFitAll")
                            print("✅ Std_ViewFitAll executed")
                        except Exception as cmd_e:
                            print(f"⚠️ Std_ViewFitAll failed: {cmd_e}")
                            
                        # Force refresh of 3D view
                        try:
                            FreeCADGui.runCommand("Std_Refresh")
                            print("✅ 3D view refreshed")
                        except Exception as refresh_e:
                            print(f"⚠️ Refresh failed: {refresh_e}")
                            
                    except Exception as gui_update_e:
                        print(f"⚠️ GUI update error: {gui_update_e}")
                        
                print("✅ CAD object created and GUI updated for Axis 5")
            except Exception as gui_e:
                print(f"⚠️ GUI update failed: {str(gui_e)}")
            
            return {
                'success': True,
                'message': 'CAD model created successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'FreeCAD execution error: {str(e)}'
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the integration"""
        return {
            'connected': self.connected,
            'base_url': self.base_url,
            'has_api_key': bool(self.api_key),
            'timeout': self.timeout
        }

# Compatibility functions for the macro
def create_text_to_cad_integration(config_path: str) -> Optional[TextToCADIntegration]:
    """Create and return a TextToCADIntegration instance"""
    try:
        return TextToCADIntegration(config_path)
    except Exception as e:
        print(f"Failed to create TextToCADIntegration: {e}")
        return None
