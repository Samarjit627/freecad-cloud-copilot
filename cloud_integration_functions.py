"""
Cloud Integration Functions for StandaloneCoPilot
Provides functions to call cloud services for DFM, cost estimation, and tool recommendations
"""

import os
import sys
import json
import time
import traceback
from typing import Dict, Any, Optional, List, Union

# Try to import FreeCAD modules
try:
    import FreeCAD
    import Part
    import FreeCADGui
except ImportError:
    print("Warning: FreeCAD modules not available in this context")

# Try to import cloud services
try:
    from cloud_services.cloud_integration import CloudIntegration
    from utils.cad_extractor import extract_cad_data_for_features
    _CLOUD_SERVICES_AVAILABLE = True
except ImportError:
    print("Warning: Cloud services not available. Some features will be disabled.")
    _CLOUD_SERVICES_AVAILABLE = False

# Global cloud integration instance
_CLOUD_INTEGRATION = None

def get_cloud_integration():
    """Get or create the cloud integration instance"""
    global _CLOUD_INTEGRATION
    
    if _CLOUD_INTEGRATION is None and _CLOUD_SERVICES_AVAILABLE:
        try:
            # Look for config file in the same directory as this file
            this_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(this_dir, "cloud_config.json")
            
            # Create cloud integration instance
            _CLOUD_INTEGRATION = CloudIntegration(config_path)
            print("Cloud integration initialized successfully")
        except Exception as e:
            print(f"Error initializing cloud integration: {str(e)}")
            traceback.print_exc()
            return None
    
    return _CLOUD_INTEGRATION

def analyze_dfm(manufacturing_process="3d_printing"):
    """
    Analyze design for manufacturability using cloud service
    
    Args:
        manufacturing_process: Target manufacturing process
        
    Returns:
        Dict containing DFM analysis results
    """
    try:
        # Get cloud integration
        cloud_integration = get_cloud_integration()
        if not cloud_integration:
            return {
                "success": False,
                "error": "Cloud integration not available",
                "service": "dfm",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
        
        # Call DFM service
        result = cloud_integration.analyze_dfm(manufacturing_process)
        
        # Display results in console
        if result.get("success", False):
            FreeCAD.Console.PrintMessage("DFM Analysis completed successfully\n")
            
            # Get DFM report
            report = cloud_integration.get_dfm_report()
            FreeCAD.Console.PrintMessage(f"{report}\n")
            
            # Visualize issues
            cloud_integration.visualize_dfm_issues()
        else:
            FreeCAD.Console.PrintError(f"DFM Analysis failed: {result.get('error', 'Unknown error')}\n")
        
        return result
        
    except Exception as e:
        print(f"Error in DFM analysis: {str(e)}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "service": "dfm",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

def estimate_cost(manufacturing_process="3d_printing", material="pla", quantity=1, region="global"):
    """
    Estimate manufacturing cost using cloud service
    
    Args:
        manufacturing_process: Target manufacturing process
        material: Material to use for manufacturing
        quantity: Production quantity
        region: Geographic region for pricing
        
    Returns:
        Dict containing cost estimation results
    """
    try:
        # Get cloud integration
        cloud_integration = get_cloud_integration()
        if not cloud_integration:
            return {
                "success": False,
                "error": "Cloud integration not available",
                "service": "cost",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
        
        # Call cost service
        result = cloud_integration.estimate_cost(
            manufacturing_process=manufacturing_process,
            material=material,
            quantity=quantity,
            region=region
        )
        
        # Display results in console
        if result.get("success", False):
            FreeCAD.Console.PrintMessage("Cost Estimation completed successfully\n")
            
            # Get cost report
            report = cloud_integration.get_cost_report()
            FreeCAD.Console.PrintMessage(f"{report}\n")
        else:
            FreeCAD.Console.PrintError(f"Cost Estimation failed: {result.get('error', 'Unknown error')}\n")
        
        return result
        
    except Exception as e:
        print(f"Error in cost estimation: {str(e)}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "service": "cost",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

def recommend_tools(manufacturing_process="cnc_machining", material="aluminum", machine_type=None):
    """
    Get tool recommendations using cloud service
    
    Args:
        manufacturing_process: Target manufacturing process
        material: Material to be machined
        machine_type: Specific machine type if applicable
        
    Returns:
        Dict containing tool recommendations
    """
    try:
        # Get cloud integration
        cloud_integration = get_cloud_integration()
        if not cloud_integration:
            return {
                "success": False,
                "error": "Cloud integration not available",
                "service": "tool_recommendation",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
        
        # Call tool service
        result = cloud_integration.recommend_tools(
            manufacturing_process=manufacturing_process,
            material=material,
            machine_type=machine_type
        )
        
        # Display results in console
        if result.get("success", False):
            FreeCAD.Console.PrintMessage("Tool Recommendation completed successfully\n")
            
            # Get recommended tools
            tools = cloud_integration.tool_service.get_recommended_tools()
            
            # Display tools
            FreeCAD.Console.PrintMessage("=== RECOMMENDED TOOLS ===\n")
            for i, tool in enumerate(tools):
                FreeCAD.Console.PrintMessage(f"{i+1}. {tool.get('name', 'Unknown')}\n")
                FreeCAD.Console.PrintMessage(f"   Type: {tool.get('type', 'Unknown')}\n")
                FreeCAD.Console.PrintMessage(f"   Diameter: {tool.get('diameter', 0)}mm\n")
                if "description" in tool:
                    FreeCAD.Console.PrintMessage(f"   Description: {tool['description']}\n")
                FreeCAD.Console.PrintMessage("\n")
            
            # Visualize tool paths
            cloud_integration.visualize_tool_paths()
        else:
            FreeCAD.Console.PrintError(f"Tool Recommendation failed: {result.get('error', 'Unknown error')}\n")
        
        return result
        
    except Exception as e:
        print(f"Error in tool recommendation: {str(e)}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "service": "tool_recommendation",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

def compare_manufacturing_methods(materials=None, processes=None, quantities=None):
    """
    Compare costs across different manufacturing methods using cloud service
    
    Args:
        materials: List of materials to compare
        processes: List of manufacturing processes to compare
        quantities: List of quantities to compare
        
    Returns:
        Dict containing comparative cost analysis
    """
    try:
        # Get cloud integration
        cloud_integration = get_cloud_integration()
        if not cloud_integration:
            return {
                "success": False,
                "error": "Cloud integration not available",
                "service": "manufacturing_comparison",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
        
        # Call manufacturing comparison service
        result = cloud_integration.compare_manufacturing_methods(
            materials=materials,
            processes=processes,
            quantities=quantities
        )
        
        # Display results in console
        if result.get("success", False):
            FreeCAD.Console.PrintMessage("Manufacturing Comparison completed successfully\n")
            
            # Get comparison data
            comparison = result.get("data", {}).get("comparison", {})
            
            # Display comparison
            FreeCAD.Console.PrintMessage("=== MANUFACTURING METHOD COMPARISON ===\n")
            
            # Format as a table
            processes_list = comparison.get("processes", [])
            materials_list = comparison.get("materials", [])
            quantities_list = comparison.get("quantities", [])
            
            if "cost_matrix" in comparison:
                cost_matrix = comparison["cost_matrix"]
                
                # Print header
                header = "Process | Material | " + " | ".join([f"Qty {q}" for q in quantities_list])
                FreeCAD.Console.PrintMessage(f"{header}\n")
                FreeCAD.Console.PrintMessage("-" * len(header) + "\n")
                
                # Print rows
                for p_idx, process in enumerate(processes_list):
                    for m_idx, material in enumerate(materials_list):
                        row = f"{process} | {material} | "
                        for q_idx, quantity in enumerate(quantities_list):
                            cost = cost_matrix[p_idx][m_idx][q_idx]
                            row += f"${cost:.2f} | "
                        FreeCAD.Console.PrintMessage(f"{row.strip(' |')}\n")
        else:
            FreeCAD.Console.PrintError(f"Manufacturing Comparison failed: {result.get('error', 'Unknown error')}\n")
        
        return result
        
    except Exception as e:
        print(f"Error in manufacturing comparison: {str(e)}")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "service": "manufacturing_comparison",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

# Function to call any cloud feature
def call_feature(name, payload=None, base_url=None):
    """
    Call a deployed microservice feature endpoint
    
    Args:
        name (str): Feature name (e.g., 'dfm_overlay', 'cost_estimate')
        payload (dict): Data to send to the feature
        base_url (str): Base URL for the service (defaults to config value)
    
    Returns:
        dict: Response from the microservice
    """
    try:
        # Get cloud integration
        cloud_integration = get_cloud_integration()
        
        # If cloud integration is available, use it
        if cloud_integration:
            # Map feature name to appropriate function
            if name == "dfm_analysis" or name == "dfm_overlay":
                return analyze_dfm(payload.get("manufacturing_process", "3d_printing"))
                
            elif name == "cost_estimate":
                return estimate_cost(
                    manufacturing_process=payload.get("manufacturing_process", "3d_printing"),
                    material=payload.get("material", "pla"),
                    quantity=payload.get("quantity", 1),
                    region=payload.get("region", "global")
                )
                
            elif name == "tool_recommendation":
                return recommend_tools(
                    manufacturing_process=payload.get("manufacturing_process", "cnc_machining"),
                    material=payload.get("material", "aluminum"),
                    machine_type=payload.get("machine_type")
                )
                
            elif name == "manufacturing_comparison":
                return compare_manufacturing_methods(
                    materials=payload.get("materials"),
                    processes=payload.get("processes"),
                    quantities=payload.get("quantities")
                )
        
        # If cloud integration is not available or feature not recognized, fall back to direct API call
        # Default base URL for local development
        if base_url is None:
            # Try to get from config
            try:
                this_dir = os.path.dirname(os.path.abspath(__file__))
                config_path = os.path.join(this_dir, "cloud_config.json")
                
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    base_url = config.get("cloud_api_url", "https://freecad-copilot-service.run.app")
            except:
                base_url = "http://localhost:8000"
        
        # Construct the full URL
        url = f"{base_url}/{name}"
        
        # Prepare payload
        if payload is None:
            payload = {}
            
        # Add timestamp and basic metadata
        payload.update({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "source": "freecad_macro",
            "macro_version": "1.1.0"
        })
        
        # Convert payload to JSON
        data = json.dumps(payload).encode('utf-8')
        
        # Get API key from config
        api_key = None
        try:
            this_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(this_dir, "cloud_config.json")
            
            with open(config_path, 'r') as f:
                config = json.load(f)
                api_key = config.get("cloud_api_key", "")
        except Exception as e:
            print(f"Warning: Could not load API key from config: {e}")
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'FreeCAD-StandaloneCoPilot/1.1.0'
        }
        
        # Add API key if available - use X-API-Key as the primary authentication method
        if api_key:
            headers['X-API-Key'] = api_key
            print(f"Using X-API-Key authentication for feature call to {name}")
        
        # Create request
        req = urllib.request.Request(
            url, 
            data=data, 
            headers=headers
        )
        
        # Make the request with timeout
        print(f"Calling feature endpoint: {url}")
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = response.read().decode('utf-8')
            result = json.loads(response_data)
            
        print(f"✅ Feature call successful: {name}")
        return {
            "success": True,
            "data": result,
            "feature": name,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
    except urllib.error.HTTPError as e:
        error_msg = f"HTTP Error {e.code}: {e.reason}"
        print(f"❌ HTTP error calling feature '{name}': {error_msg}")
        FreeCAD.Console.PrintError(f"❌ Feature call failed: {error_msg}\n")
        return {
            "success": False,
            "error": error_msg,
            "feature": name,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
    except urllib.error.URLError as e:
        error_msg = f"Connection error: {str(e.reason)}"
        print(f"❌ Connection error calling feature '{name}': {error_msg}")
        FreeCAD.Console.PrintError(f"❌ Feature call failed: {error_msg}\n")
        return {
            "success": False,
            "error": error_msg,
            "feature": name,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON response: {str(e)}"
        print(f"❌ JSON error from feature '{name}': {error_msg}")
        FreeCAD.Console.PrintError(f"❌ Feature call failed: {error_msg}\n")
        return {
            "success": False,
            "error": error_msg,
            "feature": name,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ Unexpected error calling feature '{name}': {error_msg}")
        FreeCAD.Console.PrintError(f"❌ Feature call failed: {error_msg}\n")
        traceback.print_exc()
        return {
            "success": False,
            "error": error_msg,
            "feature": name,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
