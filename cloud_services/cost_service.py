"""
Manufacturing Cost Estimation Cloud Service Integration
Provides cost analysis capabilities through cloud services
"""

import os
import sys
import json
import time
import traceback
from typing import Dict, Any, Optional, List, Tuple

# Try to import FreeCAD modules
try:
    import FreeCAD
    import Part
except ImportError:
    print("Warning: FreeCAD modules not available in this context")

# Import cloud service handler
try:
    from cloud_services.service_handler import CloudServiceHandler
except ImportError:
    # Adjust path for direct execution
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from cloud_services.service_handler import CloudServiceHandler

class CostService:
    """Manufacturing cost estimation service"""
    
    def __init__(self, config_path=None):
        """Initialize the cost estimation service"""
        self.service_handler = CloudServiceHandler(config_path)
        self.last_estimate = None
        
    def estimate_cost(self, cad_data=None, manufacturing_process="3d_printing", 
                     material="pla", quantity=1, region="global"):
        """
        Estimate manufacturing cost for the current model
        
        Args:
            cad_data: Pre-extracted CAD data or None to extract from active document
            manufacturing_process: Target manufacturing process
            material: Material to use for manufacturing
            quantity: Production quantity
            region: Geographic region for pricing
            
        Returns:
            Dict containing cost estimation results
        """
        try:
            # Get CAD data if not provided
            if cad_data is None:
                from utils.cad_extractor import extract_cad_data_for_features
                cad_data = extract_cad_data_for_features()
            
            # Prepare payload
            payload = {
                "cad_data": cad_data,
                "manufacturing_process": manufacturing_process,
                "material": material,
                "quantity": quantity,
                "region": region,
                "analysis_type": "cost",
                "detail_level": "comprehensive"
            }
            
            # Call the cost estimation service
            result = self.service_handler.call_service("cost", payload)
            
            # Store the cost results
            if result.get("success", False):
                self.last_estimate = result.get("data", {})
                
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
    
    def get_total_cost(self) -> float:
        """
        Get the total estimated cost from the last analysis
        
        Returns:
            Float representing the total cost
        """
        if not self.last_estimate:
            return 0.0
            
        return self.last_estimate.get("total_cost", 0.0)
    
    def get_cost_breakdown(self) -> Dict[str, float]:
        """
        Get detailed cost breakdown from the last estimate
        
        Returns:
            Dict with cost categories and values
        """
        if not self.last_estimate:
            return {}
            
        return self.last_estimate.get("cost_breakdown", {})
    
    def get_cost_factors(self) -> List[Dict[str, Any]]:
        """
        Get factors affecting the cost from the last estimate
        
        Returns:
            List of cost factors with description and impact
        """
        if not self.last_estimate:
            return []
            
        return self.last_estimate.get("cost_factors", [])
    
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """
        Get suggestions for cost optimization
        
        Returns:
            List of suggestions with description and potential savings
        """
        if not self.last_estimate:
            return []
            
        return self.last_estimate.get("optimization_suggestions", [])
    
    def compare_manufacturing_methods(self, cad_data=None, materials=None, 
                                     processes=None, quantities=None):
        """
        Compare costs across different manufacturing methods
        
        Args:
            cad_data: Pre-extracted CAD data or None to extract from active document
            materials: List of materials to compare
            processes: List of manufacturing processes to compare
            quantities: List of quantities to compare
            
        Returns:
            Dict containing comparative cost analysis
        """
        try:
            # Set defaults
            if materials is None:
                materials = ["pla", "abs", "nylon"]
            if processes is None:
                processes = ["3d_printing", "cnc_machining", "injection_molding"]
            if quantities is None:
                quantities = [1, 10, 100, 1000]
                
            # Get CAD data if not provided
            if cad_data is None:
                from utils.cad_extractor import extract_cad_data_for_features
                cad_data = extract_cad_data_for_features()
            
            # Prepare payload
            payload = {
                "cad_data": cad_data,
                "materials": materials,
                "processes": processes,
                "quantities": quantities,
                "analysis_type": "comparative_cost",
                "detail_level": "comprehensive"
            }
            
            # Call the cost comparison service
            result = self.service_handler.call_service("cost", payload)
            
            return result
            
        except Exception as e:
            print(f"Error in cost comparison: {str(e)}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "service": "cost_comparison",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
    
    def display_cost_report(self):
        """
        Generate a formatted cost report from the last estimate
        
        Returns:
            String containing formatted cost report
        """
        if not self.last_estimate:
            return "No cost estimate available. Run estimate_cost() first."
            
        # Extract data from last estimate
        total = self.get_total_cost()
        breakdown = self.get_cost_breakdown()
        factors = self.get_cost_factors()
        suggestions = self.get_optimization_suggestions()
        
        # Format the report
        report = []
        report.append("=== MANUFACTURING COST ESTIMATE ===")
        report.append(f"Total Cost: ${total:.2f}")
        report.append("")
        
        # Add breakdown
        report.append("--- Cost Breakdown ---")
        for category, amount in breakdown.items():
            report.append(f"{category.replace('_', ' ').title()}: ${amount:.2f}")
        report.append("")
        
        # Add factors
        report.append("--- Cost Factors ---")
        for factor in factors:
            report.append(f"• {factor.get('description', 'Unknown factor')}")
            if 'impact' in factor:
                report.append(f"  Impact: {factor['impact']}")
        report.append("")
        
        # Add suggestions
        report.append("--- Cost Optimization Suggestions ---")
        for suggestion in suggestions:
            report.append(f"• {suggestion.get('description', 'Unknown suggestion')}")
            if 'potential_savings' in suggestion:
                report.append(f"  Potential Savings: ${suggestion['potential_savings']:.2f}")
        
        return "\n".join(report)
