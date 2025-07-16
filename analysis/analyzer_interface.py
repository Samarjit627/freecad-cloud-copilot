#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Analyzer Interface Module for Manufacturing Co-Pilot

This module connects the CAD analyzer to the chat interface,
handling the display of analysis results and initiating the questionnaire.
"""

import FreeCAD
import os
import json
from typing import Dict, List, Any, Optional

# Import local modules
# Use relative imports for modules within the package
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from analysis.cad_analyzer import CADAnalyzer, FeatureVisualizer
from macro.ui_components import MessageCard


class AnalyzerInterface:
    """
    Interface between the CAD analyzer and the chat interface.
    Handles displaying analysis results and initiating the questionnaire.
    """
    
    def __init__(self, chat_interface=None):
        """
        Initialize the analyzer interface.
        
        Args:
            chat_interface: Reference to the chat interface
        """
        self.chat_interface = chat_interface
        self.analyzer = None
        self.visualizer = None
        self.analysis_results = None
        self.questionnaire_initiated = False
    
    def analyze_active_document(self):
        """
        Analyze the active FreeCAD document and display initial results.
        
        Returns:
            bool: True if analysis was successful, False otherwise
        """
        try:
            doc = FreeCAD.ActiveDocument
            if not doc:
                if self.chat_interface:
                    self.chat_interface.add_chat_message(
                        "assistant", 
                        "No active document found. Please open a CAD model first."
                    )
                return False
            
            # Create analyzer and perform analysis
            self.analyzer = CADAnalyzer(doc)
            self.analysis_results = self.analyzer.analyze()
            
            # Create visualizer
            self.visualizer = FeatureVisualizer(doc, self.analyzer)
            
            # Display initial results
            self._display_initial_results()
            
            return True
            
        except Exception as e:
            if self.chat_interface:
                self.chat_interface.add_chat_message(
                    "assistant", 
                    f"Error analyzing document: {str(e)}"
                )
            return False
    
    def _display_initial_results(self):
        """Display initial analysis results in the chat interface."""
        if not self.chat_interface or not self.analysis_results:
            return
        
        # Get summary for display
        summary = self.analyzer.get_summary()
        
        # Create formatted message
        message = self._format_initial_results(summary)
        
        # Add message to chat
        self.chat_interface.add_chat_message("assistant", message)
    
    def _format_initial_results(self, summary: Dict[str, Any]) -> str:
        """
        Format initial analysis results for display.
        
        Args:
            summary: Analysis summary
            
        Returns:
            str: Formatted message
        """
        # Create a box with the initial results
        message = "## CAD Analysis Complete\n\n"
        message += "```\n"
        message += f"┌─ CAD ANALYSIS ─────────────────────────────┐\n"
        message += f"│ Part Name: {summary['part_name']}\n"
        message += f"│ Type: {summary['type']}\n"
        message += f"│ Volume: {summary['volume']}\n"
        message += f"│ Dimensions: {summary['dimensions']}\n"
        message += f"│ Surface Area: {summary['surface_area']}\n"
        message += f"│ Center of Mass: {summary['center_of_mass']}\n"
        message += f"└──────────────────────────────────────────────┘\n"
        message += "```\n\n"
        
        # Add feature counts
        message += "### Detected Features\n"
        message += f"- Holes: {summary['feature_counts']['holes']}\n"
        message += f"- Fillets: {summary['feature_counts']['fillets']}\n"
        message += f"- Chamfers: {summary['feature_counts']['chamfers']}\n"
        message += f"- Ribs: {summary['feature_counts']['ribs']}\n"
        
        # Add wall thickness if available
        if 'min_wall_thickness' in self.analysis_results['metadata']:
            min_thickness = self.analysis_results['metadata']['min_wall_thickness']
            max_thickness = self.analysis_results['metadata']['max_wall_thickness']
            avg_thickness = self.analysis_results['metadata']['avg_wall_thickness']
            
            message += "\n### Wall Thickness\n"
            message += f"- Minimum: {min_thickness:.2f} mm\n"
            message += f"- Maximum: {max_thickness:.2f} mm\n"
            message += f"- Average: {avg_thickness:.2f} mm\n"
        
        # Add prompt for questionnaire
        message += "\nTo provide the most relevant manufacturing guidance, "
        message += "I'd like to understand your requirements better. "
        message += "Would you like to start the manufacturing questionnaire now?"
        
        return message
    
    def start_questionnaire(self):
        """
        Initiate the manufacturing questionnaire.
        
        Returns:
            bool: True if questionnaire was started, False otherwise
        """
        if not self.chat_interface:
            return False
            
        if self.questionnaire_initiated:
            self.chat_interface.add_chat_message(
                "assistant", 
                "The questionnaire has already been initiated."
            )
            return False
        
        # Import questionnaire module here to avoid circular imports
        from macro.questionnaire import ManufacturingQuestionnaire
        
        # Create questionnaire
        questionnaire = ManufacturingQuestionnaire(self.chat_interface)
        
        # Start questionnaire
        questionnaire.start()
        
        self.questionnaire_initiated = True
        return True
    
    def display_detailed_analysis(self, context=None):
        """
        Display detailed analysis results based on questionnaire context.
        
        Args:
            context: Context from questionnaire responses
            
        Returns:
            bool: True if display was successful, False otherwise
        """
        if not self.chat_interface or not self.analysis_results:
            return False
            
        if not context:
            context = {}
            
        # Create message with detailed analysis
        message = self._format_detailed_analysis(context)
        
        # Add message to chat
        self.chat_interface.add_chat_message("assistant", message)
        
        return True
    
    def _format_detailed_analysis(self, context: Dict[str, Any]) -> str:
        """
        Format detailed analysis results for display.
        
        Args:
            context: Context from questionnaire responses
            
        Returns:
            str: Formatted message
        """
        # Extract relevant context
        process = context.get('manufacturing_process', 'Unknown')
        material = context.get('material', 'Unknown')
        volume = context.get('production_volume', 'Unknown')
        
        # Create header
        message = "## Manufacturing Analysis\n\n"
        
        # Add context summary
        message += "Based on your requirements:\n"
        message += f"- Manufacturing Process: {process}\n"
        message += f"- Material: {material}\n"
        message += f"- Production Volume: {volume}\n\n"
        
        # Add findings box
        message += "```\n"
        message += f"┌─ MANUFACTURING ANALYSIS ─────────────────────┐\n"
        message += f"│ Initial Findings:                            │\n"
        
        # Count potential issues
        issues = []
        
        # Check wall thickness for the selected process
        if 'min_wall_thickness' in self.analysis_results['metadata']:
            min_thickness = self.analysis_results['metadata']['min_wall_thickness']
            
            # Different processes have different minimum wall thickness requirements
            min_required = 0.5  # Default
            if process.lower() == 'injection molding':
                if material.lower() in ['abs', 'plastic', 'polymer']:
                    min_required = 0.5
                else:
                    min_required = 0.8
            elif process.lower() == 'die casting':
                min_required = 0.9
            elif process.lower() == 'cnc machining':
                min_required = 0.5
                
            if min_thickness < min_required:
                issues.append(f"Wall thickness ({min_thickness:.2f}mm) below minimum for {process} ({min_required}mm)")
        
        # Check for small holes
        small_holes = 0
        for hole in self.analysis_results['features']['holes']:
            if hole['diameter'] < 1.0:  # Example threshold
                small_holes += 1
                
        if small_holes > 0:
            issues.append(f"Found {small_holes} holes with diameter < 1.0mm")
        
        # Add issues count
        message += f"│ • {len(issues)} potential manufacturability issues  │\n"
        
        # Add optimization opportunities
        opportunities = []
        
        # Check for potential draft angle issues (simplified)
        if process.lower() == 'injection molding' or process.lower() == 'die casting':
            opportunities.append("Consider adding draft angles to vertical walls")
        
        # Check for potential material reduction
        if 'max_wall_thickness' in self.analysis_results['metadata']:
            max_thickness = self.analysis_results['metadata']['max_wall_thickness']
            if max_thickness > 5.0:  # Example threshold
                opportunities.append("Potential material reduction in thick sections")
        
        # Add opportunities count
        message += f"│ • {len(opportunities)} cost optimization opportunities │\n"
        
        # Add process compatibility
        compatible_processes = ['CNC Machining']
        
        # Simple rules for process compatibility
        if 'min_wall_thickness' in self.analysis_results['metadata']:
            min_thickness = self.analysis_results['metadata']['min_wall_thickness']
            if min_thickness >= 0.5:
                compatible_processes.append('Injection Molding')
            if min_thickness >= 0.9:
                compatible_processes.append('Die Casting')
                
        # Format compatible processes
        process_str = ', '.join(compatible_processes)
        message += f"│ • Compatible with: {process_str} │\n"
        
        message += f"└──────────────────────────────────────────────┘\n"
        message += "```\n\n"
        
        # Add detailed issues
        if issues:
            message += "### Potential Issues\n"
            for i, issue in enumerate(issues):
                message += f"{i+1}. {issue}\n"
            message += "\n"
        
        # Add detailed opportunities
        if opportunities:
            message += "### Optimization Opportunities\n"
            for i, opportunity in enumerate(opportunities):
                message += f"{i+1}. {opportunity}\n"
            message += "\n"
        
        # Add next steps
        message += "### Next Steps\n"
        message += "Would you like me to:\n"
        message += "1. Explain any of these issues in more detail?\n"
        message += "2. Show visualization of problem areas?\n"
        message += "3. Suggest specific improvements for any issue?\n"
        
        return message
    
    def visualize_feature(self, feature_type):
        """
        Visualize a specific feature type.
        
        Args:
            feature_type: Type of feature to visualize ('wall_thickness', 'holes', etc.)
            
        Returns:
            bool: True if visualization was successful, False otherwise
        """
        if not self.visualizer:
            return False
            
        # Clear existing visualizations
        self.visualizer.clear_visualizations()
        
        # Create visualization based on feature type
        if feature_type == 'wall_thickness':
            self.visualizer.show_wall_thickness()
            return True
        elif feature_type == 'holes':
            self.visualizer.show_holes()
            return True
        else:
            return False


def create_analyzer_interface(chat_interface):
    """
    Create and return an analyzer interface instance.
    
    Args:
        chat_interface: Reference to the chat interface
        
    Returns:
        AnalyzerInterface: Analyzer interface instance
    """
    return AnalyzerInterface(chat_interface)
