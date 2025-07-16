"""
UI Components for the FreeCAD Manufacturing Co-Pilot
Reusable UI components for the chat interface
Includes support for multi-agent system integration
"""

from PySide2 import QtWidgets, QtCore, QtGui
from typing import Dict, Any, List, Optional, Callable

# Import local modules
try:
    import config
except ImportError:
    import config

class ChatMessageWidget(QtWidgets.QWidget):
    """Widget for displaying a chat message"""
    
    def __init__(self, role: str, content: str, parent=None):
        super().__init__(parent)
        self.role = role
        self.content = content
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI for the chat message"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Role indicator
        role_layout = QtWidgets.QHBoxLayout()
        role_layout.setContentsMargins(0, 0, 0, 0)
        
        if self.role == "User":
            avatar_label = QtWidgets.QLabel("👤")
            role_label = QtWidgets.QLabel("You")
            self.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                }
            """)
        else:
            avatar_label = QtWidgets.QLabel("🚀")
            role_label = QtWidgets.QLabel("Manufacturing Co-Pilot")
            self.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                }
            """)
        
        avatar_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #4b5563;
                background: transparent;
            }
        """)
        
        role_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #4b5563;
                background: transparent;
            }
        """)
        
        role_layout.addWidget(avatar_label)
        role_layout.addWidget(role_label)
        role_layout.addStretch()
        
        # Content
        content_widget = QtWidgets.QFrame()
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        
        # Use QTextBrowser for rich text support
        content_browser = QtWidgets.QTextBrowser()
        content_browser.setOpenExternalLinks(True)
        content_browser.setHtml(self.format_markdown(self.content))
        content_browser.setFrameShape(QtWidgets.QFrame.NoFrame)
        content_browser.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        content_browser.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        content_browser.setMinimumHeight(50)
        content_browser.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        content_browser.document().setDocumentMargin(0)
        
        # Set height based on content
        document_height = content_browser.document().size().height()
        content_browser.setMinimumHeight(min(300, int(document_height + 10)))
        
        if self.role == "User":
            content_widget.setStyleSheet("""
                QFrame {
                    background-color: #f3f4f6;
                    border-radius: 12px;
                    padding: 8px;
                }
                QTextBrowser {
                    background-color: transparent;
                    color: #000000;
                    font-size: 14px;
                    selection-background-color: #d1d5db;
                }
            """)
        else:
            content_widget.setStyleSheet("""
                QFrame {
                    background-color: #eef2ff;
                    border-radius: 12px;
                    padding: 8px;
                }
                QTextBrowser {
                    background-color: transparent;
                    color: #000000;
                    font-size: 14px;
                    font-weight: 500;
                    selection-background-color: #c7d2fe;
                }
            """)
            
        # Force text color to be black
        content_browser.setStyleSheet("color: #000000; background-color: transparent;")
        content_browser.document().setDefaultStyleSheet("body { color: #000000; }")

        
        content_layout.addWidget(content_browser)
        
        # Add to main layout
        layout.addLayout(role_layout)
        layout.addWidget(content_widget)
    
    def format_markdown(self, text: str) -> str:
        """Format markdown text to HTML"""
        # Basic markdown formatting
        html = text
        
        # Bold
        html = html.replace("**", "<b>", 1)
        while "**" in html:
            html = html.replace("**", "</b>", 1)
            if "**" in html:
                html = html.replace("**", "<b>", 1)
        
        # Italic
        html = html.replace("*", "<i>", 1)
        while "*" in html:
            html = html.replace("*", "</i>", 1)
            if "*" in html:
                html = html.replace("*", "<i>", 1)
        
        # Code blocks
        html = html.replace("```", "<pre><code>", 1)
        while "```" in html:
            html = html.replace("```", "</code></pre>", 1)
            if "```" in html:
                html = html.replace("```", "<pre><code>", 1)
        
        # Inline code
        html = html.replace("`", "<code>", 1)
        while "`" in html:
            html = html.replace("`", "</code>", 1)
            if "`" in html:
                html = html.replace("`", "<code>", 1)
        
        # Lists
        lines = html.split("\n")
        in_list = False
        for i, line in enumerate(lines):
            if line.strip().startswith("• "):
                if not in_list:
                    lines[i] = "<ul><li>" + line.strip()[2:] + "</li>"
                    in_list = True
                else:
                    lines[i] = "<li>" + line.strip()[2:] + "</li>"
            elif line.strip().startswith("- "):
                if not in_list:
                    lines[i] = "<ul><li>" + line.strip()[2:] + "</li>"
                    in_list = True
                else:
                    lines[i] = "<li>" + line.strip()[2:] + "</li>"
            elif in_list and not line.strip().startswith(("• ", "- ")) and line.strip():
                lines[i-1] += "</ul>"
                in_list = False
        
        if in_list:
            lines[-1] += "</ul>"
        
        html = "\n".join(lines)
        
        # Replace newlines with <br>
        html = html.replace("\n", "<br>")
        
        return html

class AnalysisPanel(QtWidgets.QWidget):
    """Panel for displaying CAD analysis results"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analysis_data = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI for the analysis panel"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Header
        header = QtWidgets.QLabel("CAD Analysis")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #111827;
        """)
        layout.addWidget(header)
        
        # Scroll area for analysis content
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            background-color: white;
            border: none;
        """)
        
        # Content widget
        self.content_widget = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(15)
        
        # Add placeholder
        placeholder = QtWidgets.QLabel("No CAD analysis available.\nClick 'Analyze CAD' to begin.")
        placeholder.setAlignment(QtCore.Qt.AlignCenter)
        placeholder.setStyleSheet("""
            font-size: 14px;
            color: #6b7280;
            padding: 20px;
        """)
        self.content_layout.addWidget(placeholder)
        self.content_layout.addStretch()
        
        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)
        
        # Analyze button
        self.analyze_button = QtWidgets.QPushButton("🔍 Analyze CAD")
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background: #4f46e5;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #4338ca;
            }
            QPushButton:pressed {
                background: #3730a3;
            }
        """)
        layout.addWidget(self.analyze_button)
    
    def update_analysis(self, analysis_data: Dict[str, Any]):
        """Update the analysis panel with new data"""
        self.analysis_data = analysis_data
        
        # Clear existing content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not analysis_data:
            # Add placeholder
            placeholder = QtWidgets.QLabel("No CAD analysis available.\nClick 'Analyze CAD' to begin.")
            placeholder.setAlignment(QtCore.Qt.AlignCenter)
            placeholder.setStyleSheet("""
                font-size: 14px;
                color: #6b7280;
                padding: 20px;
            """)
            self.content_layout.addWidget(placeholder)
            self.content_layout.addStretch()
            return
        
        # Add document info
        doc_name = analysis_data.get("document_name", "Unknown Document")
        doc_info = QtWidgets.QLabel(f"📄 <b>{doc_name}</b>")
        doc_info.setTextFormat(QtCore.Qt.RichText)
        doc_info.setStyleSheet("""
            font-size: 16px;
            color: #111827;
            padding-bottom: 5px;
        """)
        self.content_layout.addWidget(doc_info)
        
        # Add dimensions
        dims = analysis_data.get("dimensions", {})
        if dims:
            dims_frame = QtWidgets.QFrame()
            dims_frame.setStyleSheet("""
                background-color: #f3f4f6;
                border-radius: 8px;
                padding: 10px;
            """)
            dims_layout = QtWidgets.QVBoxLayout(dims_frame)
            
            dims_header = QtWidgets.QLabel("📏 Dimensions")
            dims_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #111827;")
            dims_layout.addWidget(dims_header)
            
            dims_grid = QtWidgets.QGridLayout()
            dims_grid.addWidget(QtWidgets.QLabel("Length:"), 0, 0)
            dims_grid.addWidget(QtWidgets.QLabel(f"{dims.get('length', 0):.1f} mm"), 0, 1)
            dims_grid.addWidget(QtWidgets.QLabel("Width:"), 1, 0)
            dims_grid.addWidget(QtWidgets.QLabel(f"{dims.get('width', 0):.1f} mm"), 1, 1)
            dims_grid.addWidget(QtWidgets.QLabel("Height:"), 2, 0)
            dims_grid.addWidget(QtWidgets.QLabel(f"{dims.get('height', 0):.1f} mm"), 2, 1)
            dims_grid.addWidget(QtWidgets.QLabel("Thickness:"), 3, 0)
            dims_grid.addWidget(QtWidgets.QLabel(f"{dims.get('thickness', 0):.2f} mm"), 3, 1)
            
            dims_layout.addLayout(dims_grid)
            self.content_layout.addWidget(dims_frame)
        
        # Add manufacturing features
        features = analysis_data.get("manufacturing_features", {})
        if features:
            features_frame = QtWidgets.QFrame()
            features_frame.setStyleSheet("""
                background-color: #eef2ff;
                border-radius: 8px;
                padding: 10px;
            """)
            features_layout = QtWidgets.QVBoxLayout(features_frame)
            
            features_header = QtWidgets.QLabel("🔧 Manufacturing Features")
            features_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #111827;")
            features_layout.addWidget(features_header)
            
            features_grid = QtWidgets.QGridLayout()
            features_grid.addWidget(QtWidgets.QLabel("Holes:"), 0, 0)
            features_grid.addWidget(QtWidgets.QLabel(f"{features.get('holes', 0)}"), 0, 1)
            features_grid.addWidget(QtWidgets.QLabel("Ribs:"), 1, 0)
            features_grid.addWidget(QtWidgets.QLabel(f"{features.get('ribs', 0)}"), 1, 1)
            features_grid.addWidget(QtWidgets.QLabel("Fillets:"), 2, 0)
            features_grid.addWidget(QtWidgets.QLabel(f"{features.get('fillets', 0)}"), 2, 1)
            features_grid.addWidget(QtWidgets.QLabel("Complexity:"), 3, 0)
            features_grid.addWidget(QtWidgets.QLabel(f"{features.get('complexity_rating', 'Unknown')}"), 3, 1)
            
            features_layout.addLayout(features_grid)
            self.content_layout.addWidget(features_frame)
        
        # Add volume and surface area
        metrics_frame = QtWidgets.QFrame()
        metrics_frame.setStyleSheet("""
            background-color: #f0fdf4;
            border-radius: 8px;
            padding: 10px;
        """)
        metrics_layout = QtWidgets.QVBoxLayout(metrics_frame)
        
        metrics_header = QtWidgets.QLabel("📊 Metrics")
        metrics_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #111827;")
        metrics_layout.addWidget(metrics_header)
        
        metrics_grid = QtWidgets.QGridLayout()
        metrics_grid.addWidget(QtWidgets.QLabel("Volume:"), 0, 0)
        metrics_grid.addWidget(QtWidgets.QLabel(f"{analysis_data.get('volume', 0):.1f} cm³"), 0, 1)
        metrics_grid.addWidget(QtWidgets.QLabel("Surface Area:"), 1, 0)
        metrics_grid.addWidget(QtWidgets.QLabel(f"{analysis_data.get('surface_area', 0):.1f} cm²"), 1, 1)
        metrics_grid.addWidget(QtWidgets.QLabel("Object Count:"), 2, 0)
        metrics_grid.addWidget(QtWidgets.QLabel(f"{analysis_data.get('object_count', 0)}"), 2, 1)
        
        metrics_layout.addLayout(metrics_grid)
        self.content_layout.addWidget(metrics_frame)
        
        # Add cloud-enhanced data if available
        if features.get("cloud_enhanced_score") is not None:
            cloud_frame = QtWidgets.QFrame()
            cloud_frame.setStyleSheet("""
                background-color: #eff6ff;
                border-radius: 8px;
                padding: 10px;
            """)
            cloud_layout = QtWidgets.QVBoxLayout(cloud_frame)
            
            cloud_header = QtWidgets.QLabel("☁️ Cloud-Enhanced Analysis")
            cloud_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #111827;")
            cloud_layout.addWidget(cloud_header)
            
            cloud_grid = QtWidgets.QGridLayout()
            cloud_grid.addWidget(QtWidgets.QLabel("Enhanced Score:"), 0, 0)
            cloud_grid.addWidget(QtWidgets.QLabel(f"{features.get('cloud_enhanced_score', 0):.1f}/10"), 0, 1)
            
            # Add supplier recommendations if available
            suppliers = features.get("supplier_recommendations", [])
            if suppliers:
                cloud_grid.addWidget(QtWidgets.QLabel("Recommended Suppliers:"), 1, 0, 1, 2)
                
                for i, supplier in enumerate(suppliers[:3], 2):
                    cloud_grid.addWidget(QtWidgets.QLabel(f"• {supplier.get('name', 'Unknown')}"), i, 0)
                    cloud_grid.addWidget(QtWidgets.QLabel(f"{supplier.get('location', 'Unknown')}"), i, 1)
            
            cloud_layout.addLayout(cloud_grid)
            self.content_layout.addWidget(cloud_frame)
        
        # Add timestamp
        timestamp = analysis_data.get("timestamp", "")
        if timestamp:
            try:
                # Format timestamp
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                
                time_label = QtWidgets.QLabel(f"Last analyzed: {formatted_time}")
                time_label.setStyleSheet("""
                    font-size: 12px;
                    color: #6b7280;
                    padding-top: 5px;
                """)
                self.content_layout.addWidget(time_label)
            except:
                pass
        
        # Add stretch to push everything to the top
        self.content_layout.addStretch()

class CloudStatusWidget(QtWidgets.QWidget):
    """Widget for displaying cloud connection status"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.connected = False
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI for the cloud status widget"""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        
        self.status_icon = QtWidgets.QLabel("⚫")
        self.status_text = QtWidgets.QLabel("Cloud: Disconnected")
        
        layout.addWidget(self.status_icon)
        layout.addWidget(self.status_text)
        layout.addStretch()
        
        self.update_status(False)
    
    def update_status(self, connected: bool):
        """Update the cloud connection status"""
        self.connected = connected
        
        if connected:
            self.status_icon.setText("🟢")
            self.status_text.setText("Cloud: Connected")
            self.status_text.setStyleSheet("color: #10b981;")
        else:
            self.status_icon.setText("🔴")
            self.status_text.setText("Cloud: Disconnected")
            self.status_text.setStyleSheet("color: #ef4444;")

class AgentButton(QtWidgets.QPushButton):
    """Button for selecting a manufacturing agent"""
    
    def __init__(self, agent_id: str, name: str, description: str):
        # Add agent icon based on agent_id
        icon_map = {
            "dfm_expert": "🛠️",
            "cost_estimator": "💰",
            "process_planner": "🔧",
            "material_selector": "🧪",
        }
        icon = icon_map.get(agent_id, "🤖")
        super().__init__(f"{icon} {name}")
        
        self.agent_id = agent_id
        self.description = description
        self.is_loading = False
        
        # Set tooltip with description
        self.setToolTip(description)
        
        # Set fixed height
        self.setFixedHeight(36)
        
        # Style
        self.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #4b5563;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 12px;
                text-align: left;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
            QPushButton:checked {
                background-color: #e0e7ff;
                border: 1px solid #6366f1;
                color: #4f46e5;
            }
            QPushButton:disabled {
                background-color: #f9fafb;
                color: #9ca3af;
                border: 1px solid #e5e7eb;
            }
        """)
        
        # Make checkable
        self.setCheckable(True)
    
    def set_loading(self, is_loading: bool):
        """Set the loading state of the button"""
        self.is_loading = is_loading
        self.setEnabled(not is_loading)
        
        # Store original text if entering loading state
        if is_loading and not hasattr(self, '_original_text'):
            self._original_text = self.text()
            self.setText(f"⏳ {self._original_text.split(' ', 1)[1]}")
        # Restore original text if exiting loading state
        elif not is_loading and hasattr(self, '_original_text'):
            self.setText(self._original_text)
            delattr(self, '_original_text')


class AgentPanel(QtWidgets.QWidget):
    """Panel for interacting with specialized manufacturing agents"""
    
    agent_selected = QtCore.Signal(str)  # Signal emitted when agent is selected
    orchestrate_agents = QtCore.Signal(list)  # Signal emitted when orchestration is requested
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # State
        self.agents = []
        self.agent_buttons = {}
        self.selected_agents = set()
        self.is_processing = False
        
        # Setup UI
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI for the agent panel"""
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Header
        header_label = QtWidgets.QLabel("🤖 Manufacturing Agents")
        header_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #111827;
        """)
        main_layout.addWidget(header_label)
        
        # Description
        description_label = QtWidgets.QLabel(
            "Select specialized manufacturing agents to answer specific questions"
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        main_layout.addWidget(description_label)
        
        # Agents container
        self.agents_container = QtWidgets.QWidget()
        self.agents_layout = QtWidgets.QVBoxLayout(self.agents_container)
        self.agents_layout.setContentsMargins(0, 0, 0, 0)
        self.agents_layout.setSpacing(6)
        
        # Placeholder for when no agents are available
        self.placeholder_label = QtWidgets.QLabel(
            "Loading manufacturing agents..."
        )
        self.placeholder_label.setStyleSheet("""
            color: #6b7280;
            font-style: italic;
            padding: 10px 0;
        """)
        self.agents_layout.addWidget(self.placeholder_label)
        
        # Add agents container to main layout
        main_layout.addWidget(self.agents_container)
        
        # Orchestrate button
        self.orchestrate_button = QtWidgets.QPushButton("🔄 Orchestrate Selected Agents")
        self.orchestrate_button.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #4338ca;
            }
            QPushButton:pressed {
                background-color: #3730a3;
            }
            QPushButton:disabled {
                background-color: #c7d2fe;
                color: #6366f1;
            }
        """)
        self.orchestrate_button.setEnabled(False)
        self.orchestrate_button.clicked.connect(self.on_orchestrate_clicked)
        main_layout.addWidget(self.orchestrate_button)
        
        # Add stretch to push everything to the top
        main_layout.addStretch()
    
    def update_agents(self, agents: List[Dict[str, Any]]):
        """Update the list of available agents"""
        # Clear existing agents
        self.clear_agents()
        
        # Store agents
        self.agents = agents
        
        # Remove placeholder if agents are available
        if agents:
            self.placeholder_label.setVisible(False)
        else:
            self.placeholder_label.setText("No manufacturing agents available")
            self.placeholder_label.setVisible(True)
            return
        
        # Add agent buttons
        for agent in agents:
            agent_id = agent.get("id", "")
            name = agent.get("name", "Unknown Agent")
            description = agent.get("description", "")
            
            # Create button
            button = AgentButton(agent_id, name, description)
            button.clicked.connect(self.on_agent_button_clicked)
            
            # Add to layout
            self.agents_layout.addWidget(button)
            
            # Store button reference
            self.agent_buttons[agent_id] = button
    
    def clear_agents(self):
        """Clear all agent buttons"""
        # Clear selected agents
        self.selected_agents.clear()
        
        # Remove all agent buttons
        for button in self.agent_buttons.values():
            self.agents_layout.removeWidget(button)
            button.deleteLater()
        
        # Clear button references
        self.agent_buttons = {}
        
        # Update orchestrate button
        self.update_orchestrate_button()
    
    def on_agent_button_clicked(self):
        """Handle agent button click"""
        # Get sender button
        button = self.sender()
        if not isinstance(button, AgentButton):
            return
        
        # Toggle selection
        if button.isChecked():
            self.selected_agents.add(button.agent_id)
            # Emit signal for single agent selection
            if len(self.selected_agents) == 1:
                self.agent_selected.emit(button.agent_id)
        else:
            self.selected_agents.remove(button.agent_id)
        
        # Update orchestrate button
        self.update_orchestrate_button()
    
    def update_orchestrate_button(self):
        """Update the state of the orchestrate button"""
        # Enable if multiple agents are selected and not processing
        self.orchestrate_button.setEnabled(len(self.selected_agents) > 1 and not self.is_processing)
        
        # Update text
        if len(self.selected_agents) > 1:
            self.orchestrate_button.setText(f"🔄 Orchestrate {len(self.selected_agents)} Agents")
        else:
            self.orchestrate_button.setText("🔄 Orchestrate Selected Agents")
            
    def set_processing(self, is_processing: bool):
        """Set the processing state of the panel"""
        self.is_processing = is_processing
        
        # Update button states
        for button in self.agent_buttons.values():
            button.setEnabled(not is_processing)
        
        # Update orchestrate button
        self.update_orchestrate_button()
        
        # Update placeholder text if needed
        if is_processing and self.placeholder_label.isVisible():
            self.placeholder_label.setText("Processing query...")
        elif not is_processing and self.placeholder_label.isVisible() and not self.agents:
            self.placeholder_label.setText("No manufacturing agents available")
            
    def set_agent_loading(self, agent_id: str, is_loading: bool):
        """Set the loading state for a specific agent"""
        if agent_id in self.agent_buttons:
            self.agent_buttons[agent_id].set_loading(is_loading)
    
    def on_orchestrate_clicked(self):
        """Handle orchestrate button click"""
        # Emit signal with selected agent IDs
        self.orchestrate_agents.emit(list(self.selected_agents))
    
    def reset_selection(self):
        """Reset agent selection"""
        # Uncheck all buttons
        for button in self.agent_buttons.values():
            button.setChecked(False)
        
        # Clear selected agents
        self.selected_agents.clear()
        
        # Update orchestrate button
        self.update_orchestrate_button()


class ModeSelectorWidget(QtWidgets.QWidget):
    """Widget for selecting chat mode"""
    
    mode_changed = QtCore.Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mode = "general"
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI for the mode selector widget"""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Mode label
        mode_label = QtWidgets.QLabel("Mode:")
        mode_label.setStyleSheet("color: #4b5563;")
        layout.addWidget(mode_label)
        
        # Mode combo box
        self.mode_combo = QtWidgets.QComboBox()
        self.mode_combo.addItem("💬 General Advice", "general")
        self.mode_combo.addItem("🔧 Design for Manufacturing", "dfm")
        self.mode_combo.addItem("💰 Cost Analysis", "cost")
        self.mode_combo.addItem("⚙️ Process Selection", "process")
        self.mode_combo.addItem("🤖 Manufacturing Agents", "agents")
        
        self.mode_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 5px 10px;
                min-width: 180px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border: 5px solid transparent;
                border-top: 5px solid #6b7280;
                width: 0;
                height: 0;
            }
        """)
        
        layout.addWidget(self.mode_combo)
        layout.addStretch()
        
        # Connect signal
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
    
    def get_current_mode(self) -> str:
        """Get the current selected mode"""
        return self.mode_combo.currentData()
    
    def set_mode(self, mode: str):
        """Set the current mode"""
        index = self.mode_combo.findData(mode)
        if index >= 0:
            self.mode_combo.setCurrentIndex(index)
            
    def _on_mode_changed(self, index):
        """Handle mode change"""
        mode = self.mode_combo.itemData(index)
        self.mode_changed.emit(mode)
