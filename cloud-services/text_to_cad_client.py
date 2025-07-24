"""
Text-to-CAD Cloud Client
Handles communication with the Text-to-CAD cloud service
"""

import os
import json
import time
import requests
import traceback
from typing import Dict, Any, Optional

class TextToCADCloudClient:
    """Client for communicating with the Text-to-CAD cloud service"""
    
    def __init__(self, config_path: Optional[str] = None, endpoint: Optional[str] = None):
        """Initialize the Text-to-CAD cloud client
        
        Args:
            config_path: Path to the configuration file
            endpoint: Override the endpoint URL from the config
        """
        self.config = {}
        self.endpoint = endpoint
        self.api_key = None
        self.connected = False
        self.last_error = None
        
        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                    
                # Get endpoint from config if not provided
                if not self.endpoint and 'text_to_cad_endpoint' in self.config:
                    self.endpoint = self.config['text_to_cad_endpoint']
                    
                # Get API key from config
                if 'text_to_cad_api_key' in self.config:
                    self.api_key = self.config['text_to_cad_api_key']
                    
                print(f"Text-to-CAD client initialized with endpoint: {self.endpoint}")
            except Exception as e:
                print(f"Error loading Text-to-CAD configuration: {str(e)}")
                traceback.print_exc()
        
        # Default endpoint if not provided
        if not self.endpoint:
            self.endpoint = "https://text-to-cad-agent-xxx-uc.a.run.app"
            print(f"Using default Text-to-CAD endpoint: {self.endpoint}")
            
        # Test connection
        self.test_connection()
    
    def test_connection(self) -> bool:
        """Test connection to the Text-to-CAD cloud service"""
        try:
            url = f"{self.endpoint}/health"
            headers = {}
            if self.api_key:
                headers['Authorization'] = f"Bearer {self.api_key}"
                
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.connected = True
                print("Successfully connected to Text-to-CAD service")
                return True
            else:
                self.connected = False
                self.last_error = f"Connection failed with status code: {response.status_code}"
                print(self.last_error)
                return False
        except Exception as e:
            self.connected = False
            self.last_error = str(e)
            print(f"Error connecting to Text-to-CAD service: {str(e)}")
            return False
    
    def generate_cad_from_text(self, description: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """Generate CAD model from text description
        
        Args:
            description: Natural language description of the part to create
            user_id: User identifier for tracking
            
        Returns:
            Dictionary with engineering analysis and FreeCAD code
        """
        if not self.connected:
            self.test_connection()
            if not self.connected:
                return {
                    "success": False,
                    "error": f"Not connected to Text-to-CAD service: {self.last_error}",
                    "fallback_mode": True
                }
        
        try:
            url = f"{self.endpoint}/text-to-cad"
            headers = {
                'Content-Type': 'application/json'
            }
            
            if self.api_key:
                headers['Authorization'] = f"Bearer {self.api_key}"
                
            payload = {
                "description": description,
                "user_id": user_id
            }
            
            print(f"Sending Text-to-CAD request: {description[:50]}...")
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                print("Successfully received Text-to-CAD response")
                return {
                    "success": True,
                    "result": result
                }
            else:
                error_msg = f"Text-to-CAD request failed with status code: {response.status_code}"
                print(error_msg)
                try:
                    error_details = response.json()
                    print(f"Error details: {json.dumps(error_details, indent=2)}")
                except:
                    pass
                
                return {
                    "success": False,
                    "error": error_msg,
                    "fallback_mode": True
                }
        except Exception as e:
            error_msg = f"Error in Text-to-CAD request: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            return {
                "success": False,
                "error": error_msg,
                "fallback_mode": True
            }
