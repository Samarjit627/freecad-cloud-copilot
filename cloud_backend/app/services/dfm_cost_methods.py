"""
DFM Cost Analysis Methods
Contains implementation of manufacturing cost estimation algorithms
"""
import math
from typing import Dict, List, Any, Optional

from ..models.dfm_models import (
    ProcessType, MaterialType, CADGeometry, CostAnalysis
)

def perform_cost_analysis(cad_geometry: CADGeometry, process: ProcessType, 
                         material: MaterialType, production_volume: int,
                         cost_models: Dict) -> Optional[CostAnalysis]:
    """
    Perform detailed manufacturing cost analysis
    
    Args:
        cad_geometry: CAD geometry data
        process: Target manufacturing process
        material: Target material
        production_volume: Production quantity
        cost_models: Cost models for different processes
        
    Returns:
        Detailed cost analysis
    """
    # Get cost model for the process
    cost_model = cost_models.get(process)
    if not cost_model:
        return None
    
    # Calculate material cost
    material_cost = calculate_material_cost(cad_geometry, material, cost_model)
    
    # Calculate labor cost
    labor_cost = calculate_labor_cost(cad_geometry, process, production_volume, cost_model)
    
    # Calculate tooling cost
    tooling_cost = calculate_tooling_cost(cad_geometry, process, cost_model)
    
    # Calculate setup cost
    setup_cost = cost_model.get("setup_cost", 0.0)
    
    # Calculate finishing cost (simplified)
    finishing_cost = 0.0
    if process == ProcessType.INJECTION_MOLDING:
        finishing_cost = 0.5  # $0.50 per part
    elif process == ProcessType.CNC_MILLING:
        finishing_cost = 2.0  # $2.00 per part
    
    # Calculate overhead cost (simplified)
    overhead_cost = (material_cost + labor_cost) * 0.2  # 20% of material and labor
    
    # Calculate total cost per part
    total_cost = material_cost + labor_cost
    if production_volume > 0:
        total_cost += tooling_cost / production_volume
        total_cost += setup_cost / production_volume
    total_cost += finishing_cost
    total_cost += overhead_cost
    
    # Apply volume discount
    volume_discount = get_volume_discount(production_volume, cost_model)
    total_cost *= volume_discount
    
    # Create cost analysis
    return CostAnalysis(
        cost_per_part=round(total_cost, 2),
        material_cost=round(material_cost, 2),
        labor_cost=round(labor_cost, 2),
        tooling_cost=round(tooling_cost, 2),
        setup_cost=round(setup_cost, 2),
        finishing_cost=round(finishing_cost, 2),
        overhead_cost=round(overhead_cost, 2)
    )

def calculate_material_cost(cad_geometry: CADGeometry, material: MaterialType, cost_model: Dict) -> float:
    """Calculate material cost based on volume and material type"""
    # Material cost rates ($/cm³)
    material_rates = {
        MaterialType.ABS: 0.05,
        MaterialType.PLA: 0.04,
        MaterialType.PETG: 0.06,
        MaterialType.NYLON: 0.08,
        MaterialType.POLYCARBONATE: 0.09,
        MaterialType.POM: 0.07,
        MaterialType.PEEK: 0.50,
        MaterialType.ALUMINUM: 0.15,
        MaterialType.STEEL: 0.10,
        MaterialType.STAINLESS_STEEL: 0.20,
        MaterialType.TITANIUM: 0.80,
        MaterialType.COPPER: 0.25,
        MaterialType.BRASS: 0.20,
        MaterialType.CARBON_FIBER: 0.40,
        MaterialType.GLASS_FIBER: 0.15
    }
    
    # Get material rate
    material_rate = material_rates.get(material, 0.05)  # Default to ABS rate
    
    # Apply process-specific material factor
    material_cost_factor = cost_model.get("material_cost_factor", 1.0)
    
    # Calculate material cost based on volume
    volume_cm3 = cad_geometry.volume / 1000.0  # Convert mm³ to cm³
    material_cost = volume_cm3 * material_rate * material_cost_factor
    
    # Add waste factor (10-30% depending on process)
    if ProcessType.INJECTION_MOLDING:
        waste_factor = 1.1  # 10% waste
    elif ProcessType.CNC_MILLING:
        waste_factor = 1.3  # 30% waste
    else:
        waste_factor = 1.2  # 20% waste
    
    return material_cost * waste_factor

def calculate_labor_cost(cad_geometry: CADGeometry, process: ProcessType, 
                        production_volume: int, cost_model: Dict) -> float:
    """Calculate labor cost based on process time and machine rate"""
    # Get machine rate
    machine_rate = cost_model.get("machine_rate", 60.0)  # $/hour
    
    # Calculate process time
    if process == ProcessType.INJECTION_MOLDING:
        # Injection molding cycle time calculation
        base_time = cost_model.get("cycle_time_base", 30.0)  # seconds
        volume_factor = cad_geometry.volume / 10000.0  # Adjust based on volume
        complexity_factor = 1.0 + (cad_geometry.faces or 0) / 100.0  # Adjust based on complexity
        
        cycle_time_seconds = base_time * volume_factor * complexity_factor
        cycle_time_hours = cycle_time_seconds / 3600.0
        
        # Labor cost per part
        labor_cost = cycle_time_hours * machine_rate
        
    elif process == ProcessType.CNC_MILLING:
        # CNC machining time calculation (simplified)
        base_time = 0.5  # hours
        volume_factor = cad_geometry.volume / 50000.0  # Adjust based on volume
        complexity_factor = 1.0 + (cad_geometry.faces or 0) / 50.0  # Adjust based on complexity
        
        machining_time_hours = base_time * volume_factor * complexity_factor
        
        # Labor cost per part
        labor_cost = machining_time_hours * machine_rate
        
    elif process == ProcessType.FDM_PRINTING:
        # 3D printing time calculation (simplified)
        volume_cm3 = cad_geometry.volume / 1000.0  # Convert mm³ to cm³
        print_speed = 15.0  # cm³/hour
        
        printing_time_hours = volume_cm3 / print_speed
        
        # Labor cost per part (less operator time needed)
        labor_cost = printing_time_hours * (machine_rate * 0.3)
        
    else:
        # Default calculation
        labor_cost = 10.0  # Default $10 per part
    
    return labor_cost

def calculate_tooling_cost(cad_geometry: CADGeometry, process: ProcessType, cost_model: Dict) -> float:
    """Calculate tooling cost based on part complexity and size"""
    if process == ProcessType.INJECTION_MOLDING:
        # Injection molding tooling cost
        base_cost = cost_model.get("tooling_base", 5000.0)
        complexity_factor = cost_model.get("tooling_complexity_factor", 1.0)
        
        # Adjust for part complexity
        faces = cad_geometry.faces or 50
        complexity_multiplier = 1.0 + (faces - 50) / 100.0
        complexity_multiplier = max(1.0, min(3.0, complexity_multiplier))
        
        # Adjust for part size
        bbox = cad_geometry.bounding_box
        max_dimension = max(bbox.length, bbox.width, bbox.height)
        size_multiplier = max_dimension / 100.0  # Normalized to 100mm
        size_multiplier = max(0.5, min(3.0, size_multiplier))
        
        tooling_cost = base_cost * complexity_multiplier * size_multiplier * complexity_factor
        
    elif process == ProcessType.CNC_MILLING:
        # CNC tooling cost (fixtures, custom tools)
        tooling_cost = cost_model.get("tooling_cost", 50.0)
        
        # Add programming cost
        programming_cost = cost_model.get("programming_cost", 200.0)
        
        tooling_cost += programming_cost
        
    else:
        # Default minimal tooling cost
        tooling_cost = 50.0
    
    return tooling_cost

def get_volume_discount(production_volume: int, cost_model: Dict) -> float:
    """Get volume discount factor based on production quantity"""
    volume_discounts = cost_model.get("volume_discounts", {})
    
    # Find the highest volume tier that's less than or equal to the production volume
    applicable_discount = 1.0
    applicable_volume = 0
    
    for volume, discount in volume_discounts.items():
        if production_volume >= volume and volume > applicable_volume:
            applicable_volume = volume
            applicable_discount = discount
    
    return applicable_discount
