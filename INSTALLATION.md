# Installation Guide for FreeCAD Manufacturing Co-Pilot

This guide will help you install and configure the FreeCAD Manufacturing Co-Pilot with multi-agent system integration.

## Prerequisites

1. FreeCAD 0.19 or later
2. Python 3.6 or later
3. PySide2 (included with FreeCAD)

## Installation Steps

### 1. Clone or Download the Repository

```bash
git clone https://github.com/your-username/freecad-cloud-copilot.git
# or download and extract the ZIP file
```

### 2. Configure API Keys

1. Open the `macro/config.py` file
2. Set your API keys and configuration:

```python
# Cloud backend configuration
USE_CLOUD_BACKEND = True  # Set to False for offline mode
CLOUD_API_URL = "https://your-cloud-backend.com/api"
CLOUD_API_KEY = "your-api-key"

# OpenAI configuration (for fallback when cloud is unavailable)
OPENAI_API_KEY = "your-openai-api-key"  # Optional
```

### 3. Install Required Python Packages

If running outside of FreeCAD, you'll need to install the required packages:

```bash
pip install PySide2 openai requests
```

### 4. Install as FreeCAD Macro

#### Option 1: Copy to Macro Directory

1. Find your FreeCAD Macro directory:
   - In FreeCAD, go to `Edit > Preferences > General > Macro`
   - Note the "Macro path"

2. Copy the entire `macro` directory to your FreeCAD Macro directory

3. Copy the `ManufacturingCoPilot.FCMacro` file to your FreeCAD Macro directory

#### Option 2: Create a Symlink

```bash
# On Linux/macOS
ln -s /path/to/freecad-cloud-copilot/ManufacturingCoPilot.FCMacro ~/.FreeCAD/Macro/

# On Windows (run as administrator)
mklink "C:\Users\YOUR_USERNAME\AppData\Roaming\FreeCAD\Macro\ManufacturingCoPilot.FCMacro" "C:\path\to\freecad-cloud-copilot\ManufacturingCoPilot.FCMacro"
```

## Running the Co-Pilot

### Within FreeCAD

1. Open FreeCAD
2. Go to `Macro > Macros...`
3. Select `ManufacturingCoPilot.FCMacro`
4. Click `Execute`

### Standalone Mode (Limited Functionality)

For development and testing purposes, you can run the co-pilot outside of FreeCAD:

```bash
python launch_copilot.py
```

Note: In standalone mode, CAD analysis features will not be available.

## Troubleshooting

### Cloud Connection Issues

If you're having trouble connecting to the cloud backend:

1. Check your internet connection
2. Verify your API key is correct
3. Try running in offline mode by setting `USE_CLOUD_BACKEND = False` in `config.py`

### Missing Dependencies

If you encounter missing dependencies when running outside of FreeCAD:

```bash
pip install -r requirements.txt
```

### FreeCAD Integration Issues

If the macro doesn't appear in FreeCAD's macro list:

1. Ensure the `.FCMacro` file is in the correct directory
2. Restart FreeCAD
3. Check the FreeCAD console for error messages
