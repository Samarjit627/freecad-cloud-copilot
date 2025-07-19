"""
Convert sketches and images to CAD models
"""

import FreeCAD
import Part
import math
import json

class SketchToCADProcessor:
    """Process sketch descriptions and create CAD models"""
    
    def __init__(self):
        """Initialize the processor"""
        self.doc = None
        
    def process_sketch_description(self, description):
        """Process a sketch description and create a CAD model"""
        try:
            # Check if description contains plate with holes
            if "plate" in description.lower() and "hole" in description.lower():
                return self.create_plate_from_sketch(description)
            
            # Check for basic shapes
            if any(shape in description.lower() for shape in ["sphere", "cylinder", "cone", "box", "cube", "torus"]):
                return self.create_generic_from_sketch(description)
                
            # Default to generic shape
            return self.create_generic_from_sketch(description)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Error processing sketch: {str(e)}"}
    
    def create_plate_from_sketch(self, description):
        """Create plate from sketch description"""
        doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("SketchPart")
        
        try:
            # Parse dimensions from description
            import re
            
            # Look for width, length, thickness/height
            width_match = re.search(r'width[:\s]*(\d+(?:\.\d+)?)', description, re.IGNORECASE)
            length_match = re.search(r'length[:\s]*(\d+(?:\.\d+)?)', description, re.IGNORECASE)
            thickness_match = re.search(r'(thickness|height)[:\s]*(\d+(?:\.\d+)?)', description, re.IGNORECASE)
            
            # Also look for dimensions in format like 200x100
            dimensions_match = re.search(r'(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)', description, re.IGNORECASE)
            
            # Extract dimensions with defaults
            width = 100.0
            length = 100.0
            thickness = 5.0
            
            if width_match:
                width = float(width_match.group(1))
            elif dimensions_match:
                length = float(dimensions_match.group(1))
                width = float(dimensions_match.group(2))
                
            if length_match:
                length = float(length_match.group(1))
                
            if thickness_match:
                thickness = float(thickness_match.group(2))
            
            print(f"Creating plate with dimensions: {length}x{width}x{thickness}mm")
            
            # Check for holes
            has_holes = 'hole' in description.lower() or 'mounting' in description.lower()
            hole_count = 0
            hole_diameter = 5.0
            
            if has_holes:
                # Try to extract hole count and size
                hole_count_match = re.search(r'(\d+)\s*holes?', description, re.IGNORECASE)
                hole_diameter_match = re.search(r'(\d+(?:\.\d+)?)\s*mm\s*holes?', description, re.IGNORECASE)
                
                hole_count = int(hole_count_match.group(1)) if hole_count_match else 4
                hole_diameter = float(hole_diameter_match.group(1)) if hole_diameter_match else 5.0
            
            print(f"Plate will have {hole_count} holes with diameter {hole_diameter}mm")
            
            # Create base plate using Part.Box directly (more reliable than makeBox)
            plate = Part.Box(length, width, thickness)
            
            # Add holes if specified
            if has_holes and hole_count > 0:
                holes = []
                
                if hole_count == 4:  # Mounting holes in corners
                    margin = max(10.0, hole_diameter * 1.5)
                    hole_positions = [
                        (margin, margin),
                        (length - margin, margin),
                        (length - margin, width - margin),
                        (margin, width - margin)
                    ]
                    
                    for pos in hole_positions:
                        try:
                            # Create cylinder with proper placement
                            cylinder = Part.makeCylinder(
                                hole_diameter/2,  # radius
                                thickness + 1,    # height (slightly larger)
                                FreeCAD.Vector(pos[0], pos[1], -0.5),  # position (slightly lower)
                                FreeCAD.Vector(0, 0, 1)  # direction
                            )
                            
                            # Check if shapes are valid
                            if not cylinder.isValid():
                                print(f"Warning: Invalid cylinder at position {pos}")
                                continue
                                
                            holes.append(cylinder)
                        except Exception as e:
                            print(f"Error creating hole at {pos}: {e}")
                else:  # Evenly distributed holes
                    rows = int(math.sqrt(hole_count))
                    cols = math.ceil(hole_count / rows)
                    
                    row_spacing = width / (rows + 1)
                    col_spacing = length / (cols + 1)
                    
                    count = 0
                    for r in range(1, rows + 1):
                        for c in range(1, cols + 1):
                            if count < hole_count:
                                try:
                                    cylinder = Part.makeCylinder(
                                        hole_diameter/2,
                                        thickness + 1,
                                        FreeCAD.Vector(c * col_spacing, r * row_spacing, -0.5),
                                        FreeCAD.Vector(0, 0, 1)
                                    )
                                    
                                    if not cylinder.isValid():
                                        print(f"Warning: Invalid cylinder at row {r}, col {c}")
                                        continue
                                        
                                    holes.append(cylinder)
                                    count += 1
                                except Exception as e:
                                    print(f"Error creating hole at row {r}, col {c}: {e}")
                
                # Cut holes from plate one by one with error handling
                for i, hole in enumerate(holes):
                    try:
                        # Use BRep cut operation with tolerance
                        plate = plate.cut(hole)
                        
                        # Verify the result is valid
                        if not plate.isValid():
                            print(f"Warning: Result shape is invalid after cutting hole {i+1}")
                            plate = plate.fix(0.01, 0.01, 0.01)  # Try to fix the shape
                    except Exception as e:
                        print(f"Error cutting hole {i+1}: {e}")
            
            # Check final shape validity
            if not plate.isValid():
                print("Warning: Final plate shape is invalid, attempting to fix...")
                plate = plate.fix(0.01, 0.01, 0.01)  # Try to fix the shape
            
            # Create FreeCAD object
            plate_obj = doc.addObject("Part::Feature", "SketchPlate")
            plate_obj.Shape = plate
            
            doc.recompute()
            
            # Generate message
            msg = f'Created plate {length}x{width}x{thickness}mm'
            if has_holes and hole_count > 0:
                msg += f' with {hole_count} holes (ø{hole_diameter}mm)'
            
            return {
                'success': True,
                'message': msg,
                'object': plate_obj
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f'Error creating plate: {str(e)}'}
    
    def create_generic_from_sketch(self, description):
        """Create generic shape from sketch description"""
        doc = FreeCAD.ActiveDocument or FreeCAD.newDocument("SketchPart")
        
        try:
            # Try to identify basic shape from description
            desc_lower = description.lower()
            
            # Extract dimensions
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', description)
            
            # Convert to float
            dimensions = [float(num) for num in numbers]
            
            # Fill in missing dimensions with defaults
            while len(dimensions) < 3:
                dimensions.append(50.0)
                
            # Create shape based on keywords
            if 'sphere' in desc_lower or 'ball' in desc_lower:
                radius = dimensions[0] / 2 if dimensions else 25.0
                shape = Part.makeSphere(radius)
                shape_obj = doc.addObject("Part::Feature", "Sphere")
                msg = f'Created sphere with radius {radius}mm'
                
            elif 'cylinder' in desc_lower or 'tube' in desc_lower:
                radius = dimensions[0] / 2 if len(dimensions) > 0 else 25.0
                height = dimensions[1] if len(dimensions) > 1 else 100.0
                
                # Check if hollow
                if 'hollow' in desc_lower or 'tube' in desc_lower:
                    inner_radius = radius * 0.7  # Default to 70% of outer radius
                    
                    # Check for specific inner diameter
                    inner_match = re.search(r'inner[:\s]*(\d+(?:\.\d+)?)', description, re.IGNORECASE)
                    if inner_match:
                        inner_radius = float(inner_match.group(1)) / 2
                    
                    outer = Part.makeCylinder(radius, height)
                    inner = Part.makeCylinder(inner_radius, height + 1)  # Slightly taller
                    inner.translate(FreeCAD.Vector(0, 0, -0.5))  # Shift down slightly
                    shape = outer.cut(inner)
                    shape_obj = doc.addObject("Part::Feature", "Tube")
                    msg = f'Created tube with outer diameter {radius*2}mm, inner diameter {inner_radius*2}mm, height {height}mm'
                else:
                    shape = Part.makeCylinder(radius, height)
                    shape_obj = doc.addObject("Part::Feature", "Cylinder")
                    msg = f'Created cylinder with diameter {radius*2}mm, height {height}mm'
                
            elif 'cone' in desc_lower:
                radius1 = dimensions[0] / 2 if len(dimensions) > 0 else 25.0
                radius2 = dimensions[1] / 2 if len(dimensions) > 1 else 10.0
                height = dimensions[2] if len(dimensions) > 2 else 100.0
                
                shape = Part.makeCone(radius1, radius2, height)
                shape_obj = doc.addObject("Part::Feature", "Cone")
                msg = f'Created cone with base diameter {radius1*2}mm, top diameter {radius2*2}mm, height {height}mm'
                
            elif 'torus' in desc_lower or 'donut' in desc_lower:
                radius1 = dimensions[0] / 2 if len(dimensions) > 0 else 50.0  # Major radius
                radius2 = dimensions[1] / 2 if len(dimensions) > 1 else 10.0  # Minor radius
                
                shape = Part.makeTorus(radius1, radius2)
                shape_obj = doc.addObject("Part::Feature", "Torus")
                msg = f'Created torus with major diameter {radius1*2}mm, minor diameter {radius2*2}mm'
                
            else:  # Default to box
                length = dimensions[0] if len(dimensions) > 0 else 100.0
                width = dimensions[1] if len(dimensions) > 1 else 100.0
                height = dimensions[2] if len(dimensions) > 2 else 50.0
                
                shape = Part.makeBox(length, width, height)
                shape_obj = doc.addObject("Part::Feature", "Box")
                msg = f'Created box {length}x{width}x{height}mm'
            
            # Assign shape
            shape_obj.Shape = shape
            doc.recompute()
            
            return {
                'success': True,
                'message': msg,
                'object': shape_obj
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error creating shape: {str(e)}'}
