"""
DFM Process Evaluation Methods
Contains implementation of manufacturing process evaluation algorithms
"""
import math
from typing import Dict, List, Any, Optional, Tuple

from ..models.dfm_models import (
    ProcessType, MaterialType, CADGeometry, ProcessSuitability
)

def evaluate_process_suitability(cad_geometry: CADGeometry, process: ProcessType,
                               material: MaterialType, production_volume: int,
                               manufacturability_score: float,
                               cost_models: Dict, material_properties: Dict) -> ProcessSuitability:
    """
    Evaluate suitability of a manufacturing process for the given part
    
    Args:
        cad_geometry: CAD geometry data
        process: Target manufacturing process
        material: Target material
        production_volume: Production quantity
        manufacturability_score: Overall manufacturability score
        cost_models: Cost models for different processes
        material_properties: Material properties
        
    Returns:
        Process suitability evaluation
    """
    # Check material compatibility with process
    material_props = material_properties.get(material, {})
    compatible_processes = material_props.get("compatible_processes", [])
    
    # Calculate suitability score
    suitability_score = manufacturability_score
    
    # Adjust score based on material compatibility
    if process not in compatible_processes:
        suitability_score *= 0.7  # 30% penalty for incompatible material
    
    # Adjust score based on production volume
    volume_suitability = calculate_volume_suitability(process, production_volume)
    suitability_score *= volume_suitability
    
    # Adjust score based on part size
    size_suitability = calculate_size_suitability(cad_geometry, process)
    suitability_score *= size_suitability
    
    # Ensure score is within range
    suitability_score = max(0.0, min(100.0, suitability_score))
    
    # Determine manufacturability rating
    if suitability_score >= 90.0:
        manufacturability = "excellent"
    elif suitability_score >= 75.0:
        manufacturability = "good"
    elif suitability_score >= 50.0:
        manufacturability = "fair"
    else:
        manufacturability = "poor"
    
    # Estimate unit cost (simplified)
    estimated_unit_cost = estimate_unit_cost(cad_geometry, process, material, production_volume, cost_models)
    
    # Estimate lead time (simplified)
    estimated_lead_time = estimate_lead_time(process, production_volume)
    
    # Get process advantages and limitations
    advantages, limitations = get_process_characteristics(process)
    
    # Create process suitability evaluation
    return ProcessSuitability(
        process=process,
        suitability_score=round(suitability_score, 1),
        manufacturability=manufacturability,
        estimated_unit_cost=round(estimated_unit_cost, 2),
        estimated_lead_time=estimated_lead_time,
        advantages=advantages,
        limitations=limitations
    )

def calculate_volume_suitability(process: ProcessType, production_volume: int) -> float:
    """Calculate suitability factor based on production volume"""
    if process == ProcessType.INJECTION_MOLDING:
        # Injection molding is best for high volumes
        if production_volume < 100:
            return 0.5
        elif production_volume < 1000:
            return 0.7
        elif production_volume < 10000:
            return 0.9
        else:
            return 1.0
    elif process == ProcessType.CNC_MILLING:
        # CNC machining is best for low to medium volumes
        if production_volume < 10:
            return 1.0
        elif production_volume < 100:
            return 0.9
        elif production_volume < 1000:
            return 0.7
        else:
            return 0.5
    elif process == ProcessType.FDM_PRINTING:
        # 3D printing is best for very low volumes
        if production_volume < 10:
            return 1.0
        elif production_volume < 50:
            return 0.8
        elif production_volume < 100:
            return 0.6
        else:
            return 0.4
    else:
        # Default
        return 0.8

def calculate_size_suitability(cad_geometry: CADGeometry, process: ProcessType) -> float:
    """Calculate suitability factor based on part size"""
    # Get maximum dimension
    bbox = cad_geometry.bounding_box
    max_dimension = max(bbox.length, bbox.width, bbox.height)
    
    if process == ProcessType.INJECTION_MOLDING:
        # Injection molding size constraints
        if max_dimension < 10:
            return 0.7  # Too small
        elif max_dimension > 1000:
            return 0.6  # Too large
        else:
            return 1.0
    elif process == ProcessType.CNC_MILLING:
        # CNC machining size constraints
        if max_dimension < 5:
            return 0.6  # Too small
        elif max_dimension > 2000:
            return 0.7  # Very large
        else:
            return 1.0
    elif process == ProcessType.FDM_PRINTING:
        # 3D printing size constraints
        if max_dimension < 5:
            return 0.8  # Small but doable
        elif max_dimension > 300:
            return 0.5  # Too large for most printers
        else:
            return 1.0
    else:
        # Default
        return 0.9

def estimate_unit_cost(cad_geometry: CADGeometry, process: ProcessType,
                     material: MaterialType, production_volume: int,
                     cost_models: Dict) -> float:
    """Estimate unit cost for the given process (simplified)"""
    # Base material costs ($/cm³)
    material_rates = {
        MaterialType.ABS: 0.05,
        MaterialType.PLA: 0.04,
        MaterialType.ALUMINUM: 0.15,
        MaterialType.STEEL: 0.10,
        # Add other materials as needed
    }
    
    # Get material rate (default to ABS if not found)
    material_rate = material_rates.get(material, 0.05)
    
    # Calculate volume in cm³
    volume_cm3 = cad_geometry.volume / 1000.0
    
    # Calculate base material cost
    material_cost = volume_cm3 * material_rate
    
    # Get cost model for the process
    cost_model = cost_models.get(process, {})
    
    if process == ProcessType.INJECTION_MOLDING:
        # Injection molding cost calculation
        tooling_cost = cost_model.get("tooling_base", 5000.0)
        machine_rate = cost_model.get("machine_rate", 75.0)
        
        # Simplified cycle time calculation (seconds)
        cycle_time = 20 + (volume_cm3 * 2)
        
        # Labor cost per part
        labor_cost = (cycle_time / 3600) * machine_rate
        
        # Amortize tooling cost
        tooling_cost_per_part = tooling_cost / production_volume
        
        # Total cost per part
        unit_cost = material_cost + labor_cost + tooling_cost_per_part
        
        # Apply volume discount
        volume_discounts = cost_model.get("volume_discounts", {})
        for threshold, discount in sorted(volume_discounts.items()):
            if production_volume >= threshold:
                unit_cost *= discount
        
    elif process == ProcessType.CNC_MILLING:
        # CNC machining cost calculation
        setup_cost = cost_model.get("setup_cost", 150.0)
        machine_rate = cost_model.get("machine_rate", 85.0)
        
        # Simplified machining time calculation (hours)
        machining_time = 0.5 + (volume_cm3 * 0.01)
        
        # Labor cost per part
        labor_cost = machining_time * machine_rate
        
        # Amortize setup cost
        setup_cost_per_part = setup_cost / production_volume
        
        # Total cost per part
        unit_cost = material_cost * 3 + labor_cost + setup_cost_per_part  # 3x material for waste
        
        # Apply volume discount
        volume_discounts = cost_model.get("volume_discounts", {})
        for threshold, discount in sorted(volume_discounts.items()):
            if production_volume >= threshold:
                unit_cost *= discount
                
    elif process == ProcessType.FDM_PRINTING:
        # 3D printing cost calculation
        machine_rate = 20.0  # $/hour for FDM printer
        
        # Simplified printing time calculation (hours)
        printing_time = volume_cm3 / 15.0  # Assuming 15 cm³/hour
        
        # Labor cost per part (minimal operator time)
        labor_cost = printing_time * machine_rate * 0.3
        
        # Total cost per part
        unit_cost = material_cost * 1.2 + labor_cost  # 20% material waste
        
    else:
        # Default calculation
        unit_cost = material_cost * 2 + 10.0  # Simplified default
    
    return max(1.0, unit_cost)  # Minimum $1.00 per part

def estimate_lead_time(process: ProcessType, production_volume: int) -> int:
    """Estimate lead time in days for the given process and volume"""
    if process == ProcessType.INJECTION_MOLDING:
        # Injection molding lead time
        tooling_time = 28  # 4 weeks for tooling
        production_time = math.ceil(production_volume / 10000)  # 10,000 parts per day
        return tooling_time + production_time
        
    elif process == ProcessType.CNC_MILLING:
        # CNC machining lead time
        setup_time = 3  # 3 days for setup and programming
        production_time = math.ceil(production_volume / 20)  # 20 parts per day
        return setup_time + production_time
        
    elif process == ProcessType.FDM_PRINTING:
        # 3D printing lead time
        setup_time = 1  # 1 day for setup
        production_time = math.ceil(production_volume / 10)  # 10 parts per day
        return setup_time + production_time
        
    else:
        # Default lead time
        return 14  # 2 weeks
        
def get_process_characteristics(process: ProcessType) -> Tuple[List[str], List[str]]:
    """Get advantages and limitations of the manufacturing process"""
    if process == ProcessType.INJECTION_MOLDING:
        advantages = [
            "High volume efficiency",
            "Excellent surface finish",
            "High dimensional accuracy",
            "Fast production cycles",
            "Wide material selection"
        ]
        limitations = [
            "High tooling cost",
            "Design change restrictions",
            "Minimum wall thickness constraints",
            "Draft angles required",
            "Long lead time for tooling"
        ]
        
    elif process == ProcessType.CNC_MILLING:
        advantages = [
            "High dimensional accuracy",
            "Excellent material properties",
            "Good surface finish",
            "No tooling for simple parts",
            "Design changes are easy"
        ]
        limitations = [
            "Higher cost for complex geometries",
            "Material waste",
            "Limited internal features",
            "Tool access constraints",
            "Higher cost for small volumes"
        ]
        
    elif process == ProcessType.FDM_PRINTING:
        advantages = [
            "No tooling required",
            "Complex geometries possible",
            "Fast turnaround for prototypes",
            "Low setup cost",
            "Design changes are easy"
        ]
        limitations = [
            "Limited material properties",
            "Lower dimensional accuracy",
            "Visible layer lines",
            "Slower production rate",
            "Limited part size"
        ]
        
    else:
        advantages = ["Suitable for specific applications"]
        limitations = ["Process-specific constraints apply"]
    
    return advantages, limitations

def evaluate_alternative_processes(cad_geometry: CADGeometry, primary_process: ProcessType,
                                 material: MaterialType, production_volume: int,
                                 cost_models: Dict, material_properties: Dict) -> List[ProcessSuitability]:
    """
    Evaluate alternative manufacturing processes
    
    Args:
        cad_geometry: CAD geometry data
        primary_process: Primary manufacturing process
        material: Target material
        production_volume: Production quantity
        cost_models: Cost models for different processes
        material_properties: Material properties
        
    Returns:
        List of alternative process evaluations
    """
    # Define alternative processes to evaluate
    alternative_processes = [
        ProcessType.INJECTION_MOLDING,
        ProcessType.CNC_MILLING,
        ProcessType.FDM_PRINTING
    ]
    
    # Remove primary process from alternatives
    if primary_process in alternative_processes:
        alternative_processes.remove(primary_process)
    
    # Evaluate each alternative process
    results = []
    for process in alternative_processes:
        # Calculate manufacturability score for this process
        manufacturability_score = 80.0  # Default score
        
        # Evaluate process suitability
        suitability = evaluate_process_suitability(
            cad_geometry, process, material, production_volume,
            manufacturability_score, cost_models, material_properties
        )
        
        results.append(suitability)
    
    # Sort by suitability score (descending)
    results.sort(key=lambda x: x.suitability_score, reverse=True)
    
    return results
