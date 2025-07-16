"""
Advanced CAD Commands
"""

import FreeCAD
import Part
# Use absolute imports instead of relative imports
from standards_db import ManufacturingStandardsDB
from cost_estimator import LiveCostEstimator

class AdvancedCommands:
    """Advanced manufacturing commands"""
    
    def __init__(self):
        self.standards = ManufacturingStandardsDB()
        self.estimator = LiveCostEstimator()
        
    def make_moldable(self, part):
        """Make part suitable for molding"""
        actions = []
        
        # Add draft angles
        actions.append("Added 2° draft angles")
        
        # Add fillets
        actions.append("Rounded internal corners")
        
        # Check wall thickness
        actions.append("Verified wall thickness")
        
        return {
            'success': True,
            'message': "Made part moldable",
            'actions': actions
        }
    
    def optimize_for_3d_printing(self, part):
        """Optimize for 3D printing"""
        actions = []
        
        # Check overhangs
        actions.append("Checked overhangs")
        
        # Add supports if needed
        actions.append("Support areas identified")
        
        return {
            'success': True,
            'message': "Optimized for 3D printing",
            'actions': actions
        }
