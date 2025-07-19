"""
Intelligent part library with recommendations
"""

import json
import os

class SmartPartLibrary:
    """Smart library for standard and custom parts"""
    
    def __init__(self):
        self.standard_parts = self.load_standard_parts()
        self.custom_parts = []
        self.usage_history = []
        
    def load_standard_parts(self):
        """Load standard part definitions"""
        return {
            # Bearings
            '608': {
                'category': 'bearing',
                'type': 'ball',
                'specs': {'id': 8, 'od': 22, 'width': 7},
                'uses': ['skateboard', 'roller', 'light_load'],
                'load_rating': 1.4  # kN
            },
            '6001': {
                'category': 'bearing',
                'type': 'ball',
                'specs': {'id': 12, 'od': 28, 'width': 8},
                'uses': ['motor_shaft', 'medium_load'],
                'load_rating': 5.1
            },
            
            # Motors
            'NEMA17': {
                'category': 'motor',
                'type': 'stepper',
                'specs': {
                    'size': 42.3,
                    'length': 40,
                    'shaft': 5,
                    'mounting_holes': 31,
                    'torque': 0.4  # Nm
                },
                'uses': ['3d_printer', 'cnc', 'robotics']
            },
            
            # Fasteners
            'M3x10': {
                'category': 'screw',
                'type': 'socket_head',
                'specs': {
                    'diameter': 3,
                    'length': 10,
                    'head_diameter': 5.5,
                    'head_height': 3
                },
                'uses': ['general', 'electronics']
            },
            
            # Linear motion
            'LM8UU': {
                'category': 'linear_bearing',
                'type': 'ball_bushing',
                'specs': {
                    'id': 8,
                    'od': 15,
                    'length': 24
                },
                'uses': ['3d_printer', 'linear_rail']
            },
            
            # Timing belts
            'GT2_6mm': {
                'category': 'belt',
                'type': 'timing',
                'specs': {
                    'pitch': 2,
                    'width': 6,
                    'tooth_profile': 'GT2'
                },
                'uses': ['3d_printer', 'motion_control']
            }
        }
    
    def search_parts(self, query):
        """Search for parts by query"""
        query_lower = query.lower()
        results = []
        
        # Search in standard parts
        for part_id, part_data in self.standard_parts.items():
            score = 0
            
            # Check category
            if part_data['category'] in query_lower:
                score += 3
            
            # Check uses
            for use in part_data.get('uses', []):
                if use in query_lower:
                    score += 2
            
            # Check part ID
            if part_id.lower() in query_lower:
                score += 5
                
            if score > 0:
                results.append({
                    'id': part_id,
                    'data': part_data,
                    'score': score
                })
        
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:5]  # Top 5 results
    
    def recommend_parts(self, context):
        """Recommend parts based on context"""
        recommendations = []
        
        # Based on project type
        if context.get('project') == '3d_printer':
            recommendations.extend([
                ('NEMA17', 'Stepper motor for axes'),
                ('LM8UU', 'Linear bearings for smooth rods'),
                ('GT2_6mm', 'Timing belt for motion'),
                ('608', 'Bearings for idler pulleys')
            ])
        elif context.get('project') == 'robotics':
            recommendations.extend([
                ('NEMA17', 'Stepper motor for joints'),
                ('608', 'Bearings for rotating joints'),
                ('M3x10', 'Screws for assembly')
            ])
        
        # Based on recent parts
        if 'shaft' in str(context.get('recent_parts', [])):
            recommendations.append(('608', 'Bearing for shaft support'))
            
        if 'motor' in str(context.get('recent_parts', [])):
            recommendations.append(('shaft_coupling', 'To connect motor to shaft'))
        
        return recommendations[:4]
    
    def get_part_cad(self, part_id):
        """Generate CAD for standard part"""
        if part_id not in self.standard_parts:
            return None
            
        part_data = self.standard_parts[part_id]
        
        # Generate based on category
        if part_data['category'] == 'bearing':
            return self.create_bearing_cad(part_data)
        elif part_data['category'] == 'screw':
            return self.create_screw_cad(part_data)
        elif part_data['category'] == 'motor':
            return self.create_motor_cad(part_data)
        
        return None
    
    def create_bearing_cad(self, data):
        """Create bearing CAD"""
        import Part
        
        specs = data['specs']
        
        # Outer ring
        outer = Part.makeCylinder(specs['od']/2, specs['width'])
        
        # Inner ring
        inner = Part.makeCylinder(specs['id']/2, specs['width'])
        
        # Create bearing shape
        bearing = outer.cut(inner)
        
        # Add groove representation
        groove_r = (specs['od'] + specs['id']) / 4
        groove = Part.makeTorus(groove_r, specs['width']/4)
        groove.translate(FreeCAD.Vector(0, 0, specs['width']/2))
        
        bearing = bearing.cut(groove)
        
        return bearing
