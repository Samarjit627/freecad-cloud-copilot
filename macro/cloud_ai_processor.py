"""
Cloud AI processing for advanced understanding
"""

import json
import re

class CloudAIProcessor:
    """Process natural language using cloud AI"""
    
    def __init__(self, cloud_client=None):
        self.cloud_client = cloud_client
        self.context_memory = []
        print(f"Debug: CloudAIProcessor initialized with client: {cloud_client is not None}")
        
    def process_advanced_command(self, text, context=None):
        """Process command with cloud AI"""
        if self.cloud_client and self.cloud_client.connected:
            return self.cloud_process(text, context)
        else:
            return self.local_process(text, context)
    
    def cloud_process(self, text, context):
        """Use cloud AI for processing"""
        try:
            if not self.cloud_client:
                print("Debug: No cloud client available, falling back to local processing")
                return self.local_process(text, context)
                
            # Build prompt with context
            prompt = self.build_ai_prompt(text, context)
            
            # Query cloud AI with fallback mechanism
            print(f"Debug: Using cloud client to process: {text}")
            
            # Try multiple endpoints with fallback
            endpoints = ["api/cad", "cad-assistant", "api/analysis/cad", "api/chat"]
            response = None
            last_error = None
            
            for endpoint in endpoints:
                try:
                    print(f"Debug: Trying endpoint: {endpoint}")
                    response = self.cloud_client.query_agent(endpoint, prompt)
                    print(f"Debug: Successfully used endpoint: {endpoint}")
                    break
                except Exception as e:
                    last_error = e
                    print(f"Debug: Endpoint {endpoint} failed: {e}")
            
            if response is None:
                print(f"Debug: All endpoints failed, last error: {last_error}")
                return self.local_process(text, context)
            
            # Parse response
            if isinstance(response, str):
                try:
                    parsed = json.loads(response)
                    return parsed
                except:
                    # Fallback parsing
                    return self.parse_text_response(response)
            else:
                return response
                
        except Exception as e:
            print(f"Cloud AI error: {e}")
            return self.local_process(text, context)
    
    def build_ai_prompt(self, text, context):
        """Build comprehensive prompt for AI"""
        prompt = f"""
        Analyze this CAD design request and provide structured response:
        
        Request: "{text}"
        
        Context:
        - Current project: {context.get('project', 'unknown')}
        - Manufacturing process: {context.get('process', 'any')}
        - Material: {context.get('material', 'any')}
        - Previous commands: {self.get_recent_context()}
        
        Provide response as JSON with:
        1. intent: Primary action (create/modify/analyze/optimize)
        2. object_type: What to create/modify
        3. parameters: Specific dimensions and properties
        4. features: Additional features to add
        5. constraints: Design constraints
        6. suggestions: Related suggestions
        
        If creating an assembly, include:
        - components: List of parts needed
        - relationships: How parts connect
        - specifications: Key dimensions
        
        Be specific with dimensions and standard part specifications.
        """
        
        return prompt
    
    def local_process(self, text, context):
        """Local processing with pattern matching"""
        text_lower = text.lower()
        print(f"Debug: Using local processing for: {text}")
        
        # Complex pattern matching
        patterns = {
            'bracket_with_ribs': r'bracket.*(?:with|having|including).*ribs',
            'gear_with_keyway': r'gear.*(?:with|having).*keyway',
            'optimized_part': r'(?:optimize|improve|strengthen).*for.*(?:weight|strength|cost)',
            'assembly_with_motors': r'(?:assembly|mechanism).*(?:with|using).*motor',
            'custom_enclosure': r'enclosure.*(?:for|to fit|housing).*(\d+).*x.*(\d+)',
            'gearbox': r'(?:create|make|design).*(?:gearbox|gear box|transmission).*(?:with|having|using).*(?:\d+:\d+|\d+:\d+\.\d+|\d+\.\d+:\d+|\d+\.\d+:\d+\.\d+).*(?:reduction|ratio)',
            # Enhanced fillet patterns to catch more variations
            'fillet': r'(?:add|apply|create|make).*(?:fillet|fillets|round|rounding).*(?:with|having|using|of|radius|=)?.*(?:\d+(?:\.\d+)?)?(?:\s*mm)?',
            'fillet_simple': r'(?:fillet|round).*(?:edge|edges|corner|corners)',
            'fillet_all': r'(?:fillet|round).*(?:all|every).*(?:edge|corner)',
            'fillet_radius': r'(?:radius|r)\s*[=:]\s*(\d+(?:\.\d+)?)',
        }
        
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, text_lower):
                return self.handle_complex_pattern(pattern_name, text)
        
        # Default parsing
        return {
            'intent': 'create',
            'object_type': self.extract_object_type(text),
            'parameters': self.extract_parameters(text),
            'features': [],
            'constraints': []
        }
    
    def handle_complex_pattern(self, pattern_name, text):
        """Handle complex command patterns"""
        text_lower = text.lower()
        
        if pattern_name == 'bracket_with_ribs':
            return {
                'intent': 'create',
                'object_type': 'bracket',
                'parameters': self.extract_parameters(text),
                'features': ['ribs', 'fillets', 'mounting_holes'],
                'constraints': ['moldable']
            }
        elif pattern_name == 'gear_with_keyway':
            params = self.extract_parameters(text)
            return {
                'intent': 'create',
                'object_type': 'gear',
                'parameters': params,
                'features': ['keyway', 'set_screw_hole'],
                'constraints': []
            }
        elif pattern_name == 'optimized_part':
            return {
                'intent': 'optimize',
                'object_type': self.extract_object_type(text) or 'part',
                'parameters': self.extract_parameters(text),
                'features': [],
                'constraints': ['lightweight', 'high_strength'],
                'optimization_target': self.extract_optimization_target(text)
            }
        elif pattern_name == 'assembly_with_motors':
            return {
                'intent': 'create',
                'object_type': 'assembly',
                'parameters': self.extract_parameters(text),
                'features': ['motors', 'mounts', 'fasteners'],
                'components': ['motor', 'frame', 'connectors'],
                'relationships': ['motor_to_frame']
            }
        elif pattern_name == 'custom_enclosure':
            match = re.search(r'enclosure.*(?:for|to fit|housing).*(\d+).*x.*(\d+)', text_lower)
            params = self.extract_parameters(text)
            if match and 'length' not in params:
                params['length'] = float(match.group(1))
                params['width'] = float(match.group(2))
            
            return {
                'intent': 'create',
                'object_type': 'enclosure',
                'parameters': params,
                'features': ['ventilation', 'mounting_tabs', 'cable_entries'],
                'constraints': ['manufacturable']
            }
            
        elif pattern_name == 'gearbox':
            # Extract ratio from text
            ratio_pattern = r'(?:\d+:\d+|\d+:\d+\.\d+|\d+\.\d+:\d+|\d+\.\d+:\d+\.\d+)'
            ratio_match = re.search(ratio_pattern, text)
            ratio = ratio_match.group(0) if ratio_match else "3:1"  # Default ratio
            
            print(f"Debug: Extracted ratio: {ratio}")
            
            # Extract other parameters
            parameters = {}
            
            # Check for module size
            module_match = re.search(r'module\s*[=:]?\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
            if module_match:
                parameters['module'] = float(module_match.group(1))
            
            # Check for number of teeth
            teeth_match = re.search(r'(\d+)\s*teeth', text, re.IGNORECASE)
            if teeth_match:
                parameters['teeth'] = int(teeth_match.group(1))
            
            print(f"Debug: Extracted parameters: {parameters}")
            
            return {
                'intent': 'create',
                'object_type': 'gearbox',
                'parameters': parameters,
                'features': [{'type': 'ratio', 'value': ratio}],
                'components': [
                    {'type': 'gear', 'role': 'input'},
                    {'type': 'gear', 'role': 'output'}
                ],
                'relationships': [
                    {'type': 'ratio', 'value': ratio, 'between': ['input', 'output']}
                ]
            }
        
        elif pattern_name in ['fillet', 'fillet_all', 'fillet_simple', 'fillet_radius']:
            # Extract radius from text
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
            
            # Default radius if not specified
            if radius is None:
                radius = 2.0
                print(f"Debug: Using default fillet radius: {radius}mm")
            
            # Check if all edges are mentioned
            all_edges = pattern_name == 'fillet_all' or 'all' in text.lower() or 'every' in text.lower()
            
            print(f"Debug: Local pattern matched for fillet command. Pattern: {pattern_name}, Radius: {radius}mm, All edges: {all_edges}")
            
            # Return a result that will be directly handled by the fillet handler
            return {
                'intent': 'modify',
                'command': 'fillet',  # This will trigger the fillet handler
                'object_type': 'fillet',
                'parameters': {'radius': radius, 'all_edges': all_edges},
                'features': [{'type': 'radius', 'value': radius}],
                'selection': 'edges' if not all_edges else 'all_edges'
            }   # Default fallback
        return {
            'intent': 'create',
            'object_type': self.extract_object_type(text),
            'parameters': self.extract_parameters(text),
            'features': [],
            'constraints': []
        }
    
    def extract_object_type(self, text):
        """Extract what type of object to create"""
        objects = ['bracket', 'gear', 'housing', 'enclosure', 'mount', 
                  'plate', 'shaft', 'spacer', 'frame', 'support']
        
        text_lower = text.lower()
        for obj in objects:
            if obj in text_lower:
                return obj
        return 'part'
    
    def extract_parameters(self, text):
        """Extract dimensional parameters"""
        params = {}
        
        # Extract dimensions (100x50x20 format)
        dim_match = re.search(r'(\d+)\s*x\s*(\d+)(?:\s*x\s*(\d+))?', text)
        if dim_match:
            params['length'] = float(dim_match.group(1))
            params['width'] = float(dim_match.group(2))
            if dim_match.group(3):
                params['height'] = float(dim_match.group(3))
        
        # Extract individual measurements
        patterns = {
            'diameter': r'(?:diameter|dia|ø)\s*[:=]?\s*(\d+(?:\.\d+)?)',
            'radius': r'radius\s*[:=]?\s*(\d+(?:\.\d+)?)',
            'thickness': r'(?:thickness|thick)\s*[:=]?\s*(\d+(?:\.\d+)?)',
            'teeth': r'(\d+)\s*teeth',
            'module': r'module\s*[:=]?\s*(\d+(?:\.\d+)?)',
        }
        
        for param, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                params[param] = float(match.group(1))
        
        return params
    
    def extract_optimization_target(self, text):
        """Extract optimization target from text"""
        text_lower = text.lower()
        
        if 'weight' in text_lower or 'lighter' in text_lower:
            return 'weight_reduction'
        elif 'strength' in text_lower or 'stronger' in text_lower:
            return 'strength_increase'
        elif 'cost' in text_lower or 'cheaper' in text_lower:
            return 'cost_reduction'
        elif 'thermal' in text_lower or 'heat' in text_lower:
            return 'thermal_performance'
        else:
            return 'general_optimization'
    
    def parse_text_response(self, response):
        """Parse text response when JSON parsing fails"""
        result = {
            'intent': 'create',
            'object_type': 'part',
            'parameters': {},
            'features': [],
            'constraints': []
        }
        
        # Try to extract key information from text
        intent_match = re.search(r'intent:?\s*(\w+)', response, re.IGNORECASE)
        if intent_match:
            result['intent'] = intent_match.group(1).lower()
            
        object_match = re.search(r'object_?type:?\s*(\w+)', response, re.IGNORECASE)
        if object_match:
            result['object_type'] = object_match.group(1).lower()
            
        # Extract parameters
        param_section = re.search(r'parameters?:?\s*\{([^}]+)\}', response)
        if param_section:
            param_text = param_section.group(1)
            param_matches = re.findall(r'[\'"]*(\w+)[\'"]*\s*:\s*(\d+(?:\.\d+)?)', param_text)
            for key, value in param_matches:
                result['parameters'][key] = float(value)
                
        # Extract features
        feature_match = re.search(r'features:?\s*\[([^\]]+)\]', response)
        if feature_match:
            features_text = feature_match.group(1)
            features = re.findall(r'[\'"]*([^\'",]+)[\'",]*', features_text)
            result['features'] = [f.strip() for f in features if f.strip()]
            
        return result
    
    def get_recent_context(self):
        """Get recent command context"""
        return self.context_memory[-5:] if self.context_memory else []
    
    def add_to_context(self, command, result):
        """Add command to context memory"""
        self.context_memory.append({
            'command': command,
            'result': result['success'],
            'type': result.get('object_type', 'unknown')
        })
