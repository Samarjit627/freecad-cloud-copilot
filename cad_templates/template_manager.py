import os
import importlib.util
import inspect
import FreeCAD as App

class TemplateManager:
    """
    Manages CAD templates and provides a unified interface to create different types of parts.
    """
    
    def __init__(self):
        self.templates = {}
        self.template_dir = os.path.dirname(os.path.abspath(__file__))
        self.load_templates()
    
    def load_templates(self):
        """Load all available templates from the template directory"""
        print(f"Loading templates from {self.template_dir}")
        
        # Get all Python files in the template directory
        template_files = [f for f in os.listdir(self.template_dir) 
                         if f.endswith('_template.py')]
        
        for file in template_files:
            try:
                # Extract template name from filename
                template_name = file.replace('_template.py', '')
                
                # Load the module
                module_path = os.path.join(self.template_dir, file)
                spec = importlib.util.spec_from_file_location(template_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find the create_* function
                create_func = None
                for name, obj in inspect.getmembers(module):
                    if name.startswith('create_') and inspect.isfunction(obj):
                        create_func = obj
                        break
                
                if create_func:
                    self.templates[template_name] = create_func
                    print(f"Loaded template: {template_name}")
                else:
                    print(f"No create_* function found in {file}")
                    
            except Exception as e:
                print(f"Error loading template {file}: {e}")
        
        print(f"Loaded {len(self.templates)} templates")
    
    def list_templates(self):
        """Return a list of available templates"""
        return list(self.templates.keys())
    
    def get_template_parameters(self, template_name):
        """Get the parameters for a specific template"""
        if template_name not in self.templates:
            return None
        
        # Get the function signature
        sig = inspect.signature(self.templates[template_name])
        params = {}
        
        # Extract parameter names and default values
        for name, param in sig.parameters.items():
            if name != 'doc':  # Skip the doc parameter
                if param.default != inspect.Parameter.empty:
                    params[name] = param.default
                else:
                    params[name] = None
        
        return params
    
    def create_part(self, template_name, doc=None, **kwargs):
        """Create a part using the specified template and parameters"""
        if template_name not in self.templates:
            print(f"Template {template_name} not found")
            return None
        
        try:
            # Create a new document if not provided
            if doc is None:
                doc = App.newDocument(template_name.capitalize())
            
            # Call the template function with the provided parameters
            return self.templates[template_name](doc=doc, **kwargs)
            
        except Exception as e:
            print(f"Error creating part with template {template_name}: {e}")
            return None
    
    def parse_text_request(self, text):
        """
        Parse a natural language request to determine the template and parameters.
        
        This is a simple implementation that looks for keywords and numbers.
        A more sophisticated implementation would use NLP techniques.
        """
        text = text.lower()
        template_name = None
        params = {}
        
        # Check for template type
        if 'bracket' in text:
            template_name = 'bracket'
        elif 'enclosure' in text or 'box' in text or 'case' in text:
            template_name = 'enclosure'
        elif 'gear' in text or 'cog' in text:
            template_name = 'gear'
        elif 'bottle' in text or 'container' in text:
            template_name = 'water_bottle'
        
        if not template_name:
            return None, {}
        
        # Get default parameters
        default_params = self.get_template_parameters(template_name)
        if not default_params:
            return template_name, {}
        
        # Extract dimensions
        import re
        
        # Look for dimensions like "100mm x 50mm x 25mm"
        dim_pattern = r'(\d+)\s*mm\s*x\s*(\d+)\s*mm\s*x\s*(\d+)\s*mm'
        dim_match = re.search(dim_pattern, text)
        
        if dim_match and template_name in ['bracket', 'enclosure']:
            if template_name == 'bracket':
                params['length'] = float(dim_match.group(1))
                params['width'] = float(dim_match.group(2))
                params['height'] = float(dim_match.group(3))
            elif template_name == 'enclosure':
                params['length'] = float(dim_match.group(1))
                params['width'] = float(dim_match.group(2))
                params['height'] = float(dim_match.group(3))
        
        # Extract specific parameters based on template
        if template_name == 'gear':
            # Look for teeth count
            teeth_match = re.search(r'(\d+)\s*teeth', text)
            if teeth_match:
                params['teeth'] = int(teeth_match.group(1))
            
            # Look for module
            module_match = re.search(r'module\s*(\d+\.?\d*)', text)
            if module_match:
                params['module'] = float(module_match.group(1))
            
            # Look for bore diameter
            bore_match = re.search(r'bore\s*(\d+\.?\d*)', text)
            if bore_match:
                params['bore_diameter'] = float(bore_match.group(1))
        
        elif template_name == 'bracket':
            # Look for thickness
            thickness_match = re.search(r'thickness\s*(\d+\.?\d*)', text)
            if thickness_match:
                params['thickness'] = float(thickness_match.group(1))
            
            # Check for reinforcement
            params['reinforcement'] = 'reinforced' in text or 'reinforcement' in text
        
        elif template_name == 'enclosure':
            # Look for wall thickness
            wall_match = re.search(r'wall\s*thickness\s*(\d+\.?\d*)', text)
            if wall_match:
                params['wall_thickness'] = float(wall_match.group(1))
            
            # Check for features
            params['include_lid'] = not ('no lid' in text or 'without lid' in text)
            params['include_mounting_holes'] = not ('no holes' in text or 'without holes' in text)
            params['include_ventilation'] = 'vent' in text
            params['include_cable_cutout'] = 'cable' in text or 'cutout' in text
        
        elif template_name == 'water_bottle':
            # Look for volume in ml
            volume_match = re.search(r'(\d+)\s*ml', text)
            if volume_match:
                params['volume'] = float(volume_match.group(1))
            
            # Look for wall thickness
            wall_match = re.search(r'wall\s*thickness\s*(\d+\.?\d*)', text)
            if wall_match:
                params['wall_thickness'] = float(wall_match.group(1))
        
        return template_name, params

# Singleton instance
_instance = None

def get_template_manager():
    """Get the singleton instance of the TemplateManager"""
    global _instance
    if _instance is None:
        _instance = TemplateManager()
    return _instance

if __name__ == "__main__":
    # Test the template manager
    manager = get_template_manager()
    print("Available templates:", manager.list_templates())
    
    # Test parsing a request
    template, params = manager.parse_text_request("Create a 100mm x 50mm x 25mm enclosure with ventilation")
    print(f"Parsed request: template={template}, params={params}")
