"""
DFM Analysis Methods
Contains implementation of various DFM analysis algorithms
"""
import math
import logging
from typing import Dict, List, Any, Tuple

from ..models.dfm_models import (
    ProcessType, MaterialType, CADGeometry, ManufacturingIssue,
    Point3D, BoundingBox
)

# Configure logging
logger = logging.getLogger(__name__)

def analyze_geometry(cad_geometry: CADGeometry, process: ProcessType, 
                    material: MaterialType, process_rules: Dict, advanced_analysis: bool = True) -> List[ManufacturingIssue]:
    """Analyze CAD geometry for manufacturing issues"""
    issues = []
    
    # Get process-specific constraints
    process_constraints = process_rules.get(process.value, {})
    logger.debug(f"Analyzing geometry for process: {process.value} with constraints: {process_constraints}")
    
    # Common checks for all processes
    logger.debug("Running common checks for all processes")
    issues.extend(check_wall_thickness(cad_geometry, process_constraints))
    issues.extend(check_aspect_ratio(cad_geometry, process_constraints))
    issues.extend(check_holes(cad_geometry, process_constraints))
    
    # Process-specific checks
    logger.debug(f"Running process-specific checks for {process.value}")
    if process == ProcessType.INJECTION_MOLDING:
        issues.extend(check_injection_molding_issues(cad_geometry, process_constraints))
    elif process == ProcessType.CNC_MILLING:
        issues.extend(check_cnc_milling_issues(cad_geometry, process_constraints))
    elif process == ProcessType.FDM_PRINTING:
        issues.extend(check_fdm_printing_issues(cad_geometry, process_constraints))
    
    # Advanced analysis if enabled
    if advanced_analysis:
        logger.debug("Running advanced analysis checks")
        if process == ProcessType.INJECTION_MOLDING:
            issues.extend(check_advanced_injection_molding(cad_geometry, process_constraints))
        elif process == ProcessType.CNC_MILLING:
            issues.extend(check_advanced_cnc_milling(cad_geometry, process_constraints))
        elif process == ProcessType.FDM_PRINTING:
            issues.extend(check_advanced_fdm_printing(cad_geometry, process_constraints))
        
        # Material compatibility check (advanced)
        issues.extend(check_material_compatibility(cad_geometry, process, material, process_constraints))
    
    # Calculate manufacturability score
    score = calculate_manufacturability_score(issues)
    rating = score_to_rating(score)
    
    logger.debug(f"Analysis complete. Found {len(issues)} issues. Manufacturability score: {score:.1f} ({rating})")
    
    # Add overall manufacturability score as an informational issue
    issues.append(ManufacturingIssue(
        title="Manufacturability Score",
        severity="info",
        description=f"Overall manufacturability score: {score:.1f}/100 ({rating})",
        recommendation="Address the identified issues to improve manufacturability",
        position=None,
        cost_impact=0.0
    ))
    
    return issues

def check_wall_thickness(cad_geometry: CADGeometry, constraints: Dict) -> List[ManufacturingIssue]:
    """Check for wall thickness issues based on manufacturing process requirements"""
    issues = []
    
    # Get constraints based on process type
    min_wall_thickness = constraints.get("min_wall_thickness", 0.8)  # Default 0.8mm
    max_wall_thickness = constraints.get("max_wall_thickness", 5.0)  # Default 5.0mm
    
    logger.debug(f"Checking wall thickness with min={min_wall_thickness}mm, max={max_wall_thickness}mm")
    logger.debug(f"CAD model has {len(cad_geometry.thin_walls)} thin walls defined")
    
    # Check thin walls if they're provided in the CAD geometry
    for thin_wall in cad_geometry.thin_walls:
        thickness = thin_wall.thickness
        location = thin_wall.location
        
        logger.debug(f"Analyzing wall with thickness {thickness}mm at location {location}")
        
        if thickness < min_wall_thickness:
            issues.append(ManufacturingIssue(
                title="Wall Thickness Too Thin",
                severity="high",
                description=f"Wall thickness of {thickness:.2f}mm is below minimum recommended {min_wall_thickness:.2f}mm",
                recommendation=f"Increase wall thickness to at least {min_wall_thickness:.2f}mm or consider adding ribs for structural support",
                position=Point3D(x=location[0], y=location[1], z=location[2]),
                cost_impact=0.15  # 15% cost impact
            ))
            logger.debug(f"Found thin wall issue: {thickness}mm < {min_wall_thickness}mm")
        elif thickness > max_wall_thickness:
            issues.append(ManufacturingIssue(
                title="Wall Thickness Too Thick",
                severity="medium",
                description=f"Wall thickness of {thickness:.2f}mm exceeds maximum recommended {max_wall_thickness:.2f}mm",
                recommendation=f"Reduce wall thickness to below {max_wall_thickness:.2f}mm to save material and reduce cooling time",
                position=Point3D(x=location[0], y=location[1], z=location[2]),
                cost_impact=0.08  # 8% cost impact
            ))
            logger.debug(f"Found thick wall issue: {thickness}mm > {max_wall_thickness}mm")
    
    # If no thin walls were provided but we have volume and surface area, estimate average wall thickness
    if not cad_geometry.thin_walls and cad_geometry.volume > 0 and cad_geometry.surface_area > 0:
        # Estimate average wall thickness using volume/surface area ratio
        estimated_thickness = 2 * cad_geometry.volume / cad_geometry.surface_area
        logger.debug(f"Estimated average wall thickness: {estimated_thickness:.2f}mm")
        
        if estimated_thickness < min_wall_thickness:
            issues.append(ManufacturingIssue(
                title="Estimated Wall Thickness Too Thin",
                severity="medium",
                description=f"Estimated average wall thickness of {estimated_thickness:.2f}mm is below minimum recommended {min_wall_thickness:.2f}mm",
                recommendation=f"Consider increasing wall thickness to at least {min_wall_thickness:.2f}mm for better manufacturability",
                position=cad_geometry.center_of_mass,
                cost_impact=0.10  # 10% cost impact
            ))
            logger.debug(f"Found estimated thin wall issue: {estimated_thickness:.2f}mm < {min_wall_thickness}mm")
        elif estimated_thickness > max_wall_thickness * 1.5:  # Using 1.5x as a threshold for estimated thickness
            issues.append(ManufacturingIssue(
                title="Estimated Wall Thickness Too Thick",
                severity="low",
                description=f"Estimated average wall thickness of {estimated_thickness:.2f}mm is significantly above recommended {max_wall_thickness:.2f}mm",
                recommendation=f"Consider reducing overall wall thickness to save material and reduce cooling time",
                position=cad_geometry.center_of_mass,
                cost_impact=0.05  # 5% cost impact
            ))
            logger.debug(f"Found estimated thick wall issue: {estimated_thickness:.2f}mm > {max_wall_thickness * 1.5}mm")
            
    logger.debug(f"Wall thickness check complete: found {len(issues)} issues")
    return issues

def check_aspect_ratio(cad_geometry: CADGeometry, constraints: Dict) -> List[ManufacturingIssue]:
    """Check for aspect ratio issues that could affect manufacturability"""
    issues = []
    
    # Get constraints based on process type
    max_aspect_ratio = constraints.get("max_aspect_ratio", 5.0)  # Default 5.0
    
    # Calculate aspect ratio from bounding box
    bbox = cad_geometry.bounding_box
    dimensions = [bbox.length, bbox.width, bbox.height]
    max_dim = max(dimensions)
    min_dim = min(dimensions)
    
    logger.debug(f"Bounding box dimensions: {dimensions}")
    logger.debug(f"Max dimension: {max_dim}, Min dimension: {min_dim}")
    
    # Avoid division by zero
    if min_dim <= 0:
        logger.warning("Minimum dimension is zero or negative, cannot calculate aspect ratio")
        issues.append(ManufacturingIssue(
            title="Invalid Dimensions",
            severity="critical",
            description="Model has zero or negative dimensions",
            recommendation="Check model integrity and ensure all dimensions are positive",
            position=cad_geometry.center_of_mass,
            cost_impact=0.25  # 25% cost impact
        ))
        return issues
    
    # Calculate aspect ratio and check against constraints
    aspect_ratio = max_dim / min_dim
    logger.debug(f"Calculated aspect ratio: {aspect_ratio:.2f} (max: {max_aspect_ratio:.2f})")
    
    if aspect_ratio > max_aspect_ratio:
        # Determine which dimensions are causing the issue
        if max_dim == bbox.length:
            long_dim = "length"
        elif max_dim == bbox.width:
            long_dim = "width"
        else:
            long_dim = "height"
            
        if min_dim == bbox.length:
            short_dim = "length"
        elif min_dim == bbox.width:
            short_dim = "width"
        else:
            short_dim = "height"
            
        issues.append(ManufacturingIssue(
            title="High Aspect Ratio",
            severity="medium",
            description=f"Aspect ratio of {aspect_ratio:.2f} exceeds recommended maximum of {max_aspect_ratio:.2f}",
            recommendation=f"Consider redesigning to reduce the {long_dim} or increase the {short_dim} for better manufacturability",
            position=cad_geometry.center_of_mass,
            cost_impact=0.12  # 12% cost impact
        ))
        logger.debug(f"Found high aspect ratio issue: {aspect_ratio:.2f} > {max_aspect_ratio:.2f}")
    
    logger.debug(f"Aspect ratio check complete: found {len(issues)} issues")
    return issues


def check_holes(cad_geometry: CADGeometry, constraints: Dict) -> List[ManufacturingIssue]:
    """Check for hole-related manufacturing issues"""
    issues = []
    
    # Get constraints
    min_hole_diameter = constraints.get("min_hole_diameter", 1.0)  # Default 1.0mm
    max_hole_depth_to_diameter_ratio = constraints.get("max_hole_depth_to_diameter_ratio", 10.0)  # Default 10:1
    
    logger.debug(f"Checking holes with min_diameter={min_hole_diameter}mm, max_depth_ratio={max_hole_depth_to_diameter_ratio}")
    logger.debug(f"CAD model has {len(cad_geometry.holes)} holes defined")
    
    # Check each hole in the model
    for hole in cad_geometry.holes:
        diameter = hole.diameter
        depth = hole.depth
        location = hole.location
        
        logger.debug(f"Analyzing hole with diameter={diameter}mm, depth={depth}mm at location={location}")
        
        # Check for small holes
        if diameter < min_hole_diameter:
            issues.append(ManufacturingIssue(
                title="Hole Diameter Too Small",
                severity="high",
                description=f"Hole diameter of {diameter:.2f}mm is below minimum recommended {min_hole_diameter:.2f}mm",
                recommendation=f"Increase hole diameter to at least {min_hole_diameter:.2f}mm or consider removing if non-essential",
                position=Point3D(x=location[0], y=location[1], z=location[2]),
                cost_impact=0.15  # 15% cost impact
            ))
            logger.debug(f"Found small hole issue: {diameter}mm < {min_hole_diameter}mm")
        
        # Check depth to diameter ratio
        if diameter > 0:  # Avoid division by zero
            depth_to_diameter_ratio = depth / diameter
            
            if depth_to_diameter_ratio > max_hole_depth_to_diameter_ratio:
                issues.append(ManufacturingIssue(
                    title="Deep Hole Issue",
                    severity="medium",
                    description=f"Hole depth-to-diameter ratio of {depth_to_diameter_ratio:.2f} exceeds recommended maximum of {max_hole_depth_to_diameter_ratio:.2f}",
                    recommendation=f"Consider increasing hole diameter, reducing depth, or using specialized deep-hole drilling processes",
                    position=Point3D(x=location[0], y=location[1], z=location[2]),
                    cost_impact=0.18  # 18% cost impact
                ))
                logger.debug(f"Found deep hole issue: depth/diameter ratio {depth_to_diameter_ratio:.2f} > {max_hole_depth_to_diameter_ratio:.2f}")
    
    logger.debug(f"Hole check complete: found {len(issues)} issues")
    return issues


def check_injection_molding_issues(cad_geometry: CADGeometry, constraints: Dict) -> List[ManufacturingIssue]:
    """Check for injection molding specific issues"""
    issues = []
    
    # Get injection molding specific constraints
    min_draft_angle = constraints.get("min_draft_angle", 1.0)  # Default 1.0 degrees
    max_undercut_depth = constraints.get("max_undercut_depth", 0.0)  # Default 0.0mm (no undercuts)
    
    logger.debug(f"Checking injection molding issues with min_draft_angle={min_draft_angle}°")
    
    # Simplified draft angle check based on bounding box
    # In a real implementation, this would analyze actual faces and their draft angles
    bbox = cad_geometry.bounding_box
    if bbox.height > 0 and (bbox.length / bbox.height > 5 or bbox.width / bbox.height > 5):
        issues.append(ManufacturingIssue(
            title="Potential Draft Angle Issue",
            severity="medium",
            description="Part has high aspect ratio walls that may require proper draft angles",
            recommendation=f"Ensure all vertical walls have at least {min_draft_angle}° draft angle for proper ejection",
            position=cad_geometry.center_of_mass,
            cost_impact=0.10  # 10% cost impact
        ))
        logger.debug("Found potential draft angle issue based on part proportions")
    
    # Check for potential sink marks in thick sections
    # In a real implementation, this would analyze actual thickness variations
    if cad_geometry.volume > 0 and cad_geometry.surface_area > 0:
        avg_thickness = 2 * cad_geometry.volume / cad_geometry.surface_area
        if avg_thickness > 4.0:  # Thick sections prone to sink marks
            issues.append(ManufacturingIssue(
                title="Potential Sink Marks",
                severity="medium",
                description=f"Average wall thickness of {avg_thickness:.2f}mm may lead to sink marks",
                recommendation="Consider using uniform wall thickness and adding ribs instead of thick sections",
                position=cad_geometry.center_of_mass,
                cost_impact=0.08  # 8% cost impact
            ))
            logger.debug(f"Found potential sink mark issue: avg thickness {avg_thickness:.2f}mm > 4.0mm")
    
    logger.debug(f"Injection molding check complete: found {len(issues)} issues")
    return issues


def check_cnc_milling_issues(cad_geometry: CADGeometry, constraints: Dict) -> List[ManufacturingIssue]:
    """Check for CNC milling specific issues"""
    issues = []
    
    # Get CNC milling specific constraints
    min_corner_radius = constraints.get("min_corner_radius", 1.0)  # Default 1.0mm
    min_feature_size = constraints.get("min_feature_size", 0.5)  # Default 0.5mm
    max_depth_to_width_ratio = constraints.get("max_depth_to_width_ratio", 4.0)  # Default 4:1
    
    logger.debug(f"Checking CNC milling issues with min_corner_radius={min_corner_radius}mm")
    
    # Check for potential deep pocket issues
    bbox = cad_geometry.bounding_box
    if bbox.height > 3 * min(bbox.length, bbox.width):
        issues.append(ManufacturingIssue(
            title="Deep Pocket Machining Issue",
            severity="medium",
            description=f"Part has deep pockets with depth-to-width ratio exceeding {max_depth_to_width_ratio}:1",
            recommendation="Consider redesigning with shallower pockets or use specialized tooling",
            position=cad_geometry.center_of_mass,
            cost_impact=0.15  # 15% cost impact
        ))
        logger.debug("Found deep pocket issue based on part proportions")
    
    # Check for potential sharp internal corner issues
    # In a real implementation, this would analyze actual corner radii
    if cad_geometry.holes and any(hole.diameter < 2 * min_corner_radius for hole in cad_geometry.holes):
        issues.append(ManufacturingIssue(
            title="Sharp Internal Corner Issue",
            severity="medium",
            description=f"Part has potential sharp internal corners below minimum radius of {min_corner_radius}mm",
            recommendation=f"Design all internal corners with at least {min_corner_radius}mm radius",
            position=cad_geometry.center_of_mass,
            cost_impact=0.12  # 12% cost impact
        ))
        logger.debug("Found sharp internal corner issue based on hole diameters")
    
    logger.debug(f"CNC milling check complete: found {len(issues)} issues")
    return issues


def check_fdm_printing_issues(cad_geometry: CADGeometry, constraints: Dict) -> List[ManufacturingIssue]:
    """Check for FDM 3D printing specific issues"""
    issues = []
    
    # Get FDM printing specific constraints
    min_feature_size = constraints.get("min_feature_size", 0.4)  # Default 0.4mm (typical nozzle size)
    max_overhang_angle = constraints.get("max_overhang_angle", 45.0)  # Default 45 degrees
    max_bridge_length = constraints.get("max_bridge_length", 10.0)  # Default 10mm
    
    logger.debug(f"Checking FDM printing issues with min_feature_size={min_feature_size}mm")
    
    # Check for potential thin features
    if cad_geometry.thin_walls and any(wall.thickness < min_feature_size for wall in cad_geometry.thin_walls):
        issues.append(ManufacturingIssue(
            title="Thin Feature Issue",
            severity="high",
            description=f"Part has features thinner than minimum printable size of {min_feature_size}mm",
            recommendation=f"Increase all feature thicknesses to at least {min_feature_size}mm",
            position=cad_geometry.center_of_mass,
            cost_impact=0.20  # 20% cost impact
        ))
        logger.debug("Found thin feature issue based on wall thicknesses")
    
    # Check for potential support structure needs
    # In a real implementation, this would analyze actual overhangs and orientations
    bbox = cad_geometry.bounding_box
    if bbox.height > 2 * max(bbox.length, bbox.width):
        issues.append(ManufacturingIssue(
            title="Potential Support Structure Needed",
            severity="medium",
            description="Part geometry may require extensive support structures during printing",
            recommendation="Consider redesigning to minimize overhangs or reorient the part for printing",
            position=cad_geometry.center_of_mass,
            cost_impact=0.15  # 15% cost impact
        ))
        logger.debug("Found potential support structure issue based on part proportions")
    
    logger.debug(f"FDM printing check complete: found {len(issues)} issues")
    return issues


def check_advanced_injection_molding(cad_geometry: CADGeometry, constraints: Dict) -> List[ManufacturingIssue]:
    """Advanced checks for injection molding"""
    issues = []
    
    # Advanced checks would analyze parting line placement, gate location, flow analysis, etc.
    # For this implementation, we'll add a few more detailed checks
    
    # Check for potential weld line issues
    if cad_geometry.holes and len(cad_geometry.holes) > 1:
        issues.append(ManufacturingIssue(
            title="Potential Weld Line Issue",
            severity="medium",
            description="Multiple holes may cause weld lines in the part",
            recommendation="Consider repositioning holes or adjusting gate location to minimize weld lines",
            position=cad_geometry.center_of_mass,
            cost_impact=0.08  # 8% cost impact
        ))
    
    # Check for uniform wall thickness
    if cad_geometry.thin_walls and len(cad_geometry.thin_walls) > 1:
        thicknesses = [wall.thickness for wall in cad_geometry.thin_walls]
        thickness_variation = max(thicknesses) - min(thicknesses)
        if thickness_variation > 1.0:  # More than 1mm variation
            issues.append(ManufacturingIssue(
                title="Non-uniform Wall Thickness",
                severity="medium",
                description=f"Wall thickness varies by {thickness_variation:.2f}mm across the part",
                recommendation="Design with uniform wall thickness to prevent warping and sink marks",
                position=cad_geometry.center_of_mass,
                cost_impact=0.10  # 10% cost impact
            ))
    
    return issues


def check_advanced_cnc_milling(cad_geometry: CADGeometry, constraints: Dict) -> List[ManufacturingIssue]:
    """Advanced checks for CNC milling"""
    issues = []
    
    # Advanced checks would analyze tool accessibility, fixturing, etc.
    # For this implementation, we'll add a few more detailed checks
    
    # Check for potential thin walls that might vibrate during machining
    if cad_geometry.thin_walls and any(wall.thickness < 1.0 for wall in cad_geometry.thin_walls):
        issues.append(ManufacturingIssue(
            title="Thin Wall Machining Issue",
            severity="medium",
            description="Thin walls may vibrate or deflect during machining",
            recommendation="Increase wall thickness or add support ribs to prevent deflection",
            position=cad_geometry.center_of_mass,
            cost_impact=0.12  # 12% cost impact
        ))
    
    # Check for deep holes that might require special tooling
    if cad_geometry.holes and any(hole.depth > 10 * hole.diameter for hole in cad_geometry.holes):
        issues.append(ManufacturingIssue(
            title="Deep Hole Drilling Issue",
            severity="medium",
            description="Deep holes may require specialized drilling techniques",
            recommendation="Consider redesigning with shallower holes or specify gun drilling operation",
            position=cad_geometry.center_of_mass,
            cost_impact=0.15  # 15% cost impact
        ))
    
    return issues


def check_advanced_fdm_printing(cad_geometry: CADGeometry, constraints: Dict) -> List[ManufacturingIssue]:
    """Advanced checks for FDM 3D printing"""
    issues = []
    
    # Advanced checks would analyze layer adhesion, warping potential, etc.
    # For this implementation, we'll add a few more detailed checks
    
    # Check for potential warping issues with large flat surfaces
    bbox = cad_geometry.bounding_box
    if bbox.length > 100 or bbox.width > 100:  # Large flat surfaces
        issues.append(ManufacturingIssue(
            title="Warping Risk",
            severity="medium",
            description="Large flat surfaces may warp during printing",
            recommendation="Add ribs or other features to reduce warping, or consider using a heated build chamber",
            position=cad_geometry.center_of_mass,
            cost_impact=0.10  # 10% cost impact
        ))
    
    # Check for potential layer adhesion issues with tall, thin features
    if bbox.height > 5 * min(bbox.length, bbox.width):  # Tall, thin features
        issues.append(ManufacturingIssue(
            title="Layer Adhesion Risk",
            severity="high",
            description="Tall, thin features may have poor layer adhesion and break easily",
            recommendation="Increase cross-sectional area or reorient the part for printing",
            position=cad_geometry.center_of_mass,
            cost_impact=0.18  # 18% cost impact
        ))
    
    return issues


def check_material_compatibility(cad_geometry: CADGeometry, process: ProcessType, material: MaterialType, constraints: Dict) -> List[ManufacturingIssue]:
    """Check material compatibility with process and geometry"""
    issues = []
    
    # Material-process compatibility checks
    incompatible_pairs = [
        (ProcessType.INJECTION_MOLDING, MaterialType.CARBON_FIBER),  # Abrasive, wears molds
        (ProcessType.CNC_MILLING, MaterialType.PLA),  # Too soft for efficient machining
        (ProcessType.FDM_PRINTING, MaterialType.PEEK)  # Requires very high temperatures
    ]
    
    if any(pair == (process, material) for pair in incompatible_pairs):
        issues.append(ManufacturingIssue(
            title="Material-Process Incompatibility",
            severity="high",
            description=f"{material.value} is not ideal for {process.value}",
            recommendation="Consider using a different material better suited for this manufacturing process",
            position=None,
            cost_impact=0.25  # 25% cost impact
        ))
    
    # Material-geometry compatibility checks
    if material == MaterialType.ABS and cad_geometry.volume > 1000000:  # Large ABS parts
        issues.append(ManufacturingIssue(
            title="Material-Size Compatibility Issue",
            severity="medium",
            description="Large ABS parts are prone to warping and dimensional instability",
            recommendation="Consider using a more dimensionally stable material like PC or reinforced nylon",
            position=None,
            cost_impact=0.15  # 15% cost impact
        ))
    
    return issues


def calculate_manufacturability_score(issues: List[ManufacturingIssue]) -> float:
    """Calculate overall manufacturability score based on issues"""
    # Base score starts at 100
    score = 100.0
    
    # Deduct points based on issue severity
    severity_deductions = {
        "low": 5.0,
        "medium": 10.0,
        "high": 20.0,
        "critical": 40.0
    }
    
    for issue in issues:
        score -= severity_deductions.get(issue.severity, 5.0)
    
    # Ensure score doesn't go below 0
    return max(0.0, score)


def score_to_rating(score: float) -> str:
    """Convert numeric score to text rating"""
    if score >= 90:
        return "excellent"
    elif score >= 75:
        return "good"
    elif score >= 50:
        return "fair"
    else:
        return "poor"

# End of file
