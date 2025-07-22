"""
Cloud Integration Module for FreeCAD CoPilot
Provides a unified interface for all cloud-based manufacturing intelligence services
"""

import os
import sys
import json
import time
import traceback
from typing import Dict, Any, Optional, List, Tuple, Union

# Import cloud services
try:
    from cloud_services.dfm_service import DFMService
    from cloud_services.cost_service import CostService
    from cloud_services.tool_service import ToolService
except ImportError:
    # Adjust path for direct execution
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from cloud_services.dfm_service import DFMService
    from cloud_services.cost_service import CostService
    from cloud_services.tool_service import ToolService

# Import utilities
try:
    from utils.cad_extractor import extract_cad_data_for_features
except ImportError:
    # Adjust path for direct execution
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.cad_extractor import extract_cad_data_for_features

class CloudIntegration:
    """
    Unified interface for all cloud-based manufacturing intelligence services
    
    This class provides a single entry point for all cloud services,
    making it easy to integrate with the StandaloneCoPilot macro.
    """
    
    def __init__(self, config_path=None):
        """Initialize the cloud integration module"""
        self.config_path = config_path
        self.dfm_service = DFMService(config_path)
        self.cost_service = CostService(config_path)
        self.tool_service = ToolService(config_path)
        self.last_cad_data = None
        
    def analyze_dfm(self, manufacturing_process="3d_printing"):
        """
        Analyze design for manufacturability
        
        Args:
            manufacturing_process: Target manufacturing process
            
        Returns:
            Dict containing DFM analysis results
        """
        try:
            # Extract CAD data if needed
            if not self.last_cad_data:
                self.last_cad_data = extract_cad_data_for_features()
            
            # Call DFM service
            result = self.dfm_service.analyze_model(
                cad_data=self.last_cad_data,
                manufacturing_process=manufacturing_process
            )
            
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
    
    def estimate_cost(self, manufacturing_process="3d_printing", 
                     material="pla", quantity=1, region="global"):
        """
        Estimate manufacturing cost
        
        Args:
            manufacturing_process: Target manufacturing process
            material: Material to use for manufacturing
            quantity: Production quantity
            region: Geographic region for pricing
            
        Returns:
            Dict containing cost estimation results
        """
        try:
            # Extract CAD data if needed
            if not self.last_cad_data:
                self.last_cad_data = extract_cad_data_for_features()
            
            # Call cost service
            result = self.cost_service.estimate_cost(
                cad_data=self.last_cad_data,
                manufacturing_process=manufacturing_process,
                material=material,
                quantity=quantity,
                region=region
            )
            
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
    
    def recommend_tools(self, manufacturing_process="cnc_machining", 
                       material="aluminum", machine_type=None):
        """
        Get tool recommendations
        
        Args:
            manufacturing_process: Target manufacturing process
            material: Material to be machined
            machine_type: Specific machine type if applicable
            
        Returns:
            Dict containing tool recommendations
        """
        try:
            # Extract CAD data if needed
            if not self.last_cad_data:
                self.last_cad_data = extract_cad_data_for_features()
            
            # Call tool service
            result = self.tool_service.recommend_tools(
                cad_data=self.last_cad_data,
                manufacturing_process=manufacturing_process,
                material=material,
                machine_type=machine_type
            )
            
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
    
    def compare_manufacturing_methods(self, materials=None, processes=None, quantities=None):
        """
        Compare costs across different manufacturing methods
        
        Args:
            materials: List of materials to compare
            processes: List of manufacturing processes to compare
            quantities: List of quantities to compare
            
        Returns:
            Dict containing comparative cost analysis
        """
        try:
            # Extract CAD data if needed
            if not self.last_cad_data:
                self.last_cad_data = extract_cad_data_for_features()
            
            # Call cost comparison service
            result = self.cost_service.compare_manufacturing_methods(
                cad_data=self.last_cad_data,
                materials=materials,
                processes=processes,
                quantities=quantities
            )
            
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
    
    def visualize_dfm_issues(self, doc=None):
        """
        Visualize DFM issues in the 3D view
        
        Args:
            doc: FreeCAD document (uses active document if None)
            
        Returns:
            Boolean indicating success
        """
        return self.dfm_service.visualize_issues(doc)
    
    def visualize_tool_paths(self, doc=None):
        """
        Visualize tool paths in the 3D view
        
        Args:
            doc: FreeCAD document (uses active document if None)
            
        Returns:
            Boolean indicating success
        """
        return self.tool_service.visualize_tool_paths(doc)
    
    def get_dfm_report(self):
        """
        Get a formatted DFM report
        
        Returns:
            String containing formatted DFM report
        """
        issues = self.dfm_service.get_dfm_issues()
        score = self.dfm_service.get_manufacturability_score()
        recommendations = self.dfm_service.get_improvement_recommendations()
        
        # Format the report
        report = []
        report.append("=== DESIGN FOR MANUFACTURING ANALYSIS ===")
        report.append(f"Manufacturability Score: {score:.1f}/100")
        report.append("")
        
        # Add issues
        report.append(f"--- Issues ({len(issues)}) ---")
        for i, issue in enumerate(issues):
            severity = issue.get("severity", "medium")
            description = issue.get("description", "Unknown issue")
            
            # Format based on severity
            if severity == "high":
                report.append(f"❌ {description}")
            elif severity == "medium":
                report.append(f"⚠️ {description}")
            else:
                report.append(f"ℹ️ {description}")
                
            # Add recommendation if available
            if "recommendation" in issue:
                report.append(f"   → {issue['recommendation']}")
        report.append("")
        
        # Add recommendations
        report.append("--- Improvement Recommendations ---")
        for rec in recommendations:
            report.append(f"• {rec.get('description', 'Unknown recommendation')}")
            if "impact" in rec:
                report.append(f"  Impact: {rec['impact']}")
        
        return "\n".join(report)
    
    def get_cost_report(self):
        """
        Get a formatted cost report
        
        Returns:
            String containing formatted cost report
        """
        return self.cost_service.display_cost_report()
    
    def refresh_cad_data(self):
        """
        Force refresh of CAD data
        
        Returns:
            Dict containing the refreshed CAD data
        """
        self.last_cad_data = extract_cad_data_for_features()
        return self.last_cad_data
