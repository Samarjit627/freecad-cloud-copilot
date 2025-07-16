"""
FreeCAD Manufacturing Co-Pilot Cloud Backend
FastAPI server that handles AI processing for the FreeCAD Manufacturing Co-Pilot
"""

import os
import logging
from datetime import datetime

# Import the FastAPI app from our modular structure
from app.main import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# This file serves as the entry point for the application
# The actual FastAPI app is defined in app/main.py

# Main entry point for gunicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
