"""
Advanced Chat Interface for the FreeCAD Manufacturing Co-Pilot
Handles the main chat UI and interaction flow
Includes multi-agent system integration
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable

from PySide2 import QtWidgets, QtCore, QtGui

# Import local modules
try:
    import config
    import cloud_client
    import cad_analyzer
    import ai_engine
    import questionnaire
    import ui_components
except ImportError:
    import config
    import cloud_client
    import cad_analyzer
    import ai_engine
    import questionnaire
    import ui_components

class ManufacturingChatInterface(QtWidgets.QWidget):
    """Manufacturing Chat Interface"""
    
    # Class variable to track instances
    _instances = []
    
    @classmethod
    def cleanup_instances(cls):
        """Aggressively clean up all existing instances and UI elements"""
        print("AGGRESSIVE CLEANUP: Removing all Manufacturing Co-Pilot UI elements...")
        
        # 1. First try to close any active FreeCAD task dialogs
        try:
            import FreeCADGui
            if FreeCADGui.Control.activeDialog():
                print("Closing active FreeCAD task dialog")
                FreeCADGui.Control.closeDialog()
        except Exception as e:
            print(f"Error closing FreeCAD task dialog: {e}")
        
        # 2. Clean up our tracked instances
        instances_to_remove = []
        for instance in cls._instances:
            try:
                print(f"Closing tracked instance: {instance}")
                # Try multiple close methods
                for method_name in ['close', 'hide', 'deleteLater', 'destroy']:
                    if hasattr(instance, method_name) and callable(getattr(instance, method_name)):
                        try:
                            getattr(instance, method_name)()
                            print(f"  - Called {method_name}() on instance")
                        except Exception as method_err:
                            print(f"  - Error calling {method_name}(): {method_err}")
                
                # Force removal
                instances_to_remove.append(instance)
            except Exception as e:
                print(f"Error handling instance: {e}")
                instances_to_remove.append(instance)
        
        # Clear our instance tracking list
        cls._instances.clear()
        
        # 3. Reset global instance reference
        global _chat_interface_instance
        _chat_interface_instance = None
        
        # 4. Reset all global flags we can find
        try:
            import sys
            for module_name in ['__main__', 'ImprovedCoPilot']:
                if module_name in sys.modules:
                    module = sys.modules[module_name]
                    for flag_name in ['_COPILOT_RUNNING', '_INTERFACE_CREATION_IN_PROGRESS']:
                        if hasattr(module, flag_name):
                            print(f"Resetting global {flag_name} flag in {module_name}")
                            setattr(module, flag_name, False)
        except Exception as e:
            print(f"Error resetting global flags: {e}")
        
        # 5. Find and close ALL widgets with Co-Pilot in the title
        try:
            from PySide2 import QtWidgets
            for widget in QtWidgets.QApplication.topLevelWidgets():
                try:
                    if hasattr(widget, 'windowTitle'):
                        title = widget.windowTitle()
                        if 'Co-Pilot' in title or 'Manufacturing' in title:
                            print(f"Closing widget: {title}")
                            # Try multiple close methods
                            for method_name in ['close', 'hide', 'deleteLater', 'destroy']:
                                if hasattr(widget, method_name) and callable(getattr(widget, method_name)):
                                    try:
                                        getattr(widget, method_name)()
                                        print(f"  - Called {method_name}() on widget")
                                    except Exception as method_err:
                                        print(f"  - Error calling {method_name}(): {method_err}")
                except Exception as widget_err:
                    print(f"Error handling widget: {widget_err}")
        except Exception as e:
            print(f"Error cleaning up widgets: {e}")
        
        # 6. Force garbage collection
        try:
            import gc
            gc.collect()
            print("Forced garbage collection")
        except Exception as e:
            print(f"Error during garbage collection: {e}")
        
        print("AGGRESSIVE CLEANUP COMPLETE")
        
        # Reset creation flag
        global _INTERFACE_CREATION_IN_PROGRESS
        _INTERFACE_CREATION_IN_PROGRESS = False
    
    def __init__(self, parent=None):
        """Initialize the chat interface"""
        # Clean up existing instances first
        ManufacturingChatInterface.cleanup_instances()
        
        # Initialize the widget
        super().__init__(parent)
        
        # Add self to instances list
        ManufacturingChatInterface._instances.append(self)
        
        # Set window title to help identify this widget
        self.setWindowTitle("Manufacturing Co-Pilot Chat")
        
        # Initialize properties
        self.cloud_client = cloud_client.get_client()
        self.ai_engine = ai_engine.ManufacturingIntelligenceEngine()
        self.is_processing = False
        self.cad_analyzer = cad_analyzer.AdvancedCADAnalyzer()
        
        # Agent system state
        self.available_agents = []
        self.current_agent_id = None
        
        # State variables
        self.cad_analysis = {}
        self.user_context = {}
        self.is_processing = False
        
        # Setup UI
        self.setup_ui()
        
        # Check cloud connection
        self.check_cloud_connection()
    
    def setup_ui(self):
        """Setup the UI for the chat interface"""
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Set global style to ensure text is visible
        self.setStyleSheet("""
            QWidget {
                color: #000000;
            }
            QLabel {
                color: #000000;
            }
            QPushButton {
                color: #000000;
            }
            QLineEdit {
                color: #000000;
                background-color: white;
            }
            QTextEdit {
                color: #000000;
                background-color: white;
            }
            QTextBrowser {
                color: #000000;
            }
            QComboBox {
                color: #000000;
                background-color: white;
            }
        """)
        
        # Chat panel
        chat_panel = QtWidgets.QWidget()
        chat_panel.setMinimumWidth(500)
        chat_layout = QtWidgets.QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # Chat header
        chat_header = QtWidgets.QWidget()
        chat_header.setStyleSheet("""
            background-color: #f9fafb;
            border-bottom: 1px solid #e5e7eb;
        """)
        chat_header_layout = QtWidgets.QHBoxLayout(chat_header)
        
        header_label = QtWidgets.QLabel("🚀 Manufacturing Co-Pilot")
        header_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #111827;
        """)
        
        chat_header_layout.addWidget(header_label)
        chat_header_layout.addStretch()
        
        # Cloud status widget
        self.cloud_status = ui_components.CloudStatusWidget()
        chat_header_layout.addWidget(self.cloud_status)
        
        chat_layout.addWidget(chat_header)
        
        # Chat messages area
        chat_messages_container = QtWidgets.QWidget()
        chat_messages_layout = QtWidgets.QVBoxLayout(chat_messages_container)
        chat_messages_layout.setContentsMargins(10, 10, 10, 10)
        chat_messages_layout.setSpacing(15)
        
        # Scroll area for messages
        self.messages_scroll = QtWidgets.QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.messages_scroll.setWidget(chat_messages_container)
        
        # Store references for adding messages
        self.messages_container = chat_messages_container
        self.messages_layout = chat_messages_layout
        
        # Add stretch to push messages to the top
        chat_messages_layout.addStretch()
        
        chat_layout.addWidget(self.messages_scroll)
        self.messages_layout.setContentsMargins(0, 0, 0, 0)
        self.messages_layout.setSpacing(15)
        self.messages_layout.addStretch()
        
        # Input area
        input_container = QtWidgets.QWidget()
        input_layout = QtWidgets.QVBoxLayout(input_container)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(10)
        
        # Input field and send button
        input_field_layout = QtWidgets.QHBoxLayout()
        
        self.input_field = QtWidgets.QTextEdit()
        self.input_field.setPlaceholderText("Ask about manufacturing...")
        self.input_field.setMaximumHeight(80)
        self.input_field.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
            }
        """)
        
        # Connect return key to send message
        self.input_field.installEventFilter(self)
        
        self.send_button = QtWidgets.QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background: #4f46e5;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 14px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #4338ca;
            }
            QPushButton:pressed {
                background: #3730a3;
            }
            QPushButton:disabled {
                background: #9ca3af;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        
        input_field_layout.addWidget(self.input_field)
        input_field_layout.addWidget(self.send_button)
        
        input_layout.addLayout(input_field_layout)
        
        # Quick action buttons
        quick_actions = QtWidgets.QHBoxLayout()
        quick_actions.setSpacing(8)
        
        # Define quick action button style
        button_style = """
            QPushButton {
                background-color: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 16px;
                padding: 4px 12px;
                font-size: 13px;
                font-weight: 500;
                color: #374151;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
            QPushButton:pressed {
                background-color: #d1d5db;
            }
        """
        
        # Create quick action buttons
        self.analyze_button = QtWidgets.QPushButton("🔍 Analyze")
        self.analyze_button.setStyleSheet(button_style)
        self.analyze_button.clicked.connect(self.analyze_cad)
        quick_actions.addWidget(self.analyze_button)
        
        self.suggestions_button = QtWidgets.QPushButton("💡 Suggestions")
        self.suggestions_button.setStyleSheet(button_style)
        self.suggestions_button.clicked.connect(self.show_suggestions)
        quick_actions.addWidget(self.suggestions_button)
        
        self.clear_button = QtWidgets.QPushButton("🗑️ Clear")
        self.clear_button.setStyleSheet(button_style)
        self.clear_button.clicked.connect(self.clear_chat)
        quick_actions.addWidget(self.clear_button)
        
        # Add stretch to push buttons to the left
        quick_actions.addStretch()
        
        input_layout.addLayout(quick_actions)
        
        chat_layout.addWidget(input_container)
        
        # Add chat panel to main layout
        main_layout.addWidget(chat_panel)
        
        # Set window properties
        self.setWindowTitle("Manufacturing Co-Pilot")
        self.resize(900, 700)
        
        # Add welcome message
        self.add_welcome_message()
    
    def eventFilter(self, obj, event):
        """Event filter for handling return key in input field"""
        if obj == self.input_field and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Return and not event.modifiers() & QtCore.Qt.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)
    
    def add_welcome_message(self):
        """Add welcome message to the chat"""
        welcome_message = """
        # 🚀 Manufacturing Co-Pilot

        Welcome to the FreeCAD Manufacturing Co-Pilot! I'm here to help you with:
        
        - Design for Manufacturing (DFM) advice
        - Manufacturing process selection
        - Cost optimization
        - CAD model analysis
        - Engineering insights
        
        How can I assist you today?
        """
        
        self.add_chat_message("Assistant", welcome_message)
        
        # Add suggestion prompt
        self.add_chat_message("Assistant", "Click the 💡 Suggestions button anytime to see contextual suggestions based on your current design.")
        
    def add_chat_message(self, role: str, content: str):
        """Add a message to the chat"""
        # Create message widget with explicit styling
        message_widget = ui_components.ChatMessageWidget(role, content)

        # Force update the widget to ensure it's visible
        message_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
            QLabel {
                color: #000000;
            }
        """)

        # Add to layout
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_widget)

        # Force update and scroll
        self.messages_container.updateGeometry()
        self.messages_scroll.updateGeometry()
        QtWidgets.QApplication.processEvents()
        self.scroll_to_bottom()
        
    def scroll_to_bottom(self):
        """Scroll the chat to the bottom"""
        self.messages_scroll.verticalScrollBar().setValue(
            self.messages_scroll.verticalScrollBar().maximum()
        )
        
    def eventFilter(self, obj, event):
        """Filter events for input field"""
        if obj == self.input_field and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Return and not event.modifiers() & QtCore.Qt.ShiftModifier:
                # Enter without shift sends message
                self.send_message()
                return True
            elif event.key() == QtCore.Qt.Key_Return and event.modifiers() & QtCore.Qt.ShiftModifier:
                # Shift+Enter adds newline
                cursor = self.input_field.textCursor()
                cursor.insertText("\n")
                return True
                
        return super().eventFilter(obj, event)
        
    def send_message(self):
        """Send a message from the input field"""
        # Get message text
        message = self.input_field.toPlainText().strip()
        if not message:
            return

        # Clear input field
        self.input_field.clear()

        # Add message to chat
        self.add_chat_message("User", message)
        
        # Disable send button during processing
        self.send_button.setEnabled(False)
        self.send_button.setText("Processing...")
        
        # Set processing flag
        self.is_processing = True
        
        # Create thread for getting response
        self.response_thread = GetResponseThread(
            self.ai_engine,
            message,
            self.cad_analysis,
            self.user_context,
            "general"  # Default mode
        )
        
        # Connect signal
        self.response_thread.response_ready.connect(self.handle_response)
        
        # Start thread
        self.response_thread.start()
        
    def show_suggestions(self):
        """Show contextual suggestions in the chat"""
        # Get current document and selection
        try:
            import FreeCAD
            doc = FreeCAD.ActiveDocument
            has_doc = doc is not None
            selection = FreeCAD.Gui.Selection.getSelection()
            has_selection = len(selection) > 0
        except:
            has_doc = False
            has_selection = False
        
        # Create contextual suggestions based on document state
        suggestions = []
        
        if not has_doc:
            suggestions.append("Create a new part")
            suggestions.append("Open a CAD file")
            suggestions.append("What can you help me with?")
        elif not has_selection:
            suggestions.append("Create a basic shape")
            suggestions.append("Analyze this design")
            suggestions.append("How can I improve this part?")
        else:
            # With selection
            obj_types = [obj.TypeId for obj in selection]
            
            if any('Mesh' in t for t in obj_types):
                suggestions.append("Convert this mesh to a solid")
            
            if len(selection) == 1:
                suggestions.append(f"Add fillets to this {selection[0].Label}")
                suggestions.append(f"Create a pattern of this {selection[0].Label}")
            else:
                suggestions.append("Combine these objects")
                suggestions.append("Create an assembly")
            
            suggestions.append("How can I optimize these parts?")
        
        # Add manufacturing-specific suggestions
        suggestions.append("What manufacturing process is best for this part?")
        suggestions.append("How can I reduce the cost of manufacturing?")
        
        # Display suggestions in chat
        suggestion_text = "**Suggested Actions:**\n\n"
        for suggestion in suggestions[:5]:  # Limit to 5 suggestions
            suggestion_text += f"• {suggestion}\n"
        
        self.add_chat_message("Assistant", suggestion_text)
        
    def analyze_cad(self):
        """Analyze the current CAD document and display results in chat"""
        import FreeCAD
        
        # Check if a document is open
        if not FreeCAD.ActiveDocument:
            self.add_chat_message("Assistant", "⚠️ No document is currently open. Please open or create a document first.")
            return
            
        # Disable the analyze button during processing
        self.analyze_button.setEnabled(False)
        self.analyze_button.setText("Analyzing...")
        
        # Add a message to indicate analysis is starting
        self.add_chat_message("Assistant", "🔍 Analyzing your CAD model...")
        
        # Run analysis in a separate thread
        self.analyze_thread = AnalyzeCADThread(self.cad_analyzer, FreeCAD.ActiveDocument)
        self.analyze_thread.analysis_ready.connect(self.handle_analysis_results)
        self.analyze_thread.error_occurred.connect(self.handle_analysis_error)
        self.analyze_thread.start()
    
    def handle_analysis_results(self, results):
        """Handle the results of CAD analysis"""
        # Format the analysis results as a message
        message = "## 📊 CAD Analysis Results\n\n"
        
        if "metadata" in results:
            metadata = results["metadata"]
            message += "### Model Information\n"
            message += f"- **Name**: {metadata.get('name', 'Unknown')}\n"
            message += f"- **Volume**: {metadata.get('volume', 0):.2f} cm³\n"
            message += f"- **Surface Area**: {metadata.get('surface_area', 0):.2f} cm²\n"
            message += f"- **Dimensions**: {metadata.get('x_length', 0):.2f} × {metadata.get('y_length', 0):.2f} × {metadata.get('z_length', 0):.2f} mm\n"
            
        if "manufacturing_insights" in results and results["manufacturing_insights"]:
            message += "\n### Manufacturing Insights\n"
            for insight in results["manufacturing_insights"]:
                message += f"- {insight}\n"
        
        # Add the analysis results to the chat
        self.add_chat_message("Assistant", message)
        
        # Re-enable the analyze button
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("🔍 Analyze")
    
    def handle_analysis_error(self, error_message):
        """Handle errors during CAD analysis"""
        self.add_chat_message("Assistant", f"⚠️ Error during analysis: {error_message}")
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("🔍 Analyze")
    
    def clear_chat(self):
        """Clear all messages from the chat"""
        # Remove all message widgets except the last one (input area)
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add welcome message back
        self.add_welcome_message()
    
    def check_cloud_connection(self):
        """Check cloud connection status"""
        # Run in a separate thread
        self.cloud_thread = CloudThread(self.cloud_client)
        self.cloud_thread.status_ready.connect(self.update_cloud_status)
        self.cloud_thread.start()
    
    def update_cloud_status(self, connected):
        """Update cloud connection status"""
        if connected:
            self.add_chat_message("Assistant", "✅ Connected to Manufacturing Co-Pilot cloud service.")
        else:
            self.add_chat_message("Assistant", "⚠️ Not connected to cloud service. Some features may be limited.")
    
    def fetch_available_agents(self):
        """Fetch available manufacturing agents"""
        # Run in a separate thread
        self.fetch_agents_thread = FetchAgentsThread(self.ai_engine)
        self.fetch_agents_thread.agents_ready.connect(self.update_available_agents)
        self.fetch_agents_thread.error_occurred.connect(self.handle_agent_fetch_error)        
        self.fetch_agents_thread.start()

class AnalyzeCADThread(QtCore.QThread):
    """Thread for analyzing CAD documents"""
    analysis_ready = QtCore.Signal(object)
    error_occurred = QtCore.Signal(str)
    
    def __init__(self, analyzer, document):
        super().__init__()
        self.analyzer = analyzer
        self.document = document
    
    def run(self):
        try:
            # Perform the analysis
            results = self.analyzer.analyze_document(self.document)
            self.analysis_ready.emit(results)
        except Exception as e:
            import traceback
            print(f"Error in CAD analysis: {str(e)}")
            traceback.print_exc()
            self.error_occurred.emit(str(e))

class GetResponseThread(QtCore.QThread):
    """Thread for getting AI response"""
    response_ready = QtCore.Signal(str)
    error_occurred = QtCore.Signal(str)
    
    def __init__(self, ai_engine, query, cad_analysis, user_context, mode):
        super().__init__()
        self.ai_engine = ai_engine
        self.query = query
        self.cad_analysis = cad_analysis or {}
        self.user_context = user_context or {}
        self.mode = mode
    
    def run(self):
        """Run the thread"""
        try:
            # Log the query attempt
            print(f"Getting expert advice in {self.mode} mode: {self.query[:50]}...")
            
            # Check if we have CAD analysis
            has_analysis = bool(self.cad_analysis and not ('error' in self.cad_analysis))
            if not has_analysis:
                print("Warning: No CAD analysis available for this query")
            
            # Get response from AI engine
            response = self.ai_engine.get_expert_advice(
                self.query,
                self.cad_analysis,
                self.user_context,
                self.mode
            )
            
            self.response_ready.emit(response)
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error getting expert advice: {error_msg}")
            
            if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                self.response_ready.emit(f"❌ **Connection Error:** Could not reach the AI service. Please check your network connection and try again.")
            elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                self.response_ready.emit(f"❌ **Authentication Error:** There was an issue with the API authentication. Please check your API keys in the configuration.")
            else:
                self.response_ready.emit(f"❌ **Error:** {error_msg}\n\nPlease try again or check the console for more details.")

class QueryAgentThread(QtCore.QThread):
    """Thread for querying a specific manufacturing agent"""
    
    response_ready = QtCore.Signal(str)
    
    def __init__(self, ai_engine, agent_id, query, cad_analysis):
        super().__init__()
        self.ai_engine = ai_engine
        self.agent_id = agent_id
        self.query = query
        self.cad_analysis = cad_analysis or {}
    
    def run(self):
        """Run the thread"""
        try:
            # Log the query attempt
            print(f"Querying agent {self.agent_id} with: {self.query[:50]}...")
            
            response = self.ai_engine.query_agent(
                self.agent_id,
                self.query,
                self.cad_analysis
            )
            
            # Extract response text from dictionary
            if isinstance(response, dict) and 'response' in response:
                self.response_ready.emit(response['response'])
            elif isinstance(response, dict) and 'error' in response:
                self.response_ready.emit(f"❌ **Agent Error:** {response['error']}")
            else:
                self.response_ready.emit(str(response))
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error querying agent {self.agent_id}: {error_msg}")
            
            if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                self.response_ready.emit(f"❌ **Connection Error:** Could not reach the {self.agent_id} agent. Please check your network connection and try again.")
            else:
                self.response_ready.emit(f"❌ **Agent Error:** The {self.agent_id} agent encountered an issue. {error_msg}")

class OrchestrationThread(QtCore.QThread):
    """Thread for orchestrating multiple manufacturing agents"""
    
    response_ready = QtCore.Signal(str)
    
    def __init__(self, ai_engine, agent_ids, query, cad_analysis):
        super().__init__()
        self.ai_engine = ai_engine
        self.agent_ids = agent_ids
        self.query = query
        self.cad_analysis = cad_analysis or {}
    
    def run(self):
        """Run the thread"""
        try:
            # Log the orchestration attempt
            agent_names = ", ".join(self.agent_ids)
            print(f"Orchestrating agents ({agent_names}) with query: {self.query[:50]}...")
            
            response = self.ai_engine.orchestrate_agents(
                self.query,
                self.cad_analysis,
                self.agent_ids
            )
            
            # Extract response text from dictionary
            if isinstance(response, dict) and 'summary' in response:
                self.response_ready.emit(response['summary'])
            elif isinstance(response, dict) and 'error' in response:
                self.response_ready.emit(f"❌ **Orchestration Error:** {response['error']}")
            else:
                self.response_ready.emit(str(response))
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error orchestrating agents {self.agent_ids}: {error_msg}")
            
            if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                self.response_ready.emit(f"❌ **Connection Error:** Could not orchestrate the selected agents. Please check your network connection and try again.")
            elif "parameter" in error_msg.lower() or "argument" in error_msg.lower() or "type" in error_msg.lower():
                self.response_ready.emit(f"❌ **System Error:** There was an issue with the agent orchestration parameters. This is likely a temporary system issue. Please try again with fewer agents.")
            else:
                self.response_ready.emit(f"❌ **Orchestration Error:** The multi-agent system encountered an issue. {error_msg}")

class CloudThread(QtCore.QThread):
    """Thread for checking cloud connection"""
    status_ready = QtCore.Signal(bool)
    
    def __init__(self, cloud_client):
        super().__init__()
        self.cloud_client = cloud_client
    
    def run(self):
        try:
            if self.cloud_client:
                connected = self.cloud_client.test_connection()
            else:
                connected = False
            self.status_ready.emit(connected)
        except Exception as e:
            print(f"Error checking cloud connection: {str(e)}")
            self.status_ready.emit(False)

class FetchAgentsThread(QtCore.QThread):
    """Thread for fetching available manufacturing agents"""
    
    agents_ready = QtCore.Signal(list)
    error_occurred = QtCore.Signal(str)
    
    def __init__(self, ai_engine):
        super().__init__()
        self.ai_engine = ai_engine
    
    def run(self):
        """Run the thread"""
        try:
            print("Fetching available manufacturing agents...")
            agents = self.ai_engine.get_available_agents()
            
            if agents:
                print(f"Found {len(agents)} manufacturing agents")
                for agent in agents:
                    agent_id = agent.get('id', 'unknown')
                    agent_name = agent.get('name', 'Unnamed Agent')
                    print(f"  - {agent_name} ({agent_id})")
            else:
                print("No manufacturing agents found")
                
            self.agents_ready.emit(agents)
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error fetching manufacturing agents: {error_msg}")
            
            # Empty list on error
            self.agents_ready.emit([])
            
            # Emit error signal
            if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                self.error_occurred.emit("Could not fetch manufacturing agents. Please check your network connection.")
            else:
                self.error_occurred.emit(f"Error fetching manufacturing agents: {error_msg}")
                
            # Provide fallback agents if needed
            # This could be implemented in the future

class AnalyzeCADThread(QtCore.QThread):
    """Thread for analyzing CAD document"""
    
    analysis_ready = QtCore.Signal(dict)
    
    def __init__(self, cad_analyzer):
        super().__init__()
        self.cad_analyzer = cad_analyzer
    
    def run(self):
        """Run the thread"""
        try:
            # Try to get active document
            import FreeCAD
            if FreeCAD.ActiveDocument is None:
                self.analysis_ready.emit({"error": "No active document. Please open a CAD file first."})
                return
            
            # Run analysis
            analysis = self.cad_analyzer.analyze_document(FreeCAD.ActiveDocument)
            
            # Add timestamp
            analysis["timestamp"] = datetime.now().isoformat()
            
            self.analysis_ready.emit(analysis)
        except Exception as e:
            self.analysis_ready.emit({"error": str(e)})


class EngineeringAnalysisThread(QtCore.QThread):
    """Thread for running engineering analysis on CAD document"""
    
    analysis_ready = QtCore.Signal(dict)
    
    def __init__(self):
        super().__init__()
    
    def run(self):
        """Run the thread"""
        try:
            # Try to get active document
            import FreeCAD
            if FreeCAD.ActiveDocument is None:
                self.analysis_ready.emit({"error": "No active document. Please open a CAD file first."})
                return
            
            # Import the cloud analyzer which contains the engineering analysis functionality
            try:
                import cloud_cad_analyzer
            except ImportError:
                import cloud_cad_analyzer
                
            # Get the analyzer and run engineering analysis only
            analyzer = cloud_cad_analyzer.get_analyzer()
            analysis = analyzer.analyze_engineering_only(FreeCAD.ActiveDocument)
            
            # Add timestamp
            analysis["timestamp"] = datetime.now().isoformat()
            
            self.analysis_ready.emit(analysis)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.analysis_ready.emit({"error": str(e)})

class CloudConnectionThread(QtCore.QThread):
    """Thread for checking cloud connection"""
    
    status_ready = QtCore.Signal(bool)
    error_message = QtCore.Signal(str)
    
    def __init__(self, cloud_client):
        super().__init__()
        self.cloud_client = cloud_client
    
    def run(self):
        """Run the thread"""
        try:
            print("Checking cloud connection...")
            if self.cloud_client:
                connected = self.cloud_client.test_connection()
                if connected:
                    print("Cloud connection successful")
                else:
                    print("Cloud connection failed - service unreachable")
            else:
                print("Cloud connection failed - no client available")
                connected = False
            self.status_ready.emit(connected)
        except Exception as e:
            error_msg = str(e)
            print(f"Cloud connection error: {error_msg}")
            self.status_ready.emit(False)
            
            # Emit detailed error message
            if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                self.error_message.emit("Could not connect to cloud services. Please check your network connection.")
            elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                self.error_message.emit("Authentication error. Please check your API keys in the configuration.")
            else:
                self.error_message.emit(f"Cloud connection error: {error_msg}")

# Global reference to the chat interface instance
_chat_interface_instance = None

def register_interface(interface_instance):
    """Register a chat interface instance for global access"""
    global _chat_interface_instance
    _chat_interface_instance = interface_instance

def get_interface():
    """Get the registered chat interface instance"""
    return _chat_interface_instance

# Flag to prevent multiple instances from being created
_INTERFACE_CREATION_IN_PROGRESS = False

def show_chat_interface():
    """Show the chat interface with robust singleton enforcement"""
    global _INTERFACE_CREATION_IN_PROGRESS
    
    print("\n=== STARTING MANUFACTURING CO-PILOT UI ===\n")
    
    # CRITICAL: First check if we're already creating an interface
    if _INTERFACE_CREATION_IN_PROGRESS:
        print("WARNING: Interface creation already in progress, preventing duplicate instance")
        QtWidgets.QMessageBox.information(
            None,
            "Co-Pilot Starting",
            "Manufacturing Co-Pilot is already starting. Please wait..."
        )
        return None
    
    # Set the flag to prevent multiple instances
    _INTERFACE_CREATION_IN_PROGRESS = True
    
    try:
        # First, aggressively clean up any existing instances
        # This ensures we start with a clean slate
        ManufacturingChatInterface.cleanup_instances()
        
        # Check for any active FreeCAD task dialogs
        try:
            import FreeCADGui
            if FreeCADGui.Control.activeDialog():
                print("Closing any active FreeCAD task dialog")
                FreeCADGui.Control.closeDialog()
        except Exception as e:
            print(f"Error checking FreeCAD task dialogs: {e}")
        
        # Create application if needed
        if QtWidgets.QApplication.instance() is None:
            app = QtWidgets.QApplication(sys.argv)
        else:
            app = QtWidgets.QApplication.instance()
        
        # Double-check for existing interface instance
        existing_interface = get_interface()
        if existing_interface is not None:
            try:
                # If we have an existing instance, bring it to front
                existing_interface.activateWindow()
                existing_interface.raise_()
                print("Using existing Manufacturing Co-Pilot interface")
                _INTERFACE_CREATION_IN_PROGRESS = False
                return existing_interface
            except Exception as e:
                print(f"Error accessing existing interface: {e}")
                # Continue with creating a new instance
        
        # Create and show the chat interface
        print("Creating new Manufacturing Co-Pilot interface")
        chat_interface = ManufacturingChatInterface()
        
        # Register the interface for global access BEFORE showing it
        # This ensures it's available if needed during show()
        register_interface(chat_interface)
        
        # Now show the interface
        chat_interface.show()
        print("Manufacturing Co-Pilot interface shown")
        
        # Set global flag in main module if possible
        try:
            import sys
            for module_name in ['__main__', 'ImprovedCoPilot']:
                if module_name in sys.modules:
                    module = sys.modules[module_name]
                    if hasattr(module, '_COPILOT_RUNNING'):
                        print(f"Setting global _COPILOT_RUNNING flag in {module_name}")
                        setattr(module, '_COPILOT_RUNNING', True)
        except Exception as flag_err:
            print(f"Error setting global flag: {flag_err}")
        
        # Reset creation flag and return the interface
        _INTERFACE_CREATION_IN_PROGRESS = False
        print("\n=== MANUFACTURING CO-PILOT UI STARTED SUCCESSFULLY ===\n")
        return chat_interface
        
    except Exception as e:
        print(f"ERROR creating chat interface: {e}")
        import traceback
        traceback.print_exc()
        
        # Reset creation flag
        _INTERFACE_CREATION_IN_PROGRESS = False
        
        # Show error to user
        try:
            QtWidgets.QMessageBox.critical(
                None,
                "Co-Pilot Error",
                f"Failed to start Manufacturing Co-Pilot:\n\n{str(e)}"
            )
        except Exception:
            pass
            
        return None
