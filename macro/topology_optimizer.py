"""
Topology optimization for weight reduction
"""

import FreeCAD
import Part
import math

class TopologyOptimizer:
    """Optimize part topology for weight/strength"""
    
    def __init__(self):
        self.safety_factor = 2.0
        self.min_thickness = 2.0
        
    def optimize_part(self, part, target_reduction=0.3, load_case=None):
        """Optimize part topology"""
        doc = FreeCAD.ActiveDocument
        
        try:
            if not hasattr(part, 'Shape'):
                return {'success': False, 'message': 'Invalid part'}
            
            # Get original properties
            original_volume = part.Shape.Volume
            bbox = part.Shape.BoundBox
            
            # Determine optimization strategy
            if self.is_plate_like(part):
                result = self.optimize_plate(part, target_reduction)
            elif self.is_beam_like(part):
                result = self.optimize_beam(part, target_reduction)
            else:
                result = self.optimize_generic(part, target_reduction)
            
            # Calculate actual reduction
            if result['success']:
                new_volume = result['object'].Shape.Volume
                actual_reduction = (original_volume - new_volume) / original_volume
                
                result['stats'] = {
                    'original_volume': original_volume / 1000,  # cm³
                    'new_volume': new_volume / 1000,
                    'reduction': actual_reduction * 100,  # %
                    'weight_saved': (original_volume - new_volume) / 1000 * 1.2  # grams (assuming plastic)
                }
            
            return result
            
        except Exception as e:
            return {'success': False, 'message': f'Optimization error: {str(e)}'}
    
    def is_plate_like(self, part):
        """Check if part is plate-like"""
        bbox = part.Shape.BoundBox
        dims = sorted([bbox.XLength, bbox.YLength, bbox.ZLength])
        
        # Plate if thinnest dimension is < 20% of others
        return dims[0] < dims[1] * 0.2
    
    def is_beam_like(self, part):
        """Check if part is beam-like"""
        bbox = part.Shape.BoundBox
        dims = sorted([bbox.XLength, bbox.YLength, bbox.ZLength])
        
        # Beam if longest dimension is > 3x others
        return dims[2] > dims[1] * 3
    
    def optimize_plate(self, part, target_reduction):
        """Optimize plate-like parts"""
        doc = FreeCAD.ActiveDocument
        bbox = part.Shape.BoundBox
        
        # Create honeycomb pattern
        optimized = part.Shape.copy()
        
        # Determine hex size based on plate size
        hex_size = min(bbox.XLength, bbox.YLength) / 10
        
        # Create honeycomb cuts
        holes = []
        rows = int(bbox.YLength / (hex_size * 1.5))
        cols = int(bbox.XLength / (hex_size * 1.73))
        
        for row in range(rows):
            for col in range(cols):
                x = col * hex_size * 1.73 + (hex_size * 0.86 if row % 2 else 0)
                y = row * hex_size * 1.5
                
                # Skip edges
                if (x > hex_size and x < bbox.XLength - hex_size and 
                    y > hex_size and y < bbox.YLength - hex_size):
                    
                    # Create hexagon
                    hex_hole = self.create_hexagon(hex_size * 0.8)
                    hex_hole.translate(FreeCAD.Vector(
                        bbox.XMin + x,
                        bbox.YMin + y,
                        bbox.ZMin
                    ))
                    
                    # Extrude through
                    hex_cut = hex_hole.extrude(FreeCAD.Vector(0, 0, bbox.ZLength))
                    holes.append(hex_cut)
        
        # Cut all holes
        for hole in holes:
            optimized = optimized.cut(hole)
        
        # Create result object
        opt_obj = doc.addObject("Part::Feature", "Optimized_Plate")
        opt_obj.Shape = optimized
        
        return {
            'success': True,
            'message': 'Created honeycomb optimization',
            'object': opt_obj,
            'pattern': 'honeycomb'
        }
    
    def optimize_beam(self, part, target_reduction):
        """Optimize beam-like parts"""
        doc = FreeCAD.ActiveDocument
        bbox = part.Shape.BoundBox
        
        # Create I-beam profile
        optimized = part.Shape.copy()
        
        # Determine which is the long axis
        if bbox.XLength > bbox.YLength and bbox.XLength > bbox.ZLength:
            long_axis = 'X'
            section_size = (bbox.YLength, bbox.ZLength)
        elif bbox.YLength > bbox.XLength and bbox.YLength > bbox.ZLength:
            long_axis = 'Y'
            section_size = (bbox.XLength, bbox.ZLength)
        else:
            long_axis = 'Z'
            section_size = (bbox.XLength, bbox.YLength)
        
        # Create web cutouts
        web_thickness = section_size[0] * 0.2
        flange_thickness = section_size[1] * 0.25
        
        # Create cutout shape
        cut_width = section_size[0] - 2 * web_thickness
        cut_height = section_size[1] - 2 * flange_thickness
        
        if cut_width > 0 and cut_height > 0:
            cutout = Part.makeBox(cut_width, cut_height, bbox.XLength * 0.8)
            
            # Position cutout
            if long_axis == 'X':
                cutout.translate(FreeCAD.Vector(
                    bbox.XMin + bbox.XLength * 0.1,
                    bbox.YMin + web_thickness,
                    bbox.ZMin + flange_thickness
                ))
            
            optimized = optimized.cut(cutout)
        
        # Create result
        opt_obj = doc.addObject("Part::Feature", "Optimized_Beam")
        opt_obj.Shape = optimized
        
        return {
            'success': True,
            'message': 'Created I-beam optimization',
            'object': opt_obj,
            'pattern': 'i-beam'
        }
    
    def optimize_generic(self, part, target_reduction):
        """Generic optimization using lattice"""
        doc = FreeCAD.ActiveDocument
        bbox = part.Shape.BoundBox
        
        # Create lattice structure
        optimized = part.Shape.copy()
        
        # Create grid of spherical cuts
        grid_size = min(bbox.XLength, bbox.YLength, bbox.ZLength) / 5
        sphere_radius = grid_size * 0.3
        
        cuts = []
        
        x_steps = int(bbox.XLength / grid_size)
        y_steps = int(bbox.YLength / grid_size)
        z_steps = int(bbox.ZLength / grid_size)
        
        for i in range(1, x_steps):
            for j in range(1, y_steps):
                for k in range(1, z_steps):
                    x = bbox.XMin + i * grid_size
                    y = bbox.YMin + j * grid_size
                    z = bbox.ZMin + k * grid_size
                    
                    # Check if inside part
                    point = FreeCAD.Vector(x, y, z)
                    if part.Shape.isInside(point, 0.1, True):
                        sphere = Part.makeSphere(sphere_radius)
                        sphere.translate(point)
                        cuts.append(sphere)
        
        # Apply cuts
        for cut in cuts[:int(len(cuts) * target_reduction)]:
            optimized = optimized.cut(cut)
        
        # Create result
        opt_obj = doc.addObject("Part::Feature", "Optimized_Lattice")
        opt_obj.Shape = optimized
        
        return {
            'success': True,
            'message': 'Created lattice optimization',
            'object': opt_obj,
            'pattern': 'lattice'
        }
    
    def create_hexagon(self, size):
        """Create hexagon shape"""
        import math
        
        angles = [i * 60 for i in range(6)]
        points = []
        
        for angle in angles:
            x = size * math.cos(math.radians(angle))
            y = size * math.sin(math.radians(angle))
            points.append(FreeCAD.Vector(x, y, 0))
        
        points.append(points[0])  # Close shape
        
        # Create wire
        lines = []
        for i in range(len(points) - 1):
            lines.append(Part.LineSegment(points[i], points[i+1]))
        
        wire = Part.Wire([line.toShape() for line in lines])
        return Part.Face(wire)
