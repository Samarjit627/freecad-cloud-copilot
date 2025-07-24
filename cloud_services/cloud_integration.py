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
        
    def analyze_dfm(self, manufacturing_process="3d_printing", material="pla", production_volume=1, advanced_analysis=True):
        """
        Analyze design for manufacturability using the industry-grade DFM engine
        
        Args:
            manufacturing_process: Target manufacturing process (e.g., '3d_printing', 'cnc_machining', 'injection_molding')
            material: Material to use for manufacturing (e.g., 'pla', 'abs', 'aluminum')
            production_volume: Production quantity (affects cost and process recommendations)
            advanced_analysis: Whether to use the advanced industry-grade DFM engine
            
        Returns:
            Dict containing comprehensive DFM analysis results
        """
        try:
            # Extract CAD data if needed
            if not self.last_cad_data:
                self.last_cad_data = extract_cad_data_for_features()
            
            # Convert manufacturing_process to ProcessType enum value if needed
            process_mapping = {
                "3d_printing": "FDM_PRINTING",
                "cnc_machining": "CNC_MACHINING",
                "injection_molding": "INJECTION_MOLDING",
                "sheet_metal": "SHEET_METAL"
            }
            
            # Map material to MaterialType enum value if needed
            material_mapping = {
                "pla": "PLA",
                "abs": "ABS",
                "nylon": "NYLON",
                "aluminum": "ALUMINUM",
                "steel": "STEEL",
                "brass": "BRASS"
            }
            
            process = process_mapping.get(manufacturing_process, manufacturing_process.upper())
            material = material_mapping.get(material, material.upper())
            
            # Call DFM service with enhanced parameters
            result = self.dfm_service.analyze_model(
                cad_data=self.last_cad_data,
                manufacturing_process=process,
                material=material,
                production_volume=production_volume,
                advanced_analysis=advanced_analysis
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
        Get a formatted DFM report with enhanced industry-grade analysis
        
        Returns:
            String containing formatted DFM report
        """
        print("DEBUG: get_dfm_report called in CloudIntegration")
        
        issues = self.dfm_service.get_dfm_issues()
        print(f"DEBUG: Retrieved {len(issues)} DFM issues")
        
        score = self.dfm_service.get_manufacturability_score()
        print(f"DEBUG: Retrieved manufacturability score: {score}")
        
        recommendations = self.dfm_service.get_improvement_recommendations()
        print(f"DEBUG: Retrieved {len(recommendations)} recommendations")
        
        cost_analysis = self.get_cost_analysis()
        print(f"DEBUG: Cost analysis available: {cost_analysis is not None}")
        
        alternative_processes = self.get_alternative_processes()
        print(f"DEBUG: Alternative processes available: {len(alternative_processes) if alternative_processes else 0}")
        
        # Print the complete report at the end
        print("DEBUG: Generating complete DFM report...")
        print(f"DEBUG: Issues count: {len(issues)}")
        print(f"DEBUG: Score: {score}")
        print(f"DEBUG: Recommendations count: {len(recommendations)}")
        print(f"DEBUG: Cost analysis available: {cost_analysis is not None}")
        print(f"DEBUG: Alternative processes count: {len(alternative_processes) if alternative_processes else 0}")
        
        final_report = self._format_dfm_report(issues, score, recommendations, cost_analysis, alternative_processes)
        print(f"DEBUG: Complete DFM report:\n{final_report}")
        print(f"DEBUG: Report length: {len(final_report)}")
        return final_report
        
    def _format_dfm_report(self, issues, score, recommendations, cost_analysis, alternative_processes):
        """Helper method to format the DFM report"""
        # Format the report
        report = []
        report.append("=== DESIGN FOR MANUFACTURING ANALYSIS ===")
        report.append(f"Manufacturability Score: {score:.1f}/100")
        report.append("")
        
        # Add issues
        report.append(f"--- Manufacturing Issues ({len(issues)}) ---")
        for i, issue in enumerate(issues):
            severity = issue.get("severity", "medium")
            description = issue.get("description", "Unknown issue")
            location = issue.get("location", "")
            
            # Format based on severity
            if severity == "critical" or severity == "high":
                report.append(f"❌ {description}")
            elif severity == "medium":
                report.append(f"⚠️ {description}")
            else:
                report.append(f"ℹ️ {description}")
                
            # Add location if available
            if location:
                report.append(f"   Location: {location}")
                
            # Add recommendation if available
            if "recommendation" in issue:
                report.append(f"   → {issue['recommendation']}")
        report.append("")
        
        # Add cost analysis if available
        if cost_analysis:
            report.append("--- Cost Analysis ---")
            report.append(f"Total Cost: ${cost_analysis.get('total_cost', 0):.2f}")
            report.append(f"Material Cost: ${cost_analysis.get('material_cost', 0):.2f}")
            report.append(f"Labor Cost: ${cost_analysis.get('labor_cost', 0):.2f}")
            report.append(f"Tooling Cost: ${cost_analysis.get('tooling_cost', 0):.2f}")
            report.append(f"Overhead: ${cost_analysis.get('overhead', 0):.2f}")
            report.append(f"Estimated Lead Time: {cost_analysis.get('lead_time', 'N/A')}")
            report.append("")
        
        # Add alternative processes if available
        if alternative_processes:
            report.append("--- Alternative Manufacturing Processes ---")
            for process in alternative_processes:
                process_name = process.get('process_name', 'Unknown')
                suitability = process.get('suitability_score', 0)
                estimated_cost = process.get('estimated_cost', 0)
                report.append(f"• {process_name} (Suitability: {suitability}/100, Est. Cost: ${estimated_cost:.2f})")
                
                # Add advantages if available
                advantages = process.get('advantages', [])
                if advantages:
                    report.append("  Advantages:")
                    for adv in advantages[:3]:  # Show top 3 advantages
                        report.append(f"    ✓ {adv}")
                        
                # Add limitations if available
                limitations = process.get('limitations', [])
                if limitations:
                    report.append("  Limitations:")
                    for lim in limitations[:2]:  # Show top 2 limitations
                        report.append(f"    ✗ {lim}")
            report.append("")
        
        # Add recommendations
        report.append("--- Expert Recommendations ---")
        for rec in recommendations:
            impact = rec.get('impact', '')
            impact_symbol = '🔴' if impact == 'high' else '🟠' if impact == 'medium' else '🟢'
            report.append(f"{impact_symbol} {rec.get('description', 'Unknown recommendation')}")
            if "details" in rec:
                report.append(f"  Details: {rec['details']}")
        
        return "\n".join(report)
        
    def get_dfm_report_legacy(self):
        """Legacy method kept for reference"""
        # Format the report
        report = []
        report.append("=== DESIGN FOR MANUFACTURING ANALYSIS ===")
        report.append(f"Manufacturability Score: {score:.1f}/100")
        report.append("")
        
        # Add issues
        report.append(f"--- Manufacturing Issues ({len(issues)}) ---")
        for i, issue in enumerate(issues):
            severity = issue.get("severity", "medium")
            description = issue.get("description", "Unknown issue")
            location = issue.get("location", "")
            
            # Format based on severity
            if severity == "critical" or severity == "high":
                report.append(f"❌ {description}")
            elif severity == "medium":
                report.append(f"⚠️ {description}")
            else:
                report.append(f"ℹ️ {description}")
                
            # Add location if available
            if location:
                report.append(f"   Location: {location}")
                
            # Add recommendation if available
            if "recommendation" in issue:
                report.append(f"   → {issue['recommendation']}")
        report.append("")
        
        # Add cost analysis if available
        if cost_analysis:
            report.append("--- Cost Analysis ---")
            report.append(f"Total Cost: ${cost_analysis.get('total_cost', 0):.2f}")
            report.append(f"Material Cost: ${cost_analysis.get('material_cost', 0):.2f}")
            report.append(f"Labor Cost: ${cost_analysis.get('labor_cost', 0):.2f}")
            report.append(f"Tooling Cost: ${cost_analysis.get('tooling_cost', 0):.2f}")
            report.append(f"Overhead: ${cost_analysis.get('overhead', 0):.2f}")
            report.append(f"Estimated Lead Time: {cost_analysis.get('lead_time', 'N/A')}")
            report.append("")
        
        # Add alternative processes if available
        if alternative_processes:
            report.append("--- Alternative Manufacturing Processes ---")
            for process in alternative_processes:
                process_name = process.get('process_name', 'Unknown')
                suitability = process.get('suitability_score', 0)
                estimated_cost = process.get('estimated_cost', 0)
                report.append(f"• {process_name} (Suitability: {suitability}/100, Est. Cost: ${estimated_cost:.2f})")
                
                # Add advantages if available
                advantages = process.get('advantages', [])
                if advantages:
                    report.append("  Advantages:")
                    for adv in advantages[:3]:  # Show top 3 advantages
                        report.append(f"    ✓ {adv}")
                        
                # Add limitations if available
                limitations = process.get('limitations', [])
                if limitations:
                    report.append("  Limitations:")
                    for lim in limitations[:2]:  # Show top 2 limitations
                        report.append(f"    ✗ {lim}")
            report.append("")
        
        # Add recommendations
        report.append("--- Expert Recommendations ---")
        for rec in recommendations:
            impact = rec.get('impact', '')
            impact_symbol = '🔴' if impact == 'high' else '🟠' if impact == 'medium' else '🟢'
            report.append(f"{impact_symbol} {rec.get('description', 'Unknown recommendation')}")
            if "details" in rec:
                report.append(f"  Details: {rec['details']}")
        
        return "\n".join(report)
    
    def get_cost_analysis(self):
        """
        Get detailed cost analysis from the DFM service
        
        Returns:
            Dict containing detailed cost breakdown
        """
        return self.dfm_service.get_cost_analysis()
    
    def get_alternative_processes(self):
        """
        Get alternative manufacturing processes from the DFM service
        
        Returns:
            List of alternative processes with suitability scores and cost estimates
        """
        return self.dfm_service.get_alternative_processes()
    
    def get_cost_report(self):
        """
        Get a formatted cost report
        
        Returns:
            String containing formatted cost report
        """
        # Try to use the enhanced cost analysis from DFM service first
        cost_analysis = self.get_cost_analysis()
        if cost_analysis:
            report = []
            report.append("=== MANUFACTURING COST ANALYSIS ===")
            report.append(f"Total Cost: ${cost_analysis.get('total_cost', 0):.2f}")
            report.append("")
            report.append("--- Cost Breakdown ---")
            report.append(f"Material Cost: ${cost_analysis.get('material_cost', 0):.2f}")
            report.append(f"Labor Cost: ${cost_analysis.get('labor_cost', 0):.2f}")
            report.append(f"Tooling Cost: ${cost_analysis.get('tooling_cost', 0):.2f}")
            report.append(f"Setup Cost: ${cost_analysis.get('setup_cost', 0):.2f}")
            report.append(f"Overhead: ${cost_analysis.get('overhead', 0):.2f}")
            
            # Add volume discount if available
            if 'volume_discount' in cost_analysis:
                report.append(f"Volume Discount: ${cost_analysis['volume_discount']:.2f}")
            
            report.append("")
            report.append("--- Production Information ---")
            report.append(f"Estimated Lead Time: {cost_analysis.get('lead_time', 'N/A')}")
            report.append(f"Production Volume: {cost_analysis.get('production_volume', 1)}")
            
            return "\n".join(report)
        else:
            # Fall back to the original cost service
            return self.cost_service.display_cost_report()
    
    def refresh_cad_data(self):
        """
        Force refresh of CAD data
        
        Returns:
            Dict containing the refreshed CAD data
        """
        self.last_cad_data = extract_cad_data_for_features()
        return self.last_cad_data
