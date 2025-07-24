#!/bin/bash
# Run the Text-to-CAD agent locally

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
export FLASK_APP=main.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=8070
