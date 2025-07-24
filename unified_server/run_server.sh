#!/bin/bash
# Run script for the FreeCAD Manufacturing Co-Pilot Unified Server

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

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
python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --reload
