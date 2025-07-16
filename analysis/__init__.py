#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Analysis package for Manufacturing Co-Pilot.

This package provides CAD analysis capabilities including:
- Basic metadata extraction
- Feature detection (holes, ribs, fillets, chamfers)
- Wall thickness analysis
- Manufacturing rule checking
- Visualization of analysis results
"""

# Import local CAD analyzer (used for development and testing)
from .cad_analyzer import CADAnalyzer, FeatureVisualizer, analyze_active_document, get_analysis_summary
from .analyzer_interface import AnalyzerInterface, create_analyzer_interface

# Import cloud-based CAD analyzer (used in production)
from .cloud_analyzer_interface import CloudAnalyzerInterface, create_cloud_analyzer_interface

__all__ = [
    # Local analyzer
    'CADAnalyzer',
    'FeatureVisualizer',
    'analyze_active_document',
    'get_analysis_summary',
    'AnalyzerInterface',
    'create_analyzer_interface',
    
    # Cloud analyzer
    'CloudAnalyzerInterface',
    'create_cloud_analyzer_interface'
]
