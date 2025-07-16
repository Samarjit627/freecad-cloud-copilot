"""
Singleton Controller for Manufacturing Co-Pilot
This module provides a singleton controller to prevent multiple instances of the Co-Pilot UI
"""

import os
import sys
import traceback
from pathlib import Path

class SingletonController:
    """
    Singleton controller to prevent multiple instances of the Manufacturing Co-Pilot
    """
    # Class-level variables to track state
    _instance = None
    _is_running = False
    _active_panel = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance"""
        if cls._instance is None:
            cls._instance = SingletonController()
        return cls._instance
    
    @classmethod
    def is_running(cls):
        """Check if the Co-Pilot is already running"""
        return cls._is_running
    
    @classmethod
    def set_running(cls, state):
        """Set the running state"""
        cls._is_running = state
    
    @classmethod
    def register_panel(cls, panel):
        """Register an active panel"""
        cls._active_panel = panel
    
    @classmethod
    def get_active_panel(cls):
        """Get the active panel"""
        return cls._active_panel
    
    @classmethod
    def clear_panel(cls):
        """Clear the active panel reference"""
        cls._active_panel = None
        cls._is_running = False
    
    def __init__(self):
        """Initialize the controller"""
        # This should only be called once
        if SingletonController._instance is not None:
            raise RuntimeError("Singleton controller already initialized")
        
        # Store reference to self
        SingletonController._instance = self
    
    def start_copilot(self, macro_class):
        """
        Start the Co-Pilot if it's not already running
        
        Args:
            macro_class: The macro class to instantiate
        
        Returns:
            bool: True if started, False if already running
        """
        if SingletonController.is_running():
            print("Manufacturing Co-Pilot is already running!")
            try:
                # Try to bring the existing instance to front
                from PySide2 import QtWidgets
                QtWidgets.QMessageBox.information(
                    None,
                    "Co-Pilot Already Running",
                    "Manufacturing Co-Pilot is already running. Please use the existing instance."
                )
                
                # Try to activate the existing panel
                panel = SingletonController.get_active_panel()
                if panel and hasattr(panel, 'widget'):
                    try:
                        panel.widget.activateWindow()
                        panel.widget.raise_()
                    except Exception as e:
                        print(f"Error activating existing panel: {e}")
            except Exception as e:
                print(f"Error showing message: {e}")
            return False
        
        # Set running state to True
        SingletonController.set_running(True)
        
        try:
            # Create and run the macro
            instance = macro_class()
            return True
        except Exception as e:
            print(f"Error starting Co-Pilot: {e}")
            traceback.print_exc()
            SingletonController.set_running(False)
            return False
