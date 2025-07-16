"""
Simple Cost Estimation
"""

class LiveCostEstimator:
    """Basic cost estimation"""
    
    def __init__(self):
        self.process_costs = {
            'injection_molding': {'setup': 5000, 'per_part': 0.50},
            'cnc_milling': {'setup': 200, 'per_hour': 75},
            '3d_printing': {'setup': 10, 'per_gram': 0.10}
        }
        
    def estimate(self, part, process='auto', quantity=100):
        """Estimate cost"""
        try:
            volume = part.Shape.Volume / 1000  # cm³
        except:
            volume = 100
            
        # Simple estimation
        if process == 'injection_molding':
            total = 5000 + (0.50 * quantity)
        elif process == 'cnc_milling':
            total = 200 + (volume * 0.1 * quantity)
        else:  # 3D printing
            total = 10 + (volume * 1.04 * 0.10 * quantity)
            
        return {
            'process': process,
            'quantity': quantity,
            'unit_cost': round(total / quantity, 2),
            'total_cost': round(total, 2)
        }
