"""
Design context management for intelligent suggestions
"""

import json
from datetime import datetime

class DesignContextManager:
    """Manage design context and provide intelligent suggestions"""
    
    def __init__(self):
        self.current_project = None
        self.parts_created = []
        self.assembly_components = []
        self.design_intent = None
        self.constraints = []
        self.material = None
        self.process = None
        
    def update_context(self, **kwargs):
        """Update context with new information"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def add_created_part(self, part_info):
        """Track created parts"""
        self.parts_created.append({
            'type': part_info.get('type'),
            'name': part_info.get('name'),
            'timestamp': datetime.now(),
            'specs': part_info.get('specs', {})
        })
    
    def suggest_next_steps(self):
        """Suggest next design steps based on context"""
        suggestions = []
        
        # Based on recent parts
        if self.parts_created:
            last_part = self.parts_created[-1]
            
            if last_part['type'] == 'gear':
                suggestions.extend([
                    "Create a matching gear for this one",
                    "Add a shaft for this gear",
                    "Create a gearbox housing",
                    "Add keyway or set screw"
                ])
            elif last_part['type'] == 'bracket':
                suggestions.extend([
                    "Add mounting holes",
                    "Create matching bracket for other side",
                    "Add reinforcement ribs",
                    "Optimize for weight"
                ])
            elif last_part['type'] == 'housing':
                suggestions.extend([
                    "Add ventilation slots",
                    "Create internal mounting points",
                    "Add cable management features",
                    "Design a matching lid"
                ])
        
        # Based on project type
        if self.current_project == 'robotics':
            suggestions.extend([
                "Add motor mounts",
                "Create sensor brackets",
                "Design cable guides",
                "Add battery compartment"
            ])
        elif self.current_project == '3d_printer':
            suggestions.extend([
                "Create carriage system",
                "Add belt tensioners",
                "Design hotend mount",
                "Create filament guide"
            ])
        
        # Based on assembly
        if len(self.assembly_components) > 1:
            suggestions.extend([
                "Add fasteners between components",
                "Create alignment features",
                "Add assembly jigs",
                "Generate bill of materials"
            ])
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def analyze_design_completeness(self):
        """Analyze if design is complete"""
        completeness = {
            'mechanical': self.check_mechanical_completeness(),
            'manufacturing': self.check_manufacturing_readiness(),
            'assembly': self.check_assembly_completeness(),
            'documentation': self.check_documentation_status()
        }
        
        overall = sum(completeness.values()) / len(completeness) * 100
        
        return {
            'overall_percentage': overall,
            'details': completeness,
            'missing': self.identify_missing_elements()
        }
    
    def check_mechanical_completeness(self):
        """Check mechanical design completeness"""
        score = 0.0
        
        # Check for basic structure
        if any(p['type'] in ['housing', 'frame', 'bracket'] for p in self.parts_created):
            score += 0.3
        
        # Check for motion elements
        if any(p['type'] in ['gear', 'bearing', 'shaft'] for p in self.parts_created):
            score += 0.3
        
        # Check for fastening
        if any('hole' in str(p.get('specs', {})) for p in self.parts_created):
            score += 0.2
        
        # Check for features
        if any('fillet' in str(p.get('specs', {})) for p in self.parts_created):
            score += 0.2
        
        return score
    
    def check_manufacturing_readiness(self):
        """Check if design is ready for manufacturing"""
        score = 0.0
        
        if self.material:
            score += 0.25
        
        if self.process:
            score += 0.25
        
        # Check for DFM features
        if any('draft' in str(p.get('specs', {})) for p in self.parts_created):
            score += 0.25
        
        if any('fillet' in str(p.get('specs', {})) for p in self.parts_created):
            score += 0.25
        
        return score
    
    def check_assembly_completeness(self):
        """Check assembly completeness"""
        if not self.assembly_components:
            return 0.0
        
        score = 0.3  # Has components
        
        # Check for fasteners
        if any('fastener' in c.lower() for c in self.assembly_components):
            score += 0.3
        
        # Check for alignment features
        if len(self.assembly_components) > 3:
            score += 0.4
        
        return score
    
    def check_documentation_status(self):
        """Check documentation completeness"""
        # Simplified - would check for drawings, BOM, etc.
        return 0.5
    
    def identify_missing_elements(self):
        """Identify what's missing from the design"""
        missing = []
        
        if not self.material:
            missing.append("Material selection")
        
        if not self.process:
            missing.append("Manufacturing process selection")
        
        if not any(p['type'] == 'housing' for p in self.parts_created):
            missing.append("Enclosure or housing")
        
        if self.assembly_components and len(self.assembly_components) > 1:
            if not any('fastener' in c.lower() for c in self.assembly_components):
                missing.append("Fasteners for assembly")
        
        return missing
    
    def export_context(self):
        """Export context for saving/sharing"""
        return {
            'project': self.current_project,
            'parts': self.parts_created,
            'assembly': self.assembly_components,
            'material': self.material,
            'process': self.process,
            'constraints': self.constraints,
            'timestamp': datetime.now().isoformat()
        }
    
    def import_context(self, context_data):
        """Import saved context"""
        self.current_project = context_data.get('project')
        self.parts_created = context_data.get('parts', [])
        self.assembly_components = context_data.get('assembly', [])
        self.material = context_data.get('material')
        self.process = context_data.get('process')
        self.constraints = context_data.get('constraints', [])
