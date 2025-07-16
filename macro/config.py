"""
Configuration for the FreeCAD Manufacturing Co-Pilot
"""

import os
from pathlib import Path

# API Configuration
CLOUD_API_URL = "https://freecad-copilot-service-501520737043.asia-south1.run.app"  # Cloud Run service URL
CLOUD_API_KEY = ""  # Set this to your API key

# OpenAI Configuration (fallback for local processing)
OPENAI_API_KEY = ""
OPENAI_MODEL = "gpt-4o-mini"

# UI Configuration
UI_THEME = "modern"  # Options: "modern", "light", "dark"
UI_FONT_SIZE = 13
UI_CHAT_WIDTH = 800
UI_ANALYSIS_WIDTH = 400

# Feature Flags
USE_CLOUD_BACKEND = True  # Set to False to use local processing only
ENABLE_AUTO_ANALYSIS = True
ENABLE_DEBUG_MODE = False

# Load from environment if available
if os.environ.get("FREECAD_COPILOT_API_URL"):
    CLOUD_API_URL = os.environ.get("FREECAD_COPILOT_API_URL")

if os.environ.get("FREECAD_COPILOT_API_KEY"):
    CLOUD_API_KEY = os.environ.get("FREECAD_COPILOT_API_KEY")

if os.environ.get("OPENAI_API_KEY"):
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Try to load from config file if it exists
config_path = Path.home() / ".freecad" / "copilot_config.py"
if config_path.exists():
    try:
        with open(config_path, "r") as f:
            exec(f.read())
    except Exception as e:
        print(f"Error loading config file: {e}")
