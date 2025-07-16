#!/usr/bin/env python3
"""
Test script to verify the chat_interface.py module loads correctly
"""

import sys
import os

# Add the parent directory to the path so we can import the macro modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Attempting to import chat_interface module...")
    from macro import chat_interface
    print("✅ Successfully imported chat_interface module!")
    print("Module structure looks good.")
except Exception as e:
    print(f"❌ Error importing chat_interface module: {e}")
    import traceback
    traceback.print_exc()
    
print("\nTest complete.")
