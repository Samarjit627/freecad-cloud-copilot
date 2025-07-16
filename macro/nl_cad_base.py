"""
Natural Language CAD Editor for FreeCAD
"""

import re
import math
import random
import FreeCAD
import Part
from cloud_ai_processor import CloudAIProcessor
from context_manager import DesignContextManager

class NaturalLanguageCADEditor:
    """Natural Language CAD Editor"""
    
    def __init__(self):
        """Initialize the NL CAD editor"""
        self.standard_parts = None
        self.manufacturing = None
        self.optimization = None
        self.command_handlers = {}
        self.assembly_gen = None  # Will be initialized later
        self.ai_processor = None  # Will be initialized in initialize_modules
        self.context = None  # Will be initialized in initialize_modules
        
    def initialize_modules(self):
        """Initialize all modules"""
        try:
            # Import modules
            from standard_parts import StandardParts
            from manufacturing_features import ManufacturingFeatures
            from optimization_features import OptimizationFeatures
            from assembly_generator import AssemblyGenerator
            from cloud_ai_processor import CloudAIProcessor
            from context_manager import DesignContextManager
            # Initialize modules
            self.standard_parts = StandardParts()
            print("Debug: StandardParts initialized in NaturalLanguageCADEditor")
            
            self.manufacturing = ManufacturingFeatures()
            print("Debug: ManufacturingFeatures initialized in NaturalLanguageCADEditor")
            
            self.optimization = OptimizationFeatures()
            print("Debug: OptimizationFeatures initialized in NaturalLanguageCADEditor")
            
            # Initialize Stage 3 modules
            self.assembly_gen = AssemblyGenerator(self.standard_parts)
            print("Debug: AssemblyGenerator initialized in NaturalLanguageCADEditor")
            
            # Initialize AI processor and context manager if not already initialized
            if not self.ai_processor:
                self.ai_processor = CloudAIProcessor()
                print("Debug: CloudAIProcessor initialized in NaturalLanguageCADEditor")
            else:
                print("Debug: CloudAIProcessor already initialized")
            
            if not self.context:
                self.context = DesignContextManager()
                print("Debug: DesignContextManager initialized in NaturalLanguageCADEditor")
            else:
                print("Debug: DesignContextManager already initialized")
            
            # Register command handlers
            self.register_command_handler('gear', self.handle_gear)
            self.register_command_handler('bearing', self.handle_bearing)
            self.register_command_handler('shaft', self.handle_shaft)
            self.register_command_handler('draft', self.handle_draft)
            self.register_command_handler('taper', self.handle_draft)
            self.register_command_handler('rib', self.handle_ribs)
            self.register_command_handler('ribs', self.handle_ribs)
            self.register_command_handler('reinforce', self.handle_ribs)
            self.register_command_handler('shell', self.handle_shell)
            self.register_command_handler('hollow', self.handle_shell)
            self.register_command_handler('extrude', self.handle_extrude)
            self.register_command_handler('moldable', self.handle_moldable)
            self.register_command_handler('injection', self.handle_moldable)
            self.register_command_handler('printable', self.handle_printable)
            self.register_command_handler('3d print', self.handle_printable)
            self.register_command_handler('lighter', self.handle_weight)
            self.register_command_handler('reduce weight', self.handle_weight)
            self.register_command_handler('hole', self.handle_hole)
            self.register_command_handler('drill', self.handle_hole)
            self.register_command_handler('fillet', self.handle_fillet)
            self.register_command_handler('round', self.handle_fillet)
            self.register_command_handler('create', self.handle_create)
            self.register_command_handler('make', self.handle_create)
            
            # Assembly commands
            self.register_command_handler('assembly', self.handle_assembly)
            self.register_command_handler('mechanism', self.handle_assembly)
            self.register_command_handler('gearbox', self.handle_gearbox)
            self.register_command_handler('suggest', self.handle_suggestions)
            self.register_command_handler('next', self.handle_suggestions)
            self.register_command_handler('help', self.handle_suggestions)
            
            # AI-enhanced commands
            self.register_command_handler('design', self.handle_ai_design)
            self.register_command_handler('analyze', self.handle_analyze)
            
            print(f"Debug: Registered {len(self.command_handlers)} command keywords: {list(self.command_handlers.keys())}")
            print("Debug: NL CAD modules initialized - Standard Parts, Manufacturing Features, and Optimization Features loaded")
            return True
        except Exception as e:
            print(f"Error initializing NL CAD modules: {str(e)}")
            return False
    
    def register_command_handler(self, keyword, handler):
        """Register a command handler for a keyword"""
        self.command_handlers[keyword.lower()] = handler
        print(f"Debug: Registered keyword '{keyword}' to handler {handler.__name__}")
    
    def process_command(self, text):
        """Process command with AI enhancement"""
        try:
            # Update context
            self.context.add_created_part({
                'type': 'command',
                'name': text
            })
            
            # Check if it's a complex command that needs AI
            if self.is_complex_command(text):
                return self.handle_ai_design(text)
            
            # Otherwise use standard processing
            print(f"Debug: Processing command: '{text}'")
            
            # Check if any registered keywords match
            print(f"Debug: Registered command keywords: {list(self.command_handlers.keys())}")
            
            # Define priority groups - specific commands should be matched before generic ones
            generic_keywords = ['create', 'make']
            
        except Exception as e:
            return {'success': False, 'message': f"Error: {str(e)}"}
        
        best_match = None
        for keyword in self.command_handlers.keys():
            if keyword.lower() in text.lower():
                if best_match is None or len(keyword) > len(best_match):
                    best_match = keyword
        
        # If a keyword is found, call the corresponding handler
        if best_match:
            handler = self.command_handlers[best_match]
            print(f"Debug: Best matching keyword '{best_match}', calling handler {handler.__name__}")
            return handler(text)
        
        # If no keyword is found, try cloud AI processing
        if hasattr(self, 'ai_processor') and self.ai_processor:
            try:
                result = self.ai_processor.process(text)
                
                # Check if the result contains a command field that matches a handler
                if result and 'command' in result:
                    command = result['command']
                    if command in self.command_handlers:
                        print(f"Debug: Found command '{command}' in AI result, calling handler {self.command_handlers[command].__name__}")
                        # Extract parameters from the result
                        if 'parameters' in result:
                            # For fillet commands, pass the radius parameter
                            if command == 'fillet' and 'radius' in result['parameters']:
                                print(f"Debug: Using radius {result['parameters']['radius']} from AI result")
                                # Modify text to include the radius for the handler
                                text = f"{text} with radius {result['parameters']['radius']}mm"
                        return self.command_handlers[command](text)
                
                if result and 'success' in result and result['success']:
                    return result
            except Exception as e:
                print(f"Error in AI processing: {str(e)}")
                # Try local processing for fillet commands if cloud fails
                if 'fillet' in text.lower() or 'round' in text.lower():
                    print("Debug: Cloud processing failed, trying local fillet handler")
                    return self.handle_fillet(text)
        
        # Fallback to direct fillet handling for fillet-related commands
        if 'fillet' in text.lower() or 'round' in text.lower():
            print("Debug: No handler found but detected fillet command, using fillet handler directly")
            return self.handle_fillet(text)
            
        # Fallback message for unrecognized commands
        print(f"Debug: No command handler found for '{text}'")
        return {'success': False, 'message': f"Command not recognized: '{text}'", 'handled': False}
    
    def handle_create(self, text):
        """Handle create commands"""
        print(f"Debug: handle_create processing: '{text}'")
        
        # Extract shape type
        shape_type = 'box'  # Default
        if 'cylinder' in text.lower() or 'rod' in text.lower():
            shape_type = 'cylinder'
        elif 'sphere' in text.lower() or 'ball' in text.lower():
            shape_type = 'sphere'
        elif 'cone' in text.lower():
            shape_type = 'cone'
        
        # Extract dimensions
        dimensions = re.findall(r'\d+(?:\.\d+)?', text)
        dimensions = [float(d) for d in dimensions]
        
        # Create the shape
        doc = FreeCAD.ActiveDocument
        if not doc:
            doc = FreeCAD.newDocument()
        
        if shape_type == 'box':
            # Default dimensions
            l, w, h = 10.0, 10.0, 10.0
            
            # Override with provided dimensions
            if len(dimensions) >= 3:
                l, w, h = dimensions[0], dimensions[1], dimensions[2]
            elif len(dimensions) == 2:
                l, w = dimensions[0], dimensions[1]
                h = min(l, w) / 2
            elif len(dimensions) == 1:
                l = w = h = dimensions[0]
            
            # Create box
            box = doc.addObject("Part::Box", "Box")
            box.Length = l
            box.Width = w
            box.Height = h
            
            doc.recompute()
            
            return {
                'success': True,
                'message': f"Created box {l}×{w}×{h}mm"
            }
            
        elif shape_type == 'cylinder':
            # Default dimensions
            d, h = 10.0, 20.0
            
            # Override with provided dimensions
            if len(dimensions) >= 2:
                d, h = dimensions[0], dimensions[1]
            elif len(dimensions) == 1:
                d = dimensions[0]
                h = d * 2
            
            # Create cylinder
            cylinder = doc.addObject("Part::Cylinder", "Cylinder")
            cylinder.Radius = d / 2
            cylinder.Height = h
            
            doc.recompute()
            
            return {
                'success': True,
                'message': f"Created cylinder ø{d}×{h}mm"
            }
        
    def handle_hole(self, text):
        """Add a hole"""
        # Basic implementation
        return {'success': True, 'message': "Hole feature coming soon"}
    
    def handle_fillet(self, text):
        """Add fillets to selected edges or all edges of selected objects"""
        print(f"Debug: handle_fillet called with text: {text}")
        
        # Extract radius
        radius = None
        radius_patterns = [
            r'(?:with|of|using)\s+(?:a\s+)?(?:radius|r)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:mm|millimeters?)?',  # with radius of 2mm
            r'(\d+(?:\.\d+)?)\s*(?:mm|millimeters?)\s*(?:radius|r)',  # 2mm radius
            r'radius\s*[=:]\s*(\d+(?:\.\d+)?)',  # radius=2
            r'(?:fillet|fillets)\s+(?:of|with)\s+(\d+(?:\.\d+)?)\s*(?:mm|millimeters?)?',  # fillets of 3 mm
            r'(\d+(?:\.\d+)?)\s*(?:mm|millimeters?)'  # simple number with mm unit
        ]
        
        for pattern in radius_patterns:
            radius_match = re.search(pattern, text, re.IGNORECASE)
            if radius_match:
                radius = float(radius_match.group(1))
                print(f"Debug: Extracted fillet radius: {radius}mm")
                break
        
        # If no radius specified, use default
        if radius is None:
            if hasattr(self, 'manufacturing') and self.manufacturing is not None:
                radius = self.manufacturing.fillet_radius
            else:
                radius = 2.0  # Default fillet radius
            print(f"Debug: Using default fillet radius: {radius}mm")
        else:
            print(f"Debug: Using specified fillet radius: {radius}mm")
        
        # Check if manufacturing_features is initialized
        if not hasattr(self, 'manufacturing') or self.manufacturing is None:
            print("Debug: manufacturing_features not initialized, initializing now")
            from manufacturing_features import ManufacturingFeatures
            self.manufacturing = ManufacturingFeatures()
            
        # Update the default fillet radius in the manufacturing features object
        if radius is not None:
            self.manufacturing.fillet_radius = radius
        
        # Check if specific edges are mentioned
        edges = None
        if 'all edges' in text.lower() or 'all' in text.lower():
            print("Debug: User requested all edges to be filleted")
            edges = None  # None means all edges in our implementation
        
        # Call the create_fillet method
        try:
            print(f"Debug: Creating fillet with radius={radius}, edges={edges}")
            result = self.manufacturing.create_fillet(radius, edges)
            print(f"Debug: Fillet result: {result}")
            
            # Ensure the document is updated
            import FreeCAD
            if FreeCAD.ActiveDocument:
                FreeCAD.ActiveDocument.recompute()
                
            return result
        except Exception as e:
            error_msg = f"Error creating fillet: {str(e)}"
            print(f"Debug: {error_msg}")
            return {'success': False, 'message': error_msg}
        
    def handle_draft(self, text):
        """Add draft angles"""
        selection = FreeCADGui.Selection.getSelection()
        if not selection:
            return {'success': False, 'message': 'Please select a part first'}
        
        # Extract angle if specified
        numbers = re.findall(r'\d+', text)
        angle = float(numbers[0]) if numbers else None
        
        return self.manufacturing.add_draft_angles(angle)  # Don't pass selection[0]

    def handle_ribs(self, text):
        """Add reinforcement ribs"""
        selection = FreeCADGui.Selection.getSelection()
        if not selection:
            return {'success': False, 'message': 'Please select a part first'}
        
        return self.manufacturing.add_ribs()  # Don't pass selection[0]
        
    def handle_shell(self, text):
        """Create a hollow shell"""
        selection = FreeCADGui.Selection.getSelection()
        if not selection:
            return {'success': False, 'message': 'Please select a part first'}
            
        # Extract thickness if specified
        thickness_match = re.search(r'(\d+\.?\d*)(?:\s*mm)?', text)
        thickness = float(thickness_match.group(1)) if thickness_match else 2.0
        
        return self.manufacturing.shell_part(thickness)  # Don't pass selection[0]
        
    def handle_extrude(self, text):
        """Handle extrusion commands"""
        print(f"Debug: handle_extrude called with text: {text}")
        
        # Extract distance with more patterns
        distance = None
        distance_patterns = [
            r'by\s+(\d+(?:\.\d+)?)\s*(?:mm|millimeters?)?',  # by 10mm
            r'(\d+(?:\.\d+)?)\s*(?:mm|millimeters?)\s*(?:deep|height|tall|thick)',  # 10mm deep
            r'to\s+(?:a\s+)?(?:depth|height|thickness)\s+of\s+(\d+(?:\.\d+)?)\s*(?:mm|millimeters?)?',  # to a depth of 10mm
            r'with\s+(?:a\s+)?(?:depth|height|thickness)\s+of\s+(\d+(?:\.\d+)?)\s*(?:mm|millimeters?)?'  # with a depth of 10mm
        ]
        
        for pattern in distance_patterns:
            distance_match = re.search(pattern, text, re.IGNORECASE)
            if distance_match:
                distance = float(distance_match.group(1))
                print(f"Debug: Extracted extrusion distance: {distance}mm")
                break
        
        # If no distance specified, use a default value
        if distance is None:
            distance = 10.0  # Default to 10mm
            print(f"Debug: Using default extrusion distance: {distance}mm")
        
        # Extract direction with more comprehensive patterns
        direction = None
        direction_patterns = {
            'up': [r'\b(?:up|upward|upwards|above|positive z)\b', r'\bin\s+(?:the\s+)?(?:positive|\+)\s*z\b'],
            'down': [r'\b(?:down|downward|downwards|below|negative z)\b', r'\bin\s+(?:the\s+)?(?:negative|-)\s*z\b'],
            'auto': [r'\b(?:normal|perpendicular|automatically|auto)\b', r'\bfollow(?:ing)?\s+(?:the\s+)?(?:face|surface)\s+normal\b']
        }
        
        for dir_name, patterns in direction_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text.lower()):
                    direction = dir_name
                    print(f"Debug: Extracted extrusion direction: {direction}")
                    break
            if direction:
                break
        
        # If no direction specified, use auto
        if direction is None:
            direction = 'auto'  # Default to automatic direction
            print(f"Debug: Using default extrusion direction: {direction}")
        
        # Check for selected faces
        try:
            import FreeCADGui
            selection = FreeCADGui.Selection.getSelectionEx()
            has_faces = False
            
            for sel_obj in selection:
                if sel_obj.SubElementNames and any('Face' in name for name in sel_obj.SubElementNames):
                    has_faces = True
                    break
            
            if not has_faces:
                print("Debug: No faces selected for extrusion")
                return {'success': False, 'message': 'Please select a face to extrude first'}
        except Exception as e:
            print(f"Debug: Error checking selection: {str(e)}")
        
        # Check if manufacturing_features is initialized
        if not hasattr(self, 'manufacturing') or self.manufacturing is None:
            print("Debug: manufacturing_features not initialized, initializing now")
            from manufacturing_features import ManufacturingFeatures
            self.manufacturing = ManufacturingFeatures()
        
        # Call the extrude_face method
        try:
            result = self.manufacturing.extrude_face(distance, direction)
            print(f"Debug: Extrusion result: {result}")
            
            # Ensure the document is updated
            import FreeCAD
            if FreeCAD.ActiveDocument:
                FreeCAD.ActiveDocument.recompute()
                
            return result
        except Exception as e:
            error_msg = f"Error during extrusion: {str(e)}"
            print(f"Debug: {error_msg}")
            return {'success': False, 'message': error_msg}
        
    def handle_gear(self, text):
        """Create a gear"""
        print("Debug: handle_gear called with text:", text)
        
        # Extract parameters
        numbers = re.findall(r'\d+', text)
        teeth = int(numbers[0]) if numbers else 20
        print("Debug: Extracted teeth count:", teeth)
        
        if 'module' in text:
            module_match = re.search(r'module\s*(\d+\.?\d*)', text)
            module = float(module_match.group(1)) if module_match else 2.0
        else:
            module = 2.0
        print("Debug: Using module:", module)
        
        # Extract width if specified
        width_match = re.search(r'width\s*(\d+\.?\d*)', text)
        width = float(width_match.group(1)) if width_match else 10.0
        print(f"Debug: Using width: {width}")
        
        # Create the gear
        return self.standard_parts.create_gear(teeth, module, width)
        
    def handle_bearing(self, text):
        """Create a bearing block"""
        print(f"Debug: handle_bearing called with text: {text}")
        
        # Extract bearing type if specified
        bearing_type = '608'  # Default bearing type
        if '6001' in text:
            bearing_type = '6001'
        elif '6201' in text:
            bearing_type = '6201'
        
        # Determine if mounting holes are needed
        mounting_holes = 'mount' in text.lower() or 'holes' in text.lower()
        
        print(f"Debug: Creating bearing block with type={bearing_type}, mounting_holes={mounting_holes}")
        
        # Call the correct method
        return self.standard_parts.create_bearing_block(bearing_type, mounting_holes)
    
    def handle_shaft(self, text):
        """Create a shaft"""
        # Extract parameters
        diameter_match = re.search(r'diameter\s*(\d+(?:\.\d+)?)', text)
        length_match = re.search(r'length\s*(\d+(?:\.\d+)?)', text)
        
        diameter = float(diameter_match.group(1)) if diameter_match else 10.0
        length = float(length_match.group(1)) if length_match else diameter * 5
        
        return self.standard_parts.create_shaft(diameter, length)
    
    def handle_moldable(self, text):
        """Make part moldable"""
        return self.optimization.make_moldable()
    
    def handle_printable(self, text):
        """Optimize for 3D printing"""
        return self.optimization.optimize_for_3d_printing()
    
    def handle_weight(self, text):
        """Reduce weight"""
        return self.optimization.reduce_weight()
    
    def handle_assembly(self, text):
        """Create an assembly"""
        result = self.assembly_gen.create_assembly(text)
        
        if result['success']:
            # Update context
            self.context.assembly_components = [
                comp[0] for comp in self.assembly_gen.components
            ]
        
        return result

    def handle_gearbox(self, text):
        """Create a gearbox assembly"""
        print(f"Debug: Handling gearbox command: {text}")
        
        # Make sure assembly generator is initialized
        if not self.assembly_gen:
            from assembly_generator import AssemblyGenerator
            self.assembly_gen = AssemblyGenerator(self.standard_parts)
            print("Debug: Created assembly generator for gearbox creation")
        
        # Process the command and create a gearbox
        result = self.assembly_gen.create_gearbox(text)
        
        if result and result.get('success'):
            print(f"Debug: Successfully created gearbox: {result.get('message')}")
            # Ensure the document is shown to the user
            if result.get('document'):
                FreeCAD.setActiveDocument(result['document'].Name)
                FreeCAD.ActiveDocument.recompute()
                if FreeCADGui:
                    FreeCADGui.SendMsgToActiveView("ViewFit")
                    FreeCADGui.updateGui()
        else:
            print(f"Debug: Failed to create gearbox: {result.get('message') if result else 'Unknown error'}")
        
        return result

    def handle_suggestions(self, text):
        """Get design suggestions"""
        suggestions = self.context.suggest_next_steps()
        
        if suggestions:
            msg = "Here are some suggestions:\n"
            for i, suggestion in enumerate(suggestions, 1):
                msg += f"{i}. {suggestion}\n"
        else:
            msg = "Try creating a part first, then I can suggest next steps."
        
        return {'success': True, 'message': msg}

    def handle_ai_design(self, text):
        """Use AI to create complex designs"""
        # Process with AI
        ai_result = self.ai_processor.process_advanced_command(
            text, 
            {
                'project': self.context.current_project,
                'material': self.context.material,
                'process': self.context.process
            }
        )
        
        # Execute based on AI interpretation
        if ai_result.get('intent') == 'create':
            if ai_result.get('object_type') == 'assembly':
                return self.handle_assembly(text)
            else:
                # Create part with AI parameters
                return self.create_from_ai_spec(ai_result)
        
        return {'success': False, 'message': 'Could not understand request'}

    def handle_analyze(self, text):
        """Analyze current design"""
        analysis = self.context.analyze_design_completeness()
        
        msg = f"Design Analysis:\n"
        msg += f"Overall Completeness: {analysis['overall_percentage']:.0f}%\n\n"
        
        msg += "Details:\n"
        for aspect, score in analysis['details'].items():
            msg += f"- {aspect.title()}: {score*100:.0f}%\n"
        
        if analysis['missing']:
            msg += "\nMissing elements:\n"
            for item in analysis['missing']:
                msg += f"• {item}\n"
        
        return {'success': True, 'message': msg}

    def create_from_ai_spec(self, ai_spec):
        """Create part from AI specification"""
        obj_type = ai_spec.get('object_type')
        params = ai_spec.get('parameters', {})
        features = ai_spec.get('features', [])
        
        # Create base object
        if obj_type == 'bracket':
            result = self.create_bracket(params)
        elif obj_type == 'gear':
            result = self.create_gear_from_params(params)
        elif obj_type == 'housing':
            result = self.create_housing(params)
        else:
            result = self.create_generic_part(params)
        
        # Add features
        if result['success'] and features:
            part = result.get('object')
            for feature in features:
                if feature == 'ribs':
                    self.manufacturing.add_ribs(part)
                elif feature == 'fillets':
                    self.manufacturing.add_fillets(part)
                elif feature == 'holes':
                    self.add_standard_holes(part, params)
        
        return result
        
    def is_complex_command(self, text):
        """Determine if command needs AI processing"""
        complex_indicators = [
            'assembly', 'mechanism', 'system',
            'for my', 'that fits', 'compatible with',
            'optimized', 'analyze', 'suggest',
            'with', 'including', 'having'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in complex_indicators)
    
    def set_cloud_client(self, cloud_client):
        """Set cloud client for AI processing"""
        if self.ai_processor:
            print(f"Debug: Setting cloud client to AI processor: {cloud_client is not None}")
            self.ai_processor.cloud_client = cloud_client
        else:
            print("Debug: AI processor not initialized yet, cannot set cloud client")
            # Initialize AI processor if needed
            from cloud_ai_processor import CloudAIProcessor
            self.ai_processor = CloudAIProcessor(cloud_client)
            print("Debug: Created new CloudAIProcessor with cloud client")
        
    def create_bracket(self, params):
        """Create a bracket with the given parameters"""
        length = params.get('length', 50)
        width = params.get('width', 30)
        height = params.get('height', 20)
        thickness = params.get('thickness', 5)
        
        # Use handle_create for basic shape
        result = self.handle_create(f"create bracket {length}x{width}x{height}")
        
        if result['success']:
            # Add the object to the result
            result['object'] = FreeCAD.ActiveDocument.ActiveObject
            
        return result
        
    def create_gear_from_params(self, params):
        """Create a gear with the given parameters"""
        teeth = params.get('teeth', 20)
        module = params.get('module', 2.0)
        width = params.get('thickness', 10.0)
        
        result = self.standard_parts.create_gear(teeth, module, width)
        
        if result['success']:
            result['object'] = FreeCAD.ActiveDocument.ActiveObject
            
        return result
        
    def create_housing(self, params):
        """Create a housing with the given parameters"""
        length = params.get('length', 100)
        width = params.get('width', 80)
        height = params.get('height', 40)
        thickness = params.get('thickness', 5)
        
        result = self.handle_create(f"create housing {length}x{width}x{height}")
        
        if result['success']:
            # Shell it to make it hollow
            obj = FreeCAD.ActiveDocument.ActiveObject
            self.manufacturing.shell_part(obj, thickness)
            result['object'] = obj
            
        return result
        
    def create_generic_part(self, params):
        """Create a generic part with the given parameters"""
        length = params.get('length', 50)
        width = params.get('width', 30)
        height = params.get('height', 20)
        shape = params.get('shape', 'box')
        
        result = self.handle_create(f"create {shape} {length}x{width}x{height}")
        
        if result['success']:
            result['object'] = FreeCAD.ActiveDocument.ActiveObject
            
        return result
        
    def add_standard_holes(self, part, params):
        """Add standard mounting holes to a part"""
        try:
            hole_diameter = params.get('hole_diameter', 5)
            hole_count = params.get('hole_count', 4)
            
            # Select the part
            FreeCADGui.Selection.clearSelection()
            FreeCADGui.Selection.addSelection(part)
            
            # Use manufacturing feature to add holes
            return self.manufacturing.add_holes(hole_diameter, hole_count)
        except Exception as e:
            print(f"Error adding standard holes: {str(e)}")
            return {'success': False, 'message': str(e)}
