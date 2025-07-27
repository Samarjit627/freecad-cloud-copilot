#!/bin/bash
# Run script for the FreeCAD Manufacturing Co-Pilot Unified Server

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment if it exists
echo "Activating virtual environment..."
source ../venv_py312/bin/activate || true

# Install dependencies with specific versions to avoid compatibility issues
echo "Installing dependencies..."
pip install fastapi==0.95.2 uvicorn==0.22.0 pydantic==1.10.8
pip install python-dotenv requests

# Create .env file from template if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.template .env
    echo "Please edit .env file to add your API keys"
fi

# Create necessary directories
mkdir -p services/__pycache__
mkdir -p routers/__pycache__

# Run the server
echo "Starting unified server..."
# Get port from environment variable or use default
port=${PORT:-8081}
python3 -m uvicorn main:app --host 0.0.0.0 --port $port --reload
