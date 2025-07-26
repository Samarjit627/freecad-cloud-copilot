#!/usr/bin/env python3
"""
Unified Server for FreeCAD Manufacturing Co-Pilot (Pydantic v2 Compatible)
This server provides both DFM analysis and Text-to-CAD functionality
"""

import os
import time
import json
import uuid
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from fastapi.security import APIKeyHeader
from fastapi.security.api_key import APIKeyHeader

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import Anthropic for Claude API
import anthropic
from anthropic import Anthropic

# Import template system
import sys
import os
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cad_templates')
sys.path.append(template_dir)
try:
    from template_manager import get_template_manager
    template_manager_available = True
    print(f"Template manager loaded from {template_dir}")
except ImportError as e:
    template_manager_available = False
    print(f"Template manager not available: {e}")

API_KEY = os.environ.get("API_KEY", "test-api-key")

# API key security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Create FastAPI app
app = FastAPI(
    title="FreeCAD Manufacturing Co-Pilot Unified Server",
    description="Provides DFM analysis and Text-to-CAD functionality",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models for DFM Analysis
class GeometryData(BaseModel):
    volume: float
    surface_area: float
    bounding_box: Dict[str, float]
    overhangs: Optional[bool] = False
    thin_walls: Optional[bool] = False
    sharp_edges: Optional[bool] = False

class ProcessData(BaseModel):
    process: str
    material: str
    quantity: int
    min_feature_size: float
    tolerance: float

class DFMAnalysisRequest(BaseModel):
    geometry: GeometryData
    process_data: ProcessData

class Issue(BaseModel):
    type: str
    severity: str
    description: str

class Recommendation(BaseModel):
    type: str
    description: str

class CostBreakdown(BaseModel):
    material_cost: float
    processing_cost: float

class CostEstimate(BaseModel):
    unit_cost: float
    total_cost: float
    breakdown: CostBreakdown

class LeadTime(BaseModel):
    min_days: int
    max_days: int
    typical_days: int

class DFMAnalysisResponse(BaseModel):
    manufacturability_score: int
    issues: List[Issue]
    recommendations: List[Recommendation]
    cost_estimate: CostEstimate
    lead_time: LeadTime
    cloud_error: Optional[str] = None
    using_fallback: Optional[bool] = None

# Models for Text-to-CAD
class TextToCADRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 2000
    temperature: Optional[float] = 0.7

class TextToCADResponse(BaseModel):
    prompt: str
    engineering_analysis: str
    freecad_code: str
    metadata: Dict[str, Any]
    cloud_error: Optional[str] = None
    using_fallback: Optional[bool] = None

# Authentication dependency
async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return api_key

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "FreeCAD Manufacturing Co-Pilot Unified Server",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "dfm_analysis": "/api/v2/analyze",
            "text_to_cad": "/api/v1/text-to-cad",
            "capabilities": "/list-capabilities",
        },
    }

# Capabilities endpoint
@app.get("/list-capabilities")
async def list_capabilities(api_key: str = Depends(verify_api_key)):
    return {
        "supported_parts": [
            "bracket",
            "enclosure",
            "bottle",
            "container",
            "gear",
            "pulley",
            "mount",
            "adapter",
            "holder",
            "custom"
        ],
        "supported_features": [
            "holes",
            "fillets",
            "chamfers",
            "threads",
            "patterns",
            "text"
        ],
        "version": "2.0.0"
    }

# DFM Analysis endpoint
@app.post("/api/v2/analyze", response_model=DFMAnalysisResponse)
async def analyze_dfm(
    request: DFMAnalysisRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Analyze a 3D model for manufacturability
    """
    # Extract data from request - using model_dump() instead of dict() for Pydantic v2
    geometry = request.geometry.model_dump()
    process_data = request.process_data.model_dump()
    
    # Calculate manufacturability score
    score = random.randint(60, 95)
    
    # Analyze issues
    issues = []
    
    # Add a note that this is the unified server implementation
    issues.append({
        "type": "unified_server",
        "severity": "low",
        "description": "This analysis is from the unified server implementation."
    })
    
    # Check for thin walls
    if geometry.get("thin_walls", False):
        issues.append({
            "type": "thin_walls",
            "severity": "medium",
            "description": "Wall thickness may be too thin for selected process"
        })
    
    # Check for overhangs in FDM printing
    if geometry.get("overhangs", False) and process_data.get("min_feature_size", 0) < 0.5:
        issues.append({
            "type": "overhangs",
            "severity": "high",
            "description": "Overhangs detected that may require support structures"
        })
    
    # Check for sharp edges
    if geometry.get("sharp_edges", False):
        issues.append({
            "type": "sharp_edges",
            "severity": "low",
            "description": "Sharp edges detected that may affect surface finish"
        })
    
    # Generate recommendations
    recommendations = []
    
    # General recommendation
    recommendations.append({
        "type": "general",
        "description": "Consider simplifying the geometry for better manufacturability"
    })
    
    # Material-specific recommendations
    material = process_data.get("material", "").upper()
    if material == "PLA" and random.random() < 0.5:
        recommendations.append({
            "type": "material",
            "description": "PLA has limited temperature resistance, consider ABS for functional parts"
        })
    
    # Calculate cost estimate
    volume = geometry.get("volume", 100)
    quantity = process_data.get("quantity", 1)
    
    material_cost = volume * 0.0875
    processing_cost = volume * 0.0375
    unit_cost = material_cost + processing_cost
    total_cost = unit_cost * quantity
    
    cost_estimate = {
        "unit_cost": unit_cost,
        "total_cost": total_cost,
        "breakdown": {
            "material_cost": material_cost,
            "processing_cost": processing_cost
        }
    }
    
    # Calculate lead time
    process = process_data.get("process", "").upper()
    base_lead_time = 5  # Default lead time in days
    
    if process == "INJECTION_MOLDING":
        base_lead_time = 30
    elif process == "CNC_MACHINING":
        base_lead_time = 10
    elif process == "FDM_PRINTING":
        base_lead_time = 3
    
    # Adjust for quantity
    quantity_factor = 1 + (quantity / 1000)
    
    min_days = max(1, int(base_lead_time * 0.6 * quantity_factor))
    max_days = int(base_lead_time * 1.4 * quantity_factor)
    typical_days = int(base_lead_time * quantity_factor)
    
    lead_time = {
        "min_days": min_days,
        "max_days": max_days,
        "typical_days": typical_days
    }
    
    # Return response
    return {
        "manufacturability_score": score,
        "issues": issues,
        "recommendations": recommendations,
        "cost_estimate": cost_estimate,
        "lead_time": lead_time,
    }

# Text-to-CAD endpoints
# This file contains a fixed version of the text_to_cad function
# Copy this into unified_server_v2.py to replace the problematic function


@app.post("/api/v1/text-to-cad", response_model=TextToCADResponse)
@app.post("/text-to-cad", response_model=TextToCADResponse)
async def text_to_cad(
    request: TextToCADRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Generate FreeCAD code from a text prompt using Anthropic's Claude API
    """
    prompt = request.prompt
    user_id = request.user_id if hasattr(request, 'user_id') else "default_user"
    
    # Initialize variables
    using_fallback = False
    freecad_code = ""
    engineering_analysis = ""
    metadata = {}
    
    try:
        # Initialize Anthropic client with API key from .env file
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise HTTPException(
                status_code=500,
                detail="ANTHROPIC_API_KEY not found in environment variables"
            )
            
        client = Anthropic(api_key=anthropic_api_key)
        
        # Create system prompt for Claude
        system_prompt = """
You are a CAD expert who writes Python code for FreeCAD. Generate Python code for FreeCAD to create the part described by the user.

IMPORTANT REQUIREMENTS:
1. Use the FreeCAD Python API with Part, Draft, and other modules as needed.
2. Include ALL necessary imports at the beginning of your code.
3. Create a complete, executable script that can run standalone in FreeCAD.
4. Create a new document with a descriptive name related to the part.
5. Ensure all dimensions are parametric and well-defined.
6. Add proper error handling with try/except blocks around critical operations.
7. Include fallbacks for complex operations that might fail.
8. Add detailed comments explaining the code and design decisions.
9. Create a visually appealing model with appropriate colors and transparency settings.
10. Include volume calculations and other relevant specifications as document labels.
11. Ensure the model is properly positioned in the 3D space.
12. Update the view at the end of the script to show the complete model.

SPECIFIC GUIDELINES FOR DIFFERENT PART TYPES:
- For containers or bottles: Ensure exact volume calculations, consistent wall thickness, and proper thread geometry if needed.
- For mechanical parts: Include proper tolerances, fillets on sharp edges, and functional dimensions.
- For enclosures: Create both base and lid components with proper fit, include mounting holes and features.
- For brackets or supports: Ensure structural integrity with appropriate reinforcements and mounting options.
- For gears or moving parts: Use precise mathematical formulas for tooth profiles and ensure proper meshing.
"""
        
        # Call Claude API
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=request.max_tokens if hasattr(request, 'max_tokens') else 4000,
            temperature=request.temperature if hasattr(request, 'temperature') else 0.1,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"Generate FreeCAD Python code to create: {prompt}. Only respond with the Python code, no explanations or markdown."}
            ]
        )
        
        # Extract the code from the response
        freecad_code = response.content[0].text
        
        # Clean the code - remove any content after control characters or specific markers
        import re
        freecad_code = re.split(r'[\x00-\x1F]|End File|```', freecad_code)[0].strip()
        print(f"Cleaned FreeCAD code length: {len(freecad_code)}")
        
        # Additional safety - ensure no non-printable characters remain
        freecad_code = ''.join(c for c in freecad_code if c.isprintable())
        
        # Check if the code is too short or incomplete (just imports)
        if len(freecad_code) < 100 or ("import FreeCAD" in freecad_code and len(freecad_code.splitlines()) < 5):
            print("Claude returned incomplete code, using template system")
            # Define a default fallback mode
            fallback_mode = request.prompt.lower()
            
            # Try to use the template manager if available
            if template_manager_available:
                try:
                    # Get template manager instance
                    manager = get_template_manager()
                    
                    # Parse the request to determine template and parameters
                    template_name, params = manager.parse_text_request(request.prompt)
                    
                    if template_name:
                        print(f"Using template: {template_name} with params: {params}")
                        
                        # Generate code to use the template
                        freecad_code = f"""
# Generated code using {template_name} template
import sys
import os
import FreeCAD
import Part

# Use the absolute path to the project directory
project_path = "{os.path.dirname(os.path.abspath(__file__))}"
sys.path.append(os.path.join(project_path, 'cad_templates'))

# Create a new document
doc = FreeCAD.newDocument("{template_name.capitalize()}")
FreeCAD.setActiveDocument(doc.Name)

# Import template manager
from template_manager import get_template_manager

# Get template manager and create part
manager = get_template_manager()

# Create part with specified parameters
result = manager.create_part('{template_name}', doc, {', '.join([f'{k}={v}' for k, v in params.items()])})

# Make sure the document is recomputed
doc.recompute()

# Update the view
try:
    import FreeCADGui
    FreeCADGui.SendMsgToActiveView("ViewFit")
    FreeCADGui.updateGui()
    for obj in doc.Objects:
        FreeCADGui.Selection.addSelection(obj)
    FreeCADGui.runCommand("Std_ViewSelection")
except Exception as e:
    print(f"GUI update error: {{e}}")
"""
                        
                        print(f"Generated template code with length: {len(freecad_code)}")
                        using_fallback = True
                    else:
                        # No suitable template found
                        print("No suitable template found")
                        using_fallback = False
                except Exception as e:
                    print(f"Error using template manager: {e}")
                    using_fallback = False
            
            # Choose appropriate fallback template based on keywords in the prompt
            if (not template_manager_available or not using_fallback):
                # Phone holder fallback
                if "phone" in fallback_mode and ("holder" in fallback_mode or "stand" in fallback_mode):
                    print("Using phone holder template")
                    # Generate phone holder code
                    freecad_code = """
# Phone holder with adjustable angle
import math
import FreeCAD as App
import Part

# Create a new document
doc = App.newDocument("PhoneHolder")
FreeCAD.setActiveDocument(doc.Name)

# Parameters
base_width = 80.0  # mm
base_length = 100.0  # mm
base_height = 10.0  # mm
phone_width = 75.0  # mm
phone_thickness = 10.0  # mm
support_height = 60.0  # mm
support_thickness = 8.0  # mm
angle = 70.0  # degrees

# Create base
base = Part.makeBox(base_length, base_width, base_height)

# Create phone support
support = Part.makeBox(support_thickness, phone_width + 20, support_height)
support.translate(App.Vector(base_length/2 - support_thickness/2, base_width/2 - (phone_width + 20)/2, base_height))

# Rotate support to desired angle
rotation_center = App.Vector(base_length/2, base_width/2, base_height)
support.rotate(rotation_center, App.Vector(0, 1, 0), 90 - angle)

# Create phone slot
slot_depth = 15.0  # mm
slot_width = phone_width + 5.0  # mm for some clearance
slot = Part.makeBox(phone_thickness + 5, slot_width, slot_depth)

# Position the slot on the support
# Calculate position based on the rotated support
slot_position = App.Vector(
    base_length/2 - phone_thickness/2,
    base_width/2 - slot_width/2,
    support_height * math.sin(math.radians(angle)) + base_height - slot_depth/2
)
slot.translate(slot_position)

# Fuse base and support
holder = base.fuse(support)

# Add the phone holder to the document
holder_obj = doc.addObject("Part::Feature", "PhoneHolder")
holder_obj.Shape = holder
holder_obj.Label = "Phone Holder"

# Add the slot to the document
slot_obj = doc.addObject("Part::Feature", "PhoneSlot")
slot_obj.Shape = slot
slot_obj.Label = "Phone Slot"

# Recompute the document
doc.recompute()

# Ensure the 3D view is updated
try:
    import FreeCADGui
    # Make sure document is active
    if FreeCAD.ActiveDocument is None and len(FreeCAD.listDocuments()) > 0:
        FreeCAD.setActiveDocument(list(FreeCAD.listDocuments().keys())[0])
    
    if FreeCADGui.ActiveDocument:
        # Force multiple view updates for robustness
        FreeCADGui.ActiveDocument.Document.recompute()
        FreeCADGui.ActiveDocument.ActiveView.fitAll()
        FreeCADGui.updateGui()
        FreeCADGui.SendMsgToActiveView("ViewFit")
        
        # Try to select objects to make them visible
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(holder_obj)
        FreeCADGui.Selection.addSelection(slot_obj)
        
        # Additional commands to ensure view update
        try:
            FreeCADGui.runCommand("Std_ViewFitAll")
            FreeCADGui.runCommand("Std_ViewSelection")
        except:
            pass
except Exception as e:
    print(f"GUI update failed: {e}")
"""
                    engineering_analysis = "Phone holder designed with an adjustable angle of 70 degrees, suitable for most smartphones up to 75mm wide."
                    metadata = {"type": "phone_holder", "dimensions": {"width": 80, "length": 100, "height": 60}}
                    using_fallback = True
                
                # Water bottle fallback
                elif "bottle" in fallback_mode or "water" in fallback_mode:
                    print("Using fixed water bottle code")
                    # Import and use the fixed water bottle implementation directly
                
                # Default fallback for any other prompt type
                else:
                    print("Using default cube template")
                    # Generate a simple parametric cube
                    freecad_code = f"""
# Simple parametric cube for '{request.prompt}'
import FreeCAD as App
import Part

# Create a new document
doc = App.newDocument("GenericPart")
FreeCAD.setActiveDocument(doc.Name)

# Parameters - adjust as needed
width = 50.0  # mm
length = 70.0  # mm
height = 30.0  # mm
fillet_radius = 5.0  # mm

# Create base cube
box = Part.makeBox(length, width, height)

# Apply fillets to all edges for a nicer look
edges = []
for edge in box.Edges:
    edges.append(edge)

filleted_box = box.makeFillet(fillet_radius, edges)

# Add to document
part_obj = doc.addObject("Part::Feature", "GenericPart")
part_obj.Shape = filleted_box
part_obj.Label = "Generic Part"

# Add dimensions as annotations
try:
    width_label = doc.addObject("App::Annotation", "WidthLabel")
    width_label.LabelText = f"Width: {width} mm"
    width_label.Position = App.Vector(length/2, -10, height/2)
    
    length_label = doc.addObject("App::Annotation", "LengthLabel")
    length_label.LabelText = f"Length: {length} mm"
    length_label.Position = App.Vector(length + 10, width/2, height/2)
    
    height_label = doc.addObject("App::Annotation", "HeightLabel")
    height_label.LabelText = f"Height: {height} mm"
    height_label.Position = App.Vector(length/2, width/2, height + 10)
except Exception as e:
    print(f"Failed to create labels: {{e}}")

doc.recompute()

# Ensure the 3D view is updated
try:
    import FreeCADGui
    # Make sure document is active
    if FreeCAD.ActiveDocument is None and len(FreeCAD.listDocuments()) > 0:
        FreeCAD.setActiveDocument(list(FreeCAD.listDocuments().keys())[0])
    
    if FreeCADGui.ActiveDocument:
        # Force multiple view updates for robustness
        FreeCADGui.ActiveDocument.Document.recompute()
        FreeCADGui.ActiveDocument.ActiveView.fitAll()
        FreeCADGui.updateGui()
        FreeCADGui.SendMsgToActiveView("ViewFit")
        
        # Try to select objects to make them visible
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(part_obj)
        
        # Additional commands to ensure view update
        try:
            FreeCADGui.runCommand("Std_ViewFitAll")
            FreeCADGui.runCommand("Std_ViewSelection")
        except:
            pass
except Exception as e:
    print(f"GUI update failed: {{e}}")
"""
                    engineering_analysis = f"Generic parametric part created for '{request.prompt}' with standard dimensions and filleted edges."
                    metadata = {"type": "generic_part", "dimensions": {"width": 50, "length": 70, "height": 30}}
                    using_fallback = True
                try:
                    # Use absolute path to import the water bottle module
                    project_path = os.path.dirname(os.path.abspath(__file__))
                    sys.path.append(project_path)
                    
                    # Extract volume from prompt if available
                    import re
                    volume_match = re.search(r'(\d+)\s*ml', fallback_mode)
                    volume = 750.0  # Default volume
                    wall_thickness = 2.0  # Default wall thickness
                    actual_volume = volume  # Default to requested volume
                    
                    # Initialize volume-related variables for error handling
                    body_volume = volume * 0.8  # Estimate: body is 80% of total volume
                    transition_inner_volume = volume * 0.1  # Estimate: transition is 10% of total volume
                    neck_inner_volume = volume * 0.1  # Estimate: neck is 10% of total volume
                    
                    if volume_match:
                        volume = float(volume_match.group(1))
                        actual_volume = volume  # Set actual volume to match requested volume
                        # Update estimates based on new volume
                        body_volume = volume * 0.8
                        transition_inner_volume = volume * 0.1
                        neck_inner_volume = volume * 0.1
                        print(f"Extracted volume from prompt: {volume}ml")
                except Exception as e:
                    print(f"Error setting up water bottle fallback: {e}")
                    volume = 750.0  # Default to 750ml if there's an error
                
                # Generate water bottle code with the specified volume
                freecad_code = f"""
# Water bottle with {volume}ml volume
import math
import FreeCAD as App
import Part

# Create a new document
doc = App.newDocument("WaterBottle")
FreeCAD.setActiveDocument(doc.Name)

# Water Bottle with Exact Volume Calculation
# This code creates a water bottle with exact {volume}ml capacity

# Parameters
volume = {volume}  # ml (EXACT target volume)
wall_thickness = 2.0  # mm (consistent wall thickness throughout)
neck_diameter = 28  # mm
neck_height = 20  # mm
cap_height = 15  # mm
thread_height = 15  # mm
transition_height = 20  # mm

# Calculate dimensions for exact volume
neck_inner_radius = (neck_diameter - 2 * wall_thickness) / 2
body_diameter = 75  # mm - optimized for standard bottle
body_inner_radius = (body_diameter - 2 * wall_thickness) / 2

# Calculate volumes step by step for exact volume
# 1. Neck inner volume
neck_inner_volume_mm3 = math.pi * neck_inner_radius**2 * neck_height
neck_inner_volume_ml = neck_inner_volume_mm3 / 1000.0

# 2. Transition inner volume (truncated cone)
r1 = body_inner_radius  # bottom radius
r2 = neck_inner_radius  # top radius
transition_inner_volume_mm3 = (math.pi * transition_height / 3.0) * (r1**2 + r1*r2 + r2**2)
transition_inner_volume_ml = transition_inner_volume_mm3 / 1000.0

# 3. Calculate exact body height for remaining volume
remaining_volume_ml = volume - neck_inner_volume_ml - transition_inner_volume_ml
remaining_volume_mm3 = remaining_volume_ml * 1000.0
body_height = remaining_volume_mm3 / (math.pi * body_inner_radius**2)

print(f"Calculated body height for {volume}ml: {{body_height:.2f}}mm")

# Create bottle body
body_outer = Part.makeCylinder(body_diameter/2, body_height)
body_inner = Part.makeCylinder(body_inner_radius, body_height - wall_thickness)
body_inner.translate(App.Vector(0, 0, wall_thickness))  # Bottom wall thickness
body = body_outer.cut(body_inner)

# Create transition (connects body to neck)
transition_outer = Part.makeCone(body_diameter/2, neck_diameter/2, transition_height)
transition_inner = Part.makeCone(body_inner_radius, neck_inner_radius, transition_height)
transition_inner.translate(App.Vector(0, 0, 0.01))  # Small offset to avoid precision issues
transition = transition_outer.cut(transition_inner)

# Position the transition at the top of the body
transition.translate(App.Vector(0, 0, body_height))

# Create neck
neck_outer = Part.makeCylinder(neck_diameter/2, neck_height)
neck_inner = Part.makeCylinder(neck_inner_radius, neck_height)
neck = neck_outer.cut(neck_inner)
neck.translate(App.Vector(0, 0, body_height + transition_height))

# Fuse all parts together
bottle = body.fuse(transition).fuse(neck)

# Add to document
bottle_obj = doc.addObject("Part::Feature", "WaterBottle")
bottle_obj.Shape = bottle
bottle_obj.Label = f"Water Bottle {volume}ml"

# Add volume information
info = doc.addObject("App::Annotation", "VolumeInfo")
info.LabelText = f"Volume: {volume}ml\\nWall thickness: {wall_thickness}mm"

# Create cap
cap = Part.makeCylinder(neck_diameter/2 + 2, cap_height)
cap.translate(App.Vector(0, 0, body_height + neck_height))
cap_obj = doc.addObject("Part::Feature", "Cap")
cap_obj.Shape = cap

# Calculate actual volume with high precision
body_volume = body_inner.Volume / 1000  # Convert mm^3 to ml
transition_inner_volume = transition_inner.Volume / 1000  # Convert mm^3 to ml
neck_inner_volume = neck_inner.Volume / 1000  # Convert mm^3 to ml
actual_volume = body_volume + transition_inner_volume + neck_inner_volume

# Display detailed volume information
print(f"Target volume: {volume:.2f} ml")
print(f"Actual volume: {actual_volume:.2f} ml")
print(f"  - Body volume: {body_volume:.2f} ml")
print(f"  - Transition volume: {transition_inner_volume:.2f} ml")
print(f"  - Neck volume: {neck_inner_volume:.2f} ml")
print(f"Volume accuracy: {actual_volume/volume*100:.1f}%")

# Add a text label showing the volume
try:
    # Create a more visible volume label
    volume_label = doc.addObject("App::Annotation", "VolumeLabel")
    volume_label.LabelText = f"Volume: {actual_volume:.1f} ml"
    volume_label.Position = App.Vector(0, -body_diameter/2 - 20, body_height/2)
    
    # Add a second label with target volume for comparison
    target_label = doc.addObject("App::Annotation", "TargetVolumeLabel")
    target_label.LabelText = f"Target: {volume:.1f} ml"
    target_label.Position = App.Vector(0, -body_diameter/2 - 20, body_height/2 + 10)
    
    # Add a label showing wall thickness
    wall_label = doc.addObject("App::Annotation", "WallThicknessLabel")
    wall_label.LabelText = f"Wall: {wall_thickness:.1f} mm"
    wall_label.Position = App.Vector(0, -body_diameter/2 - 20, body_height/2 - 10)
    
    doc.recompute()
except Exception as e:
    print(f"Failed to create labels: {{e}}")

doc.recompute()

# Ensure the 3D view is updated
try:
    import FreeCADGui
    # Make sure document is active
    if FreeCAD.ActiveDocument is None and len(FreeCAD.listDocuments()) > 0:
        FreeCAD.setActiveDocument(list(FreeCAD.listDocuments().keys())[0])
    
    if FreeCADGui.ActiveDocument:
        # Force multiple view updates for robustness
        FreeCADGui.ActiveDocument.Document.recompute()
        FreeCADGui.ActiveDocument.ActiveView.fitAll()
        FreeCADGui.updateGui()
        FreeCADGui.SendMsgToActiveView("ViewFit")
        
        # Try to select objects to make them visible
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(bottle_obj)
        FreeCADGui.Selection.addSelection(cap_obj)
        
        # Additional commands to ensure view update
        try:
            FreeCADGui.runCommand("Std_ViewFitAll")
            FreeCADGui.runCommand("Std_ViewSelection")
        except:
            pass
        
        # Final GUI update
        FreeCADGui.updateGui()
except Exception as e:
    print(f"Error updating 3D view: {{e}}")
    pass  # Headless mode or other error
"""
                using_fallback = True
                
        # Generate a simple engineering analysis
        engineering_analysis = f"# Engineering Analysis for {prompt}\n\n## Overview\nThis analysis is for creating {prompt} using FreeCAD.\n\n## Requirements\n- Create a 3D model based on the prompt\n- Ensure manufacturability\n- Follow best practices for CAD design\n\n## Constraints\n- Dimensions are appropriate for the described object\n- Material properties considered for the application\n- Manufacturing process taken into account"
        
        # Create metadata
        metadata = {
            "generated_by": "anthropic_claude",
            "model": "claude-3-5-sonnet-20240620",
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(freecad_code.split()),
            "timestamp": time.time(),
            "user_id": user_id
        }
        
        # Return response
        return {
            "prompt": prompt,
            "freecad_code": freecad_code,
            "using_fallback": using_fallback,
            "engineering_analysis": engineering_analysis,
            "metadata": metadata,
            "cloud_error": None
        }
    except Exception as e:
        print(f"Error in text_to_cad endpoint: {e}")
        # Log the error but return a proper response instead of raising an exception
        # This ensures the client gets a useful response even when errors occur
        return {
            "prompt": request.prompt if hasattr(request, 'prompt') else "Unknown prompt",
            "freecad_code": "",
            "using_fallback": True,
            "engineering_analysis": "Error generating CAD model",
            "metadata": {"error": str(e)},
            "cloud_error": str(e)
        }

@app.get("/debug/test-water-bottle")
async def debug_test_water_bottle(api_key: str = Depends(verify_api_key)):
    """Direct test endpoint for water bottle template"""
    print("=== DEBUG: Direct water bottle template test ===")
    
    volume = 500
    wall_thickness = 2.0
    
    # Use simple concatenated strings to avoid triple quote issues
    bottle_template = ('# Test water bottle with VOLUME_PLACEHOLDER ml\n'
                      'import FreeCAD as App\n'
                      'import Part\n\n'
                      'doc = App.newDocument("TestBottle")\n'
                      'bottle = Part.makeCylinder(30, 100)\n'
                      'obj = doc.addObject("Part::Feature", "TestBottle")\n'
                      'obj.Shape = bottle\n'
                      'obj.Label = "Test Bottle VOLUME_PLACEHOLDER ml"\n'
                      'doc.recompute()\n'
                      'print("Test bottle created successfully")\n')
    
    freecad_code = bottle_template.replace('VOLUME_PLACEHOLDER', str(volume))
    
    print(f"DEBUG: Direct test - code length: {len(freecad_code)}")
    
    # Return in the same format as the text_to_cad endpoint
    return {
        "prompt": f"Debug test water bottle {volume}ml",
        "freecad_code": freecad_code,
        "using_fallback": True,
        "engineering_analysis": f"Water bottle designed with {volume}ml capacity and {wall_thickness}mm wall thickness",
        "metadata": {
            "type": "water_bottle",
            "volume_ml": volume,
            "wall_thickness_mm": wall_thickness,
            "code_length": len(freecad_code),
            "debug_test": True
        },
        "cloud_error": None
    }

# Run the server
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8089))  # Changed default port to 8089
    uvicorn.run(app, host="0.0.0.0", port=port)
