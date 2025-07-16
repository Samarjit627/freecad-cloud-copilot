#!/usr/bin/env python3
"""
Launcher script for the FreeCAD Manufacturing Co-Pilot
This script launches the Manufacturing Co-Pilot chat interface
"""

import sys
import os
from pathlib import Path

# Add macro directory to path
SCRIPT_DIR = Path(__file__).parent
MACRO_DIR = SCRIPT_DIR / "macro"
sys.path.append(str(MACRO_DIR))

# Try to import FreeCAD
try:
    import FreeCAD
    INSIDE_FREECAD = True
except ImportError:
    INSIDE_FREECAD = False
    print("⚠️ FreeCAD module not found. Running in standalone mode.")

# Import required modules
from macro import chat_interface

def main():
    """Main function"""
    print("🚀 Launching FreeCAD Manufacturing Co-Pilot...")
    
    # Show the chat interface
    app = chat_interface.show_chat_interface()
    
    # If not running inside FreeCAD, start the Qt event loop
    if not INSIDE_FREECAD:
        print("Running in standalone mode (limited functionality)")
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
