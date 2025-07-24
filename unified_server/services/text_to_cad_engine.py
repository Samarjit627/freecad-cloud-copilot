"""
Text-to-CAD Engine Service
Handles conversion of text descriptions to FreeCAD models
"""

import logging
import time
import os
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class TextToCADEngine:
    """Engine for converting text descriptions to CAD models"""
    
    def __init__(self):
        """Initialize the Text-to-CAD engine"""
        logger.info("Initializing Text-to-CAD Engine")
        
        # Load API keys from environment variables
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")
        
        # Import AI libraries conditionally to avoid startup errors if not available
        self.anthropic_client = None
        self.openai_client = None
        
        try:
            import anthropic
            from anthropic import Anthropic
            if self.anthropic_api_key:
                self.anthropic_client = Anthropic(api_key=self.anthropic_api_key)
                logger.info("Anthropic client initialized")
            else:
                logger.warning("Anthropic API key not found, using fallback mode")
        except ImportError:
            logger.warning("Anthropic library not available, using fallback mode")
        
        try:
            import openai
            if self.openai_api_key:
                openai.api_key = self.openai_api_key
                self.openai_client = openai
                logger.info("OpenAI client initialized")
            else:
                logger.warning("OpenAI API key not found, using fallback mode")
        except ImportError:
            logger.warning("OpenAI library not available, using fallback mode")
    
    def generate_engineering_analysis(self, prompt: str, detail_level: str = "medium") -> str:
        """
        Generate engineering analysis from a text prompt
        
        Args:
            prompt: Text description of the design
            detail_level: Level of detail for the analysis (low, medium, high)
            
        Returns:
            Engineering analysis text
        """
        logger.info(f"Generating engineering analysis with detail level: {detail_level}")
        
        # If Anthropic client is available, use it
        if self.anthropic_client:
            try:
                system_prompt = f"""You are an expert mechanical engineer specializing in CAD design.
                Analyze the following design request and provide a detailed engineering analysis.
                Include material recommendations, structural considerations, manufacturing constraints,
                and design optimization suggestions. Use a {detail_level} level of detail.
                """
                
                response = self.anthropic_client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=2000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                return response.content[0].text
            except Exception as e:
                logger.error(f"Error generating engineering analysis with Anthropic: {e}")
                # Fall back to template-based analysis
        
        # If OpenAI client is available, use it as fallback
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": f"You are an expert mechanical engineer specializing in CAD design. Provide a {detail_level} detail engineering analysis."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000
                )
                
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Error generating engineering analysis with OpenAI: {e}")
                # Fall back to template-based analysis
        
        # Fallback to template-based analysis if no AI services are available
        return self._generate_fallback_analysis(prompt, detail_level)
    
    def generate_freecad_code(self, prompt: str, engineering_analysis: str) -> str:
        """
        Generate FreeCAD Python code from a text prompt and engineering analysis
        
        Args:
            prompt: Text description of the design
            engineering_analysis: Engineering analysis text
            
        Returns:
            FreeCAD Python code
        """
        logger.info(f"Generating FreeCAD code for prompt: {prompt[:50]}...")
        
        # If Anthropic client is available, use it
        if self.anthropic_client:
            try:
                system_prompt = """You are an expert FreeCAD programmer. 
                Generate Python code for FreeCAD that implements the requested design.
                The code should be complete, well-commented, and ready to run in FreeCAD's Python console.
                Use best practices for parametric modeling and include appropriate error handling.
                """
                
                combined_prompt = f"""Design Request: {prompt}
                
                Engineering Analysis: {engineering_analysis}
                
                Based on this information, generate complete FreeCAD Python code that implements this design.
                The code should be well-structured, commented, and follow FreeCAD best practices.
                """
                
                response = self.anthropic_client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=4000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": combined_prompt}]
                )
                
                # Extract code blocks from the response
                code = response.content[0].text
                
                # If the response contains markdown code blocks, extract just the code
                if "```python" in code and "```" in code:
                    code_blocks = []
                    lines = code.split("\n")
                    in_code_block = False
                    
                    for line in lines:
                        if line.strip().startswith("```python"):
                            in_code_block = True
                            continue
                        elif line.strip() == "```" and in_code_block:
                            in_code_block = False
                            continue
                        
                        if in_code_block:
                            code_blocks.append(line)
                    
                    return "\n".join(code_blocks)
                
                return code
            except Exception as e:
                logger.error(f"Error generating FreeCAD code with Anthropic: {e}")
                # Fall back to template-based code
        
        # If OpenAI client is available, use it as fallback
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert FreeCAD programmer. Generate Python code for FreeCAD that implements the requested design."},
                        {"role": "user", "content": f"Design: {prompt}\n\nAnalysis: {engineering_analysis}\n\nGenerate FreeCAD Python code for this design."}
                    ],
                    max_tokens=4000
                )
                
                code = response.choices[0].message.content
                
                # If the response contains markdown code blocks, extract just the code
                if "```python" in code and "```" in code:
                    code_blocks = []
                    lines = code.split("\n")
                    in_code_block = False
                    
                    for line in lines:
                        if line.strip().startswith("```python"):
                            in_code_block = True
                            continue
                        elif line.strip() == "```" and in_code_block:
                            in_code_block = False
                            continue
                        
                        if in_code_block:
                            code_blocks.append(line)
                    
                    return "\n".join(code_blocks)
                
                return code
            except Exception as e:
                logger.error(f"Error generating FreeCAD code with OpenAI: {e}")
                # Fall back to template-based code
        
        # Fallback to template-based code if no AI services are available
        return self._generate_fallback_code(prompt)
    
    def _generate_fallback_analysis(self, prompt: str, detail_level: str) -> str:
        """Generate a fallback engineering analysis when AI services are unavailable"""
        logger.info("Using fallback engineering analysis generator")
        
        # Extract keywords from prompt
        keywords = prompt.lower()
        
        # Determine likely object type
        object_type = "component"
        if any(word in keywords for word in ["gear", "cog", "sprocket"]):
            object_type = "gear"
        elif any(word in keywords for word in ["bracket", "mount", "holder"]):
            object_type = "bracket"
        elif any(word in keywords for word in ["enclosure", "case", "housing", "box"]):
            object_type = "enclosure"
        elif any(word in keywords for word in ["shaft", "axle", "rod"]):
            object_type = "shaft"
        
        # Determine likely material
        material = "PLA"
        if any(word in keywords for word in ["metal", "steel", "aluminum", "strong"]):
            material = "metal"
        elif any(word in keywords for word in ["flexible", "soft"]):
            material = "TPU"
        
        # Generate analysis based on object type and detail level
        analysis = f"""# Engineering Analysis for {prompt}

## Overview
This analysis examines the design requirements for the requested {object_type}.

## Material Considerations
For this {object_type}, {material} would be an appropriate material choice based on the requirements.
"""

        if detail_level in ["medium", "high"]:
            analysis += f"""
## Structural Considerations
The {object_type} should be designed with appropriate wall thickness and internal supports to ensure structural integrity.

## Manufacturing Constraints
Consider the following manufacturing constraints:
- Minimum wall thickness: 1.2mm for 3D printing
- Avoid overhangs greater than 45 degrees without supports
- Include appropriate tolerances for mating parts (0.1-0.2mm)
"""

        if detail_level == "high":
            analysis += f"""
## Design Optimization Suggestions
1. Use fillets on internal corners to reduce stress concentration
2. Consider adding ribs for additional strength without increasing material usage
3. Design for proper orientation during manufacturing to minimize support structures
4. Ensure adequate clearance for assembly and operation

## Performance Considerations
The {object_type} should be tested under expected load conditions to verify performance.
Finite Element Analysis (FEA) is recommended for critical components.
"""

        return analysis
    
    def _generate_fallback_code(self, prompt: str) -> str:
        """Generate fallback FreeCAD code when AI services are unavailable"""
        logger.info("Using fallback FreeCAD code generator")
        
        # Extract keywords from prompt
        keywords = prompt.lower()
        
        # Determine object type and generate appropriate code
        if "gear" in keywords:
            return self._generate_gear_code(prompt)
        elif "bracket" in keywords:
            return self._generate_bracket_code(prompt)
        elif "box" in keywords or "enclosure" in keywords:
            return self._generate_box_code(prompt)
        else:
            return self._generate_simple_part_code(prompt)
    
    def _generate_gear_code(self, prompt: str) -> str:
        """Generate code for a gear"""
        # Extract parameters from prompt if possible
        teeth = 20  # Default
        for word in prompt.split():
            if word.isdigit() and 5 <= int(word) <= 100:
                teeth = int(word)
                break
        
        return f"""# FreeCAD Python code for a gear with {teeth} teeth
import FreeCAD as App
import Part
import Draft
import math

# Create a new document
doc = App.newDocument("Gear")

# Parameters
teeth = {teeth}  # Number of teeth
module = 2.0     # Module (tooth size)
thickness = 5.0  # Thickness of the gear
bore = 5.0       # Center hole diameter

# Calculate gear dimensions
pitch_diameter = module * teeth
outer_diameter = pitch_diameter + 2 * module
root_diameter = pitch_diameter - 2.5 * module

# Create the basic gear shape
body = doc.addObject("Part::Cylinder", "GearBody")
body.Radius = outer_diameter / 2
body.Height = thickness

# Create center bore
bore_cut = doc.addObject("Part::Cylinder", "Bore")
bore_cut.Radius = bore / 2
bore_cut.Height = thickness

# Cut the bore from the body
cut = doc.addObject("Part::Cut", "GearWithBore")
cut.Base = body
cut.Tool = bore_cut

# Create a tooth profile
# This is a simplified tooth profile
def create_tooth(angle):
    tooth_height = module
    tooth_width = module * math.pi / 2
    
    # Create a box for the tooth
    tooth = Part.makeBox(tooth_height, tooth_width, thickness)
    
    # Position and rotate the tooth
    tooth.translate(App.Vector(pitch_diameter/2, -tooth_width/2, 0))
    tooth.rotate(App.Vector(0,0,0), App.Vector(0,0,1), angle * 360 / teeth)
    
    return tooth

# Create all teeth
teeth_shapes = []
for i in range(teeth):
    angle = i / teeth
    tooth = create_tooth(angle)
    teeth_shapes.append(tooth)

# Combine all teeth
teeth_union = Part.makeCompound(teeth_shapes)

# Add teeth to document
teeth_obj = doc.addObject("Part::Feature", "Teeth")
teeth_obj.Shape = teeth_union

# Final gear (simplified approach)
doc.recompute()
App.ActiveDocument = doc
App.ActiveDocument.recompute()

print("Gear created successfully")
"""
    
    def _generate_bracket_code(self, prompt: str) -> str:
        """Generate code for a bracket"""
        return """# FreeCAD Python code for a simple bracket
import FreeCAD as App
import Part

# Create a new document
doc = App.newDocument("Bracket")

# Parameters
length = 80.0
width = 40.0
thickness = 5.0
hole_diameter = 6.0
hole_distance = 60.0

# Create the base plate
plate = doc.addObject("Part::Box", "BasePlate")
plate.Length = length
plate.Width = width
plate.Height = thickness

# Create mounting holes
hole1 = doc.addObject("Part::Cylinder", "Hole1")
hole1.Radius = hole_diameter / 2
hole1.Height = thickness
hole1.Placement = App.Placement(App.Vector(10, width/2, 0), App.Rotation(0, 0, 0))

hole2 = doc.addObject("Part::Cylinder", "Hole2")
hole2.Radius = hole_diameter / 2
hole2.Height = thickness
hole2.Placement = App.Placement(App.Vector(10 + hole_distance, width/2, 0), App.Rotation(0, 0, 0))

# Cut the holes from the plate
cut1 = doc.addObject("Part::Cut", "CutHole1")
cut1.Base = plate
cut1.Tool = hole1

cut2 = doc.addObject("Part::Cut", "CutHole2")
cut2.Base = cut1
cut2.Tool = hole2

# Create the vertical support
support = doc.addObject("Part::Box", "Support")
support.Length = thickness
support.Width = width
support.Height = 30.0
support.Placement = App.Placement(App.Vector(length/2 - thickness/2, 0, thickness), App.Rotation(0, 0, 0))

# Fuse the plate and support
bracket = doc.addObject("Part::Fuse", "Bracket")
bracket.Base = cut2
bracket.Tool = support

# Recompute the document
doc.recompute()
App.ActiveDocument = doc
App.ActiveDocument.recompute()

print("Bracket created successfully")
"""
    
    def _generate_box_code(self, prompt: str) -> str:
        """Generate code for a box or enclosure"""
        return """# FreeCAD Python code for a simple enclosure/box
import FreeCAD as App
import Part

# Create a new document
doc = App.newDocument("Enclosure")

# Parameters
length = 100.0
width = 80.0
height = 40.0
wall_thickness = 2.0
fillet_radius = 2.0

# Create outer shell
outer = doc.addObject("Part::Box", "OuterShell")
outer.Length = length
outer.Width = width
outer.Height = height

# Create inner cavity
inner = doc.addObject("Part::Box", "InnerCavity")
inner.Length = length - 2 * wall_thickness
inner.Width = width - 2 * wall_thickness
inner.Height = height - wall_thickness
inner.Placement = App.Placement(App.Vector(wall_thickness, wall_thickness, wall_thickness), App.Rotation(0, 0, 0))

# Cut inner cavity from outer shell
box = doc.addObject("Part::Cut", "BoxShell")
box.Base = outer
box.Tool = inner

# Add fillets to the edges (simplified approach)
# In a real implementation, you would iterate through the edges and add fillets

# Recompute the document
doc.recompute()
App.ActiveDocument = doc
App.ActiveDocument.recompute()

print("Enclosure created successfully")
"""
    
    def _generate_simple_part_code(self, prompt: str) -> str:
        """Generate code for a simple part"""
        return """# FreeCAD Python code for a simple part
import FreeCAD as App
import Part

# Create a new document
doc = App.newDocument("SimplePart")

# Create a box
box = doc.addObject("Part::Box", "Box")
box.Length = 50.0
box.Width = 30.0
box.Height = 10.0

# Create a cylinder
cylinder = doc.addObject("Part::Cylinder", "Cylinder")
cylinder.Radius = 10.0
cylinder.Height = 20.0
cylinder.Placement = App.Placement(App.Vector(25, 15, 10), App.Rotation(0, 0, 0))

# Fuse the shapes
fusion = doc.addObject("Part::Fuse", "Fusion")
fusion.Base = box
fusion.Tool = cylinder

# Recompute the document
doc.recompute()
App.ActiveDocument = doc
App.ActiveDocument.recompute()

print("Simple part created successfully")
"""
