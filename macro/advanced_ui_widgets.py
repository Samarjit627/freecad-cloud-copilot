"""
Advanced UI widgets for context and suggestions
"""

from PySide2 import QtWidgets, QtCore
import FreeCAD
import FreeCADGui

class ContextWidget(QtWidgets.QWidget):
    """Widget showing current design context"""
    
    def __init__(self, context_manager, parent=None):
        super().__init__(parent)
        self.context = context_manager
        self.setup_ui()
        
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Title
        title = QtWidgets.QLabel("Design Context")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Context info
        self.info_text = QtWidgets.QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(100)
        layout.addWidget(self.info_text)
        
        # Update button
        update_btn = QtWidgets.QPushButton("Update Context")
        update_btn.clicked.connect(self.update_display)
        layout.addWidget(update_btn)
        
        # Initial update
        self.update_display()
        
    def update_display(self):
        """Update context display"""
        info = f"Project: {self.context.current_project or 'None'}\n"
        info += f"Parts Created: {len(self.context.parts_created)}\n"
        info += f"Material: {self.context.material or 'Not selected'}\n"
        info += f"Process: {self.context.process or 'Not selected'}\n"
        
        if self.context.assembly_components:
            info += f"Assembly: {len(self.context.assembly_components)} components\n"
        
        self.info_text.setText(info)


class SuggestionsWidget(QtWidgets.QWidget):
    """Widget for intelligent suggestions"""
    
    def __init__(self, nl_editor, parent=None):
        super().__init__(parent)
        self.nl_editor = nl_editor
        self.setup_ui()
        
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Title
        title = QtWidgets.QLabel("AI Suggestions")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Suggestions list
        self.suggestions_list = QtWidgets.QListWidget()
        self.suggestions_list.itemClicked.connect(self.execute_suggestion)
        layout.addWidget(self.suggestions_list)
        
        # Refresh button
        refresh_btn = QtWidgets.QPushButton("Get Suggestions")
        refresh_btn.clicked.connect(self.refresh_suggestions)
        layout.addWidget(refresh_btn)
        
        # Analysis button
        analyze_btn = QtWidgets.QPushButton("Analyze Design")
        analyze_btn.clicked.connect(self.analyze_design)
        layout.addWidget(analyze_btn)
        
    def refresh_suggestions(self):
        """Get new suggestions"""
        suggestions = self.nl_editor.context.suggest_next_steps()
        
        self.suggestions_list.clear()
        for suggestion in suggestions:
            self.suggestions_list.addItem(suggestion)
            
    def execute_suggestion(self, item):
        """Execute clicked suggestion"""
        command = item.text()
        result = self.nl_editor.process_command(command.lower())
        
        # Show result
        msg = QtWidgets.QMessageBox()
        if result['success']:
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText(result['message'])
        else:
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText(result['message'])
        msg.exec_()
        
    def analyze_design(self):
        """Run design analysis"""
        result = self.nl_editor.handle_analyze("")
        
        # Show analysis in dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Design Analysis")
        dialog.setMinimumWidth(400)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        text = QtWidgets.QTextEdit()
        text.setReadOnly(True)
        text.setText(result['message'])
        layout.addWidget(text)
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()


class NLCommandWidget(QtWidgets.QWidget):
    """Widget for natural language command input"""
    
    def __init__(self, nl_editor, parent=None):
        super().__init__(parent)
        self.nl_editor = nl_editor
        self.setup_ui()
        
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Title
        title = QtWidgets.QLabel("Natural Language CAD Commands")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Command input
        input_layout = QtWidgets.QHBoxLayout()
        
        self.command_input = QtWidgets.QLineEdit()
        self.command_input.setPlaceholderText("Enter a CAD command...")
        self.command_input.returnPressed.connect(self.execute_command)
        input_layout.addWidget(self.command_input)
        
        execute_btn = QtWidgets.QPushButton("Execute")
        execute_btn.clicked.connect(self.execute_command)
        input_layout.addWidget(execute_btn)
        
        layout.addLayout(input_layout)
        
        # Command history
        history_group = QtWidgets.QGroupBox("Recent Commands")
        history_layout = QtWidgets.QVBoxLayout()
        
        self.history_list = QtWidgets.QListWidget()
        self.history_list.itemClicked.connect(self.use_history_item)
        history_layout.addWidget(self.history_list)
        
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
    def execute_command(self):
        """Execute the current command"""
        command = self.command_input.text()
        if command:
            # Add to history
            self.history_list.insertItem(0, command)
            if self.history_list.count() > 10:
                self.history_list.takeItem(10)
            
            # Execute command
            result = self.nl_editor.process_command(command)
            
            # Clear input
            self.command_input.clear()
            
            # Show result in message box if needed
            if not result.get('success', False):
                QtWidgets.QMessageBox.warning(
                    self, "Command Error", result.get('message', "Unknown error")
                )
                
    def use_history_item(self, item):
        """Use a command from history"""
        self.command_input.setText(item.text())


class AssemblyWidget(QtWidgets.QWidget):
    """Widget for assembly creation"""
    
    def __init__(self, nl_editor, parent=None):
        super().__init__(parent)
        self.nl_editor = nl_editor
        self.setup_ui()
        
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Title
        title = QtWidgets.QLabel("Assembly Creator")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Assembly templates
        templates_group = QtWidgets.QGroupBox("Quick Assemblies")
        templates_layout = QtWidgets.QVBoxLayout()
        
        assemblies = [
            ("Gearbox 3:1", "create a gearbox with 3:1 reduction"),
            ("Linear Actuator", "create linear actuator 100mm stroke"),
            ("Motor Mount NEMA17", "create motor mount for NEMA17"),
            ("Pulley System", "create pulley system 2:1 ratio"),
            ("Lead Screw Assembly", "create lead screw assembly 200mm")
        ]
        
        for name, command in assemblies:
            btn = QtWidgets.QPushButton(name)
            btn.clicked.connect(lambda checked, cmd=command: self.create_assembly(cmd))
            templates_layout.addWidget(btn)
            
        templates_group.setLayout(templates_layout)
        layout.addWidget(templates_group)
        
        # Custom assembly
        custom_group = QtWidgets.QGroupBox("Custom Assembly")
        custom_layout = QtWidgets.QVBoxLayout()
        
        self.assembly_input = QtWidgets.QTextEdit()
        self.assembly_input.setPlaceholderText(
            "Describe your assembly:\n"
            "e.g., 'Create a gearbox with NEMA23 motor input "
            "and 5:1 reduction for a robot arm'"
        )
        self.assembly_input.setMaximumHeight(80)
        custom_layout.addWidget(self.assembly_input)
        
        create_btn = QtWidgets.QPushButton("Create Assembly")
        create_btn.clicked.connect(self.create_custom_assembly)
        custom_layout.addWidget(create_btn)
        
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)
        
    def create_assembly(self, command):
        """Create assembly from command"""
        result = self.nl_editor.process_command(command)
        self.show_result(result)
        
    def create_custom_assembly(self):
        """Create custom assembly"""
        text = self.assembly_input.toPlainText()
        if text:
            result = self.nl_editor.process_command(text)
            self.show_result(result)
            
    def show_result(self, result):
        """Show creation result"""
        msg = QtWidgets.QMessageBox()
        if result['success']:
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText(result['message'])
            
            if 'components' in result:
                msg.setDetailedText(f"Created {result['components']} components")
        else:
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText(result['message'])
        msg.exec_()
