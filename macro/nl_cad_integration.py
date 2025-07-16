"""
Integration module for NL CAD in main macro
"""

from PySide2 import QtWidgets
import sys
import os

# Ensure the macro directory is in the Python path
macro_dir = os.path.dirname(os.path.abspath(__file__))
if macro_dir not in sys.path:
    sys.path.append(macro_dir)

# Use absolute imports instead of relative imports
from nl_cad_base import NaturalLanguageCADEditor
from advanced_commands import AdvancedCommands
from standard_parts import StandardParts
from manufacturing_features import ManufacturingFeatures
from optimization_features import OptimizationFeatures
from advanced_ui_widgets import ContextWidget, SuggestionsWidget, AssemblyWidget, NLCommandWidget

def integrate_nl_cad(chat_interface):
    """Integrate NL CAD into chat interface - Stage 3"""
    
    # Create NL editor
    nl_editor = NaturalLanguageCADEditor()
    
    # Initialize all modules using the built-in method
    nl_editor.initialize_modules()
    
    # Set cloud client if available
    if hasattr(chat_interface, 'cloud_client') and chat_interface.cloud_client:
        print("Debug: Setting cloud client from chat interface to NL editor")
        nl_editor.set_cloud_client(chat_interface.cloud_client)
    else:
        print("Debug: No cloud client available in chat interface")
    
    # Create main container
    container = QtWidgets.QWidget()
    container_layout = QtWidgets.QHBoxLayout(container)
    
    # Left side - command input
    left_widget = QtWidgets.QWidget()
    left_layout = QtWidgets.QVBoxLayout(left_widget)
    
    nl_widget = NLCommandWidget(nl_editor)
    left_layout.addWidget(nl_widget)
    
    assembly_widget = AssemblyWidget(nl_editor)
    left_layout.addWidget(assembly_widget)
    
    container_layout.addWidget(left_widget)
    
    # Right side - context and suggestions
    right_widget = QtWidgets.QWidget()
    right_layout = QtWidgets.QVBoxLayout(right_widget)
    
    context_widget = ContextWidget(nl_editor.context)
    right_layout.addWidget(context_widget)
    
    suggestions_widget = SuggestionsWidget(nl_editor)
    right_layout.addWidget(suggestions_widget)
    
    right_layout.addStretch()
    
    container_layout.addWidget(right_widget)
    
    # Add to interface
    if hasattr(chat_interface, 'layout'):
        layout = chat_interface.layout()
        
        # Add separator
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        layout.insertWidget(layout.count() - 1, separator)
        
        # Add container
        layout.insertWidget(layout.count() - 1, container)
    
    # Add a welcome message about CAD commands
    chat_interface.add_message("Assistant", "✨ Natural Language CAD commands are now available!\n\n" +
                           "Basic shapes: 'create a box 100x50x20', 'make a cylinder 30x50'\n" +
                           "Manufacturing: 'add draft angles', 'add reinforcement ribs', 'make this part hollow'\n" +
                           "Standard parts: 'create a gear with 24 teeth', 'create bearing block', 'create shaft'\n" +
                           "Optimization: 'make this moldable', 'optimize for 3D printing', 'reduce weight by 30%'\n" +
                           "Assembly: 'create a gearbox with 3:1 reduction', 'create a motor mount for NEMA17'\n" +
                           "AI Design: 'suggest next steps', 'analyze design', 'design a bracket with mounting holes'")
    
    # Extend chat handling for advanced commands
    original_send = chat_interface.send_message
    
    def enhanced_send():
        text = chat_interface.input_field.text()
        
        if not text.strip():
            return
        
        # Let NL editor handle all CAD-related commands
        result = nl_editor.process_command(text)
        if result.get('handled', True):  # Default to handled
            chat_interface.add_message("User", text)
            chat_interface.add_message("Assistant", result['message'])
            chat_interface.input_field.clear()
            
            # Update context widget
            context_widget.update_display()
            
            # Refresh suggestions
            suggestions_widget.refresh_suggestions()
        else:
            original_send()
    
    chat_interface.send_message = enhanced_send
    
    return container
