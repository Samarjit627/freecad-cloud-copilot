# Text-to-CAD Integration for FreeCAD Cloud Co-Pilot

This extension adds advanced Text-to-CAD capabilities to the FreeCAD Cloud Co-Pilot, allowing users to generate complex 3D models from natural language descriptions with engineering analysis.

## Features

- **Natural Language Model Generation**: Create CAD models by describing them in plain English
- **Engineering Analysis**: Receive detailed engineering analysis alongside your generated models
- **Specialized Part Types**: Support for specialized parts including:
  - Bicycles with customizable frame geometry
  - Water bottles with parametric dimensions
  - Gears with configurable teeth and modules
  - Brackets with mounting features
  - Generic parts with basic geometry

## Usage

1. Launch FreeCAD and run the `StandaloneCoPilot.FCMacro`
2. In the chat interface, enter a natural language description of the part you want to create:

Examples:
- "Create a mountain bike frame with 29-inch wheels and a 70-degree head tube angle"
- "Generate a 750ml water bottle with a standard neck diameter"
- "Design a gear with 24 teeth and module 2"
- "Make a mounting bracket with 4 holes"

3. The system will process your request through the cloud service and generate:
   - FreeCAD Python code for the model
   - Engineering analysis of the design
   - The 3D model will appear in your FreeCAD document

## Configuration

The Text-to-CAD service is configured in the `cloud_config.json` file with these parameters:
- `text_to_cad_endpoint`: URL of the Text-to-CAD cloud service
- `text_to_cad_api_key`: API key for authentication

## Requirements

- FreeCAD 0.20 or newer
- Internet connection to access the cloud service
- Valid API keys configured in `cloud_config.json`

## Technical Details

The Text-to-CAD integration consists of:
1. A cloud service (`text-to-cad-agent`) that processes natural language requests and generates FreeCAD Python code
2. A client integration (`text_to_cad_integration.py`) that communicates with the cloud service
3. Updates to the StandaloneCoPilot.FCMacro to handle Text-to-CAD requests

The cloud service uses advanced AI to analyze engineering requirements and generate appropriate CAD code with professional engineering analysis.
