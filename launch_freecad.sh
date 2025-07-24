#!/bin/bash
# Launch FreeCAD with the Cloud Co-Pilot macro

# Path to FreeCAD application
FREECAD_APP="/Applications/FreeCAD.app/Contents/MacOS/FreeCAD"

# Check if FreeCAD exists
if [ ! -f "$FREECAD_APP" ]; then
    echo "FreeCAD not found at $FREECAD_APP"
    echo "Please update the path in this script"
    exit 1
fi

echo "Launching FreeCAD with Cloud Co-Pilot..."
echo "Text-to-CAD server should be running on port 9999"
echo "Use natural language commands like 'Generate a 750ml water bottle' to test the Text-to-CAD functionality"

# Launch FreeCAD
"$FREECAD_APP" "$PWD/StandaloneCoPilot.FCMacro"
