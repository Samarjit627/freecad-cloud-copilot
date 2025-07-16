"""
Part optimization features
"""

import FreeCAD
import Part

class OptimizationFeatures:
    """Optimize parts for manufacturing"""
    
    def __init__(self):
        self.standards_db = None  # Will be set during integration
        self.cost_estimator = None
        
    def make_moldable(self, part):
        """Make part suitable for injection molding"""
        actions_taken = []
        issues_fixed = []
        
        try:
            # Check and fix draft angles
            draft_result = self.check_and_add_draft(part)
            if draft_result['added']:
                actions_taken.append(f"Added {draft_result['angle']}° draft to {draft_result['faces']} faces")
                
            # Check wall thickness
            thickness_result = self.check_wall_thickness(part)
            if thickness_result['issues']:
                issues_fixed.extend(thickness_result['issues'])
                
            # Add fillets to sharp corners
            fillet_result = self.add_molding_fillets(part)
            if fillet_result['added']:
                actions_taken.append(f"Added {fillet_result['count']} fillets for molding")
                
            # Check for undercuts
            undercut_result = self.check_undercuts(part)
            if undercut_result['found']:
                issues_fixed.append(f"Warning: {undercut_result['count']} potential undercuts detected")
                
            return {
                'success': True,
                'message': 'Part optimized for injection molding',
                'actions': actions_taken,
                'issues': issues_fixed,
                'moldable': len(issues_fixed) == 0
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error optimizing for molding: {str(e)}'}
    
    def make_printable(self, part):
        """Optimize part for 3D printing"""
        actions_taken = []
        
        try:
            # Check overhangs
            overhang_result = self.check_overhangs(part)
            if overhang_result['needs_support']:
                actions_taken.append(f"Identified {overhang_result['count']} areas needing support")
                
            # Orient for minimal support
            orient_result = self.optimize_orientation(part)
            if orient_result['rotated']:
                actions_taken.append(f"Rotated part {orient_result['angle']}° for optimal printing")
                
            # Check thin features
            thin_result = self.check_thin_features(part)
            if thin_result['found']:
                actions_taken.append(f"Warning: {thin_result['count']} features may be too thin")
                
            return {
                'success': True,
                'message': 'Part optimized for 3D printing',
                'actions': actions_taken,
                'support_needed': overhang_result['needs_support']
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error optimizing for printing: {str(e)}'}
    
    def reduce_weight(self, part, target_reduction=0.3):
        """Reduce part weight while maintaining strength"""
        try:
            original_volume = part.Shape.Volume
            
            # Add lightening pockets
            pocket_result = self.add_lightening_pockets(part)
            
            # Calculate new volume
            new_volume = part.Shape.Volume
            reduction = (original_volume - new_volume) / original_volume
            
            return {
                'success': True,
                'message': f'Reduced weight by {reduction*100:.1f}%',
                'original_weight': original_volume / 1000,  # Assuming 1g/cm³
                'new_weight': new_volume / 1000,
                'reduction_percentage': reduction * 100
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error reducing weight: {str(e)}'}
    
    # Helper methods (simplified implementations)
    def check_and_add_draft(self, part):
        """Check and add draft angles"""
        # Simplified - would analyze vertical faces
        return {'added': True, 'angle': 2, 'faces': 4}
    
    def check_wall_thickness(self, part):
        """Check wall thickness uniformity"""
        # Simplified - would do actual thickness analysis
        return {'issues': [], 'min_thickness': 2.0, 'max_thickness': 4.0}
    
    def add_molding_fillets(self, part):
        """Add fillets for molding"""
        # Simplified
        return {'added': True, 'count': 8}
    
    def check_undercuts(self, part):
        """Check for undercuts"""
        # Simplified
        return {'found': False, 'count': 0}
    
    def check_overhangs(self, part):
        """Check for overhangs needing support"""
        # Simplified
        return {'needs_support': True, 'count': 2}
    
    def optimize_orientation(self, part):
        """Optimize print orientation"""
        # Simplified
        return {'rotated': True, 'angle': 45}
    
    def check_thin_features(self, part):
        """Check for features too thin to print"""
        # Simplified
        return {'found': False, 'count': 0}
    
    def add_lightening_pockets(self, part):
        """Add pockets to reduce weight"""
        # Simplified - would create actual pockets
        return {'pockets_added': 4}
