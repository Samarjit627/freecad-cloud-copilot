"""
Cloud Analyzer Interface for the Manufacturing Co-Pilot
Connects the cloud-based CAD analyzer with the chat interface
"""

import os
import sys
import time
import threading
from typing import Dict, Any, Optional, List, Callable

import FreeCAD
import FreeCADGui

# Import local modules
try:
    from macro import cloud_analyzer
    from macro import chat_interface
except ImportError:
    # Add parent directory to path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from macro import cloud_analyzer
    from macro import chat_interface

class CloudAnalyzerInterface:
    """Interface between the cloud CAD analyzer and the chat interface"""
    
    def __init__(self, chat_interface_instance=None):
        """Initialize the analyzer interface"""
        self.analyzer = cloud_analyzer.get_analyzer()
        self.chat_interface = chat_interface_instance or chat_interface.get_interface()
        self.last_analysis = None
        self.is_analyzing = False
        self.analysis_thread = None
    
    def analyze_active_document(self) -> bool:
        """
        Analyze the active document using the cloud CAD analyzer
        
        Returns:
            bool: True if analysis was successful, False otherwise
        """
        try:
            # Check if there's an active document
            if not FreeCAD.ActiveDocument:
                self._add_message("❌ No active document. Please open a CAD model first.")
                return False
            
            # Check if already analyzing
            if self.is_analyzing:
                self._add_message("⚠️ Analysis already in progress. Please wait...")
                return False
            
            # Start analysis
            self.is_analyzing = True
            self._add_message("🔍 Analyzing CAD model in the cloud... Please wait.")
            
            # Show initial metadata while waiting for cloud analysis
            self._show_initial_metadata()
            
            # Run cloud analysis in a separate thread
            self.analysis_thread = threading.Thread(
                target=self._run_cloud_analysis,
                args=(FreeCAD.ActiveDocument,)
            )
            self.analysis_thread.daemon = True
            self.analysis_thread.start()
            
            return True
            
        except Exception as e:
            self._add_message(f"❌ Error starting analysis: {str(e)}")
            self.is_analyzing = False
            return False
    
    def _show_initial_metadata(self):
        """Show initial metadata while waiting for cloud analysis"""
        try:
            doc = FreeCAD.ActiveDocument
            
            # Basic metadata that can be extracted quickly
            message = "📊 **Basic Model Information**\n\n"
            message += f"**Model Name:** {doc.Name}\n"
            
            # Count objects
            part_count = 0
            for obj in doc.Objects:
                if hasattr(obj, "Shape"):
                    part_count += 1
            
            message += f"**Part Count:** {part_count}\n"
            
            # Get bounding box for basic dimensions
            try:
                shapes = []
                for obj in doc.Objects:
                    if hasattr(obj, "Shape"):
                        shapes.append(obj.Shape)
                
                if shapes:
                    # Create a compound shape
                    import Part
                    compound = Part.makeCompound(shapes)
                    bbox = compound.BoundBox
                    
                    # Add bounding box dimensions
                    message += f"**Dimensions (mm):** {bbox.XLength:.2f} × {bbox.YLength:.2f} × {bbox.ZLength:.2f}\n"
            except:
                pass
                
            message += "\n🔄 **Sending to cloud for detailed analysis...**\n"
            message += "This may take a moment as we analyze features like holes, fillets, chamfers, and wall thickness."
            
            self._add_message(message)
            
        except Exception as e:
            print(f"Error showing initial metadata: {str(e)}")
    
    def _run_cloud_analysis(self, document):
        """
        Run cloud analysis in a separate thread
        
        Args:
            document: FreeCAD document to analyze
        """
        try:
            # Run the analysis
            analysis = self.analyzer.analyze_document(document)
            self.last_analysis = analysis
            
            # Show results
            self._show_analysis_results(analysis)
            
        except Exception as e:
            self._add_message(f"❌ Error during cloud analysis: {str(e)}")
        finally:
            self.is_analyzing = False
    
    def _show_analysis_results(self, analysis: Dict[str, Any]):
        """
        Show analysis results in the chat interface
        
        Args:
            analysis: Analysis results from the cloud
        """
        try:
            if "error" in analysis:
                self._add_message(f"❌ Analysis error: {analysis['error']}")
                return
            
            # Format metadata
            message = "✅ **CAD Analysis Complete**\n\n"
            
            # Add metadata
            if "metadata" in analysis:
                metadata = analysis["metadata"]
                message += "**Model Information:**\n"
                
                if "name" in metadata:
                    message += f"• **Name:** {metadata['name']}\n"
                
                if "dimensions" in metadata:
                    dims = metadata["dimensions"]
                    message += f"• **Dimensions:** {dims[0]:.2f} × {dims[1]:.2f} × {dims[2]:.2f} mm\n"
                
                if "volume" in metadata:
                    message += f"• **Volume:** {metadata['volume']:.2f} cm³\n"
                
                if "surface_area" in metadata:
                    message += f"• **Surface Area:** {metadata['surface_area']:.2f} cm²\n"
                
                if "center_of_mass" in metadata:
                    com = metadata["center_of_mass"]
                    message += f"• **Center of Mass:** ({com[0]:.2f}, {com[1]:.2f}, {com[2]:.2f}) mm\n"
            
            # Add feature counts
            if "features" in analysis:
                features = analysis["features"]
                message += "\n**Detected Features:**\n"
                
                if "holes" in features:
                    message += f"• **Holes:** {len(features['holes'])}\n"
                
                if "fillets" in features:
                    message += f"• **Fillets:** {len(features['fillets'])}\n"
                
                if "chamfers" in features:
                    message += f"• **Chamfers:** {len(features['chamfers'])}\n"
                
                if "ribs" in features:
                    message += f"• **Ribs:** {len(features['ribs'])}\n"
            
            # Add wall thickness if available
            if "metadata" in analysis and "min_wall_thickness" in analysis["metadata"]:
                metadata = analysis["metadata"]
                message += "\n**Wall Thickness Analysis:**\n"
                message += f"• **Minimum:** {metadata['min_wall_thickness']:.2f} mm\n"
                message += f"• **Maximum:** {metadata['max_wall_thickness']:.2f} mm\n"
                message += f"• **Average:** {metadata['avg_wall_thickness']:.2f} mm\n"
            
            # Add manufacturing insights if available
            if "manufacturing_insights" in analysis:
                insights = analysis["manufacturing_insights"]
                message += "\n**Manufacturing Insights:**\n"
                
                for insight in insights:
                    message += f"• {insight}\n"
            
            # Add prompt for questionnaire
            message += "\n🔍 **Would you like to start the manufacturing questionnaire to get more detailed insights?**"
            
            self._add_message(message)
            
        except Exception as e:
            self._add_message(f"❌ Error displaying analysis results: {str(e)}")
    
    def _add_message(self, content: str):
        """
        Add a message to the chat interface
        
        Args:
            content: Message content
        """
        if self.chat_interface:
            self.chat_interface.add_chat_message("Assistant", content)
        else:
            print(content)

def create_cloud_analyzer_interface(chat_interface_instance=None) -> CloudAnalyzerInterface:
    """
    Create a cloud analyzer interface
    
    Args:
        chat_interface_instance: Chat interface instance
        
    Returns:
        CloudAnalyzerInterface instance
    """
    return CloudAnalyzerInterface(chat_interface_instance)
