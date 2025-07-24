"""
Production-Level CAD Geometry Extraction System - Part 1: Core Framework
Complete implementation for FreeCAD geometry analysis and feature extraction
Designed for Industry-Grade DFM Backend Integration
"""

import os
import sys
import json
import math
import time
import traceback
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# FreeCAD imports with error handling
try:
    import FreeCAD
    import Part
    import FreeCADGui
    import Draft
    import Mesh
    FREECAD_AVAILABLE = True
except ImportError as e:
    print(f"Warning: FreeCAD modules not available: {e}")
    FREECAD_AVAILABLE = False

# ==========================================
# DATA MODELS FOR CAD GEOMETRY
# ==========================================

class PartType(str, Enum):
    """Classification of part types for targeted analysis"""
    MECHANICAL_COMPONENT = "mechanical_component"
    HOUSING_ENCLOSURE = "housing_enclosure"
    BRACKET_MOUNT = "bracket_mount"
    GEAR_DRIVE = "gear_drive"
    SHAFT_ROD = "shaft_rod"
    PLATE_PANEL = "plate_panel"
    COMPLEX_ASSEMBLY = "complex_assembly"
    THIN_WALLED_PART = "thin_walled_part"
    THICK_SECTION_PART = "thick_section_part"
    UNKNOWN = "unknown"

class FeatureType(str, Enum):
    """Comprehensive feature classification"""
    HOLE_THROUGH = "hole_through"
    HOLE_BLIND = "hole_blind"
    HOLE_COUNTERBORE = "hole_counterbore"
    HOLE_COUNTERSINK = "hole_countersink"
    POCKET_RECTANGULAR = "pocket_rectangular"
    POCKET_CIRCULAR = "pocket_circular"
    POCKET_COMPLEX = "pocket_complex"
    BOSS_CIRCULAR = "boss_circular"
    BOSS_RECTANGULAR = "boss_rectangular"
    RIB_STRUCTURAL = "rib_structural"
    RIB_COOLING = "rib_cooling"
    FILLET_INTERNAL = "fillet_internal"
    FILLET_EXTERNAL = "fillet_external"
    CHAMFER_EDGE = "chamfer_edge"
    THREAD_INTERNAL = "thread_internal"
    THREAD_EXTERNAL = "thread_external"
    UNDERCUT_GROOVE = "undercut_groove"
    UNDERCUT_RELIEF = "undercut_relief"
    THIN_WALL = "thin_wall"
    THICK_SECTION = "thick_section"
    SHARP_CORNER = "sharp_corner"
    DRAFT_SURFACE = "draft_surface"
    PARTING_LINE = "parting_line"

@dataclass
class GeometricTolerance:
    """Geometric tolerance specification"""
    tolerance_type: str  # "dimensional", "geometric", "surface_finish"
    specification: str   # e.g., "±0.1", "⊥0.05", "Ra 3.2"
    applied_to: List[str]  # Feature IDs this tolerance applies to
    critical: bool = False
    achievable_processes: List[str] = field(default_factory=list)

@dataclass
class SurfaceFinish:
    """Surface finish specification"""
    surface_id: str
    finish_type: str  # "machined", "as_molded", "polished", "textured"
    roughness_ra: float  # Ra value in micrometers
    direction: Optional[str] = None  # "parallel", "perpendicular", "circular"
    special_requirements: List[str] = field(default_factory=list)

@dataclass
class DetailedFeature:
    """Comprehensive feature representation"""
    feature_id: str
    feature_type: FeatureType
    location: Tuple[float, float, float]  # Center point
    orientation: Tuple[float, float, float]  # Direction vector

    # Dimensional properties
    dimensions: Dict[str, float] = field(default_factory=dict)
    bounding_box: Dict[str, float] = field(default_factory=dict)

    # Geometric properties
    volume: float = 0.0
    surface_area: float = 0.0
    aspect_ratio: float = 1.0
    complexity_score: float = 0.0

    # Manufacturing properties
    accessibility: str = "accessible"  # "accessible", "limited", "inaccessible"
    draft_angle: Optional[float] = None
    fillet_radii: List[float] = field(default_factory=list)
    surface_finish: Optional[SurfaceFinish] = None
    tolerances: List[GeometricTolerance] = field(default_factory=list)

    # Relationships
    parent_feature_id: Optional[str] = None
    child_feature_ids: List[str] = field(default_factory=list)
    intersecting_features: List[str] = field(default_factory=list)

    # Manufacturing analysis
    manufacturability_issues: List[str] = field(default_factory=list)
    cost_drivers: List[str] = field(default_factory=list)
    recommended_processes: List[str] = field(default_factory=list)

    # Geometric data for visualization
    geometry_data: Optional[Dict[str, Any]] = None

@dataclass
class WallThicknessAnalysis:
    """Comprehensive wall thickness analysis"""
    region_id: str
    location: Tuple[float, float, float]
    thickness: float
    local_variations: List[float] = field(default_factory=list)

    # Surrounding context
    adjacent_features: List[str] = field(default_factory=list)
    structural_role: str = "primary"  # "primary", "secondary", "cosmetic"

    # Manufacturing implications
    process_suitability: Dict[str, bool] = field(default_factory=dict)
    potential_issues: List[str] = field(default_factory=list)
    recommended_thickness: Optional[float] = None

@dataclass
class MaterialFlow:
    """Material flow analysis for molding processes"""
    flow_path_id: str
    start_location: Tuple[float, float, float]
    end_location: Tuple[float, float, float]
    flow_distance: float
    cross_sectional_area: float

    # Flow characteristics
    flow_resistance: float = 0.0
    turbulence_risk: str = "low"  # "low", "medium", "high"
    cooling_rate: float = 0.0

    # Potential issues
    weld_line_risk: bool = False
    air_trap_risk: bool = False
    incomplete_fill_risk: bool = False

@dataclass
class ComprehensiveCADGeometry:
    """Production-level CAD geometry representation"""
    # Part identification
    part_name: str
    part_type: PartType
    file_path: Optional[str] = None
    extraction_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Basic geometric properties
    overall_dimensions: Dict[str, float] = field(default_factory=dict)
    bounding_box: Dict[str, float] = field(default_factory=dict)
    volume: float = 0.0
    surface_area: float = 0.0
    center_of_mass: Dict[str, float] = field(default_factory=dict)
    moments_of_inertia: Dict[str, float] = field(default_factory=dict)

    # Detailed feature analysis
    features: List[DetailedFeature] = field(default_factory=list)
    wall_thickness_analysis: List[WallThicknessAnalysis] = field(default_factory=list)
    material_flow_analysis: List[MaterialFlow] = field(default_factory=list)

    # Manufacturing-specific analysis
    draft_analysis: Dict[str, Any] = field(default_factory=dict)
    undercut_analysis: Dict[str, Any] = field(default_factory=dict)
    parting_line_analysis: Dict[str, Any] = field(default_factory=dict)
    stress_concentration_analysis: Dict[str, Any] = field(default_factory=dict)
    manufacturability_summary: Dict[str, Any] = field(default_factory=dict)

    # Quality and specifications
    tolerances: List[GeometricTolerance] = field(default_factory=list)
    surface_finishes: List[SurfaceFinish] = field(default_factory=list)

    # Model complexity metrics
    complexity_metrics: Dict[str, float] = field(default_factory=dict)
    feature_density: float = 0.0
    geometric_complexity_index: float = 0.0

    # Validation and quality
    extraction_quality: str = "unknown"  # "excellent", "good", "fair", "poor"
    validation_errors: List[str] = field(default_factory=list)
    completeness_score: float = 0.0

# ==========================================
# CORE ANALYZER CLASS FRAMEWORK
# ==========================================

class ProductionCADAnalyzer:
    """Production-level CAD geometry extraction and analysis"""
    
    def __init__(self):
        self.feature_extractors = {}
        self.model_analyzers = {}
        self._initialize_extractors()
        self._initialize_analyzers()
    
    def _initialize_extractors(self):
        """Initialize feature extraction methods"""
        self.feature_extractors = {
            FeatureType.HOLE_THROUGH: self._extract_holes,
            FeatureType.HOLE_BLIND: self._extract_holes,
            FeatureType.POCKET_RECTANGULAR: self._extract_pockets,
            FeatureType.POCKET_CIRCULAR: self._extract_pockets,
            FeatureType.BOSS_CIRCULAR: self._extract_bosses,
            FeatureType.RIB_STRUCTURAL: self._extract_ribs,
            FeatureType.FILLET_INTERNAL: self._extract_fillets,
            FeatureType.THIN_WALL: self._extract_thin_walls,
            FeatureType.UNDERCUT_GROOVE: self._extract_undercuts
        }
    
    def _initialize_analyzers(self):
        """Initialize model-specific analyzers"""
        self.model_analyzers = {
            PartType.HOUSING_ENCLOSURE: self._analyze_housing,
            PartType.BRACKET_MOUNT: self._analyze_bracket,
            PartType.GEAR_DRIVE: self._analyze_gear,
            PartType.SHAFT_ROD: self._analyze_shaft,
            PartType.THIN_WALLED_PART: self._analyze_thin_walled_part,
            PartType.MECHANICAL_COMPONENT: self._analyze_mechanical_component
        }
    
    def extract_comprehensive_geometry(self, document_name: Optional[str] = None) -> ComprehensiveCADGeometry:
        """
        Extract comprehensive geometry data from FreeCAD document
        
        Args:
            document_name: Name of FreeCAD document to analyze (None for active)
            
        Returns:
            ComprehensiveCADGeometry object with complete analysis
        """
        
        if not FREECAD_AVAILABLE:
            raise RuntimeError("FreeCAD modules not available")
        
        # Get document
        doc = self._get_document(document_name)
        if not doc:
            raise RuntimeError(f"Document not found: {document_name}")
        
        print(f"🔍 Starting comprehensive geometry extraction for: {doc.Name}")
        
        try:
            # Initialize geometry object
            geometry = ComprehensiveCADGeometry(
                part_name=doc.Name,
                part_type=PartType.UNKNOWN,
                file_path=doc.FileName if hasattr(doc, 'FileName') else None
            )
            
            # Step 1: Basic geometric analysis
            print("📐 Analyzing basic geometric properties...")
            self._extract_basic_properties(doc, geometry)
            
            # Step 2: Classify part type
            print("🏷️ Classifying part type...")
            geometry.part_type = self._classify_part_type(doc, geometry)
            
            # Step 3: Extract detailed features
            print("🔧 Extracting detailed features...")
            self._extract_all_features(doc, geometry)
            
            # Step 4: Perform wall thickness analysis
            print("📏 Analyzing wall thickness...")
            self._analyze_wall_thickness(doc, geometry)
            
            # Step 5: Manufacturing-specific analysis
            print("⚙️ Performing manufacturing analysis...")
            self._perform_manufacturing_analysis(doc, geometry)
            
            # Step 6: Model-specific analysis
            print("🎯 Running model-specific analysis...")
            self._perform_model_specific_analysis(doc, geometry)
            
            # Step 7: Calculate complexity metrics
            print("📊 Calculating complexity metrics...")
            self._calculate_complexity_metrics(geometry)
            
            # Step 8: Validate extraction quality
            print("✅ Validating extraction quality...")
            self._validate_extraction_quality(geometry)
            
            print(f"✅ Extraction complete! Quality: {geometry.extraction_quality}")
            print(f"📈 Features extracted: {len(geometry.features)}")
            print(f"🎯 Complexity index: {geometry.geometric_complexity_index:.2f}")
            
            return geometry
            
        except Exception as e:
            print(f"❌ Extraction failed: {str(e)}")
            traceback.print_exc()
            
            # Return partial data with error info
            error_geometry = ComprehensiveCADGeometry(
                part_name=doc.Name if doc else "Unknown",
                part_type=PartType.UNKNOWN,
                extraction_quality="poor"
            )
            error_geometry.validation_errors.append(f"Extraction failed: {str(e)}")
            return error_geometry
    
    def _get_document(self, document_name: Optional[str]):
        """Get FreeCAD document with error handling"""
        try:
            if document_name:
                return FreeCAD.getDocument(document_name)
            else:
                return FreeCAD.ActiveDocument
        except Exception as e:
            print(f"Error getting document: {e}")
            return None
    
    def _extract_basic_properties(self, doc, geometry: ComprehensiveCADGeometry):
        """Extract basic geometric properties"""
        
        total_volume = 0.0
        total_surface_area = 0.0
        min_x = min_y = min_z = float('inf')
        max_x = max_y = max_z = float('-inf')
        
        center_mass_x = center_mass_y = center_mass_z = 0.0
        mass_contributions = 0
        
        # Analyze all solid objects
        solid_objects = self._get_solid_objects(doc)
        
        if not solid_objects:
            print("⚠️ No solid objects found in document")
            return
        
        for obj in solid_objects:
            try:
                if not hasattr(obj, 'Shape') or not obj.Shape.isValid():
                    continue
                
                shape = obj.Shape
                
                # Volume and surface area
                if hasattr(shape, 'Volume') and shape.Volume > 0:
                    total_volume += shape.Volume
                    total_surface_area += shape.Area
                    
                    # Center of mass
                    if hasattr(shape, 'CenterOfMass'):
                        com = shape.CenterOfMass
                        center_mass_x += com.x * shape.Volume
                        center_mass_y += com.y * shape.Volume  
                        center_mass_z += com.z * shape.Volume
                        mass_contributions += shape.Volume
                
                # Bounding box
                if hasattr(shape, 'BoundBox'):
                    bbox = shape.BoundBox
                    min_x = min(min_x, bbox.XMin)
                    min_y = min(min_y, bbox.YMin)
                    min_z = min(min_z, bbox.ZMin)
                    max_x = max(max_x, bbox.XMax)
                    max_y = max(max_y, bbox.YMax)
                    max_z = max(max_z, bbox.ZMax)
                    
            except Exception as e:
                print(f"Warning: Error processing object {obj.Name}: {e}")
                continue
        
        # Store results
        geometry.volume = total_volume
        geometry.surface_area = total_surface_area
        
        # Overall dimensions
        if max_x != float('-inf'):
            geometry.overall_dimensions = {
                "length": max_x - min_x,
                "width": max_y - min_y,
                "height": max_z - min_z
            }
            
            geometry.bounding_box = {
                "x_min": min_x, "x_max": max_x,
                "y_min": min_y, "y_max": max_y,
                "z_min": min_z, "z_max": max_z,
                "center_x": (max_x + min_x) / 2,
                "center_y": (max_y + min_y) / 2,
                "center_z": (max_z + min_z) / 2
            }
        
        # Center of mass
        if mass_contributions > 0:
            geometry.center_of_mass = {
                "x": center_mass_x / mass_contributions,
                "y": center_mass_y / mass_contributions,
                "z": center_mass_z / mass_contributions
            }
        
        # Calculate moments of inertia (simplified)
        geometry.moments_of_inertia = self._calculate_moments_of_inertia(solid_objects)
    
    def _calculate_moments_of_inertia(self, solid_objects) -> Dict[str, float]:
        """Calculate moments of inertia for solid objects"""
        
        moments = {
            "Ixx": 0.0,
            "Iyy": 0.0, 
            "Izz": 0.0,
            "Ixy": 0.0,
            "Ixz": 0.0,
            "Iyz": 0.0
        }
        
        for obj in solid_objects:
            try:
                if hasattr(obj, 'Shape') and hasattr(obj.Shape, 'MatrixOfInertia'):
                    matrix = obj.Shape.MatrixOfInertia
                    if matrix:
                        moments["Ixx"] += matrix.A11
                        moments["Iyy"] += matrix.A22
                        moments["Izz"] += matrix.A33
                        moments["Ixy"] += matrix.A12
                        moments["Ixz"] += matrix.A13
                        moments["Iyz"] += matrix.A23
            except:
                continue
        
        return moments
    
    def _get_solid_objects(self, doc) -> List:
        """Get all solid objects from document"""
        solid_objects = []
        
        for obj in doc.Objects:
            # Skip non-shape objects
            if not hasattr(obj, 'Shape'):
                continue
                
            # Skip invalid shapes
            if not obj.Shape.isValid():
                continue
                
            # Skip construction geometry
            if hasattr(obj, 'ViewObject') and hasattr(obj.ViewObject, 'Visibility'):
                if not obj.ViewObject.Visibility:
                    continue
            
            # Check if it's a solid
            if hasattr(obj.Shape, 'Volume') and obj.Shape.Volume > 0:
                solid_objects.append(obj)
                
            # Also include Part::Feature objects
            elif obj.TypeId.startswith('Part::'):
                solid_objects.append(obj)
        
        print(f"Found {len(solid_objects)} solid objects")
        return solid_objects
    
    def _classify_part_type(self, doc, geometry: ComprehensiveCADGeometry) -> PartType:
        """Intelligently classify the part type based on geometry"""
        
        dims = geometry.overall_dimensions
        if not dims:
            return PartType.UNKNOWN
        
        length = dims.get("length", 0)
        width = dims.get("width", 0)
        height = dims.get("height", 0)
        volume = geometry.volume
        
        # Calculate ratios
        max_dim = max(length, width, height)
        min_dim = min(length, width, height)
        aspect_ratio = max_dim / min_dim if min_dim > 0 else 1
        
        # Surface area to volume ratio (indicates wall thickness)
        sa_vol_ratio = geometry.surface_area / volume if volume > 0 else 0
        
        print(f"Classification metrics: AR={aspect_ratio:.2f}, SA/V={sa_vol_ratio:.2f}")
        
        # Classification logic
        if aspect_ratio > 8 and min_dim < max_dim * 0.2:
            return PartType.SHAFT_ROD
            
        elif sa_vol_ratio > 0.5 and max_dim > 50:  # High surface area, likely thin-walled
            if length > width * 1.5 and width > height * 2:
                return PartType.PLATE_PANEL
            else:
                return PartType.HOUSING_ENCLOSURE
                
        elif sa_vol_ratio > 1.0:  # Very high surface area ratio
            return PartType.THIN_WALLED_PART
            
        elif aspect_ratio > 3 and sa_vol_ratio < 0.3:
            return PartType.BRACKET_MOUNT
            
        elif max_dim < 100 and aspect_ratio < 2:
            # Analyze features to determine if it's a gear
            solid_objects = self._get_solid_objects(doc)
            if self._has_gear_characteristics(solid_objects):
                return PartType.GEAR_DRIVE
            else:
                return PartType.MECHANICAL_COMPONENT
                
        else:
            return PartType.MECHANICAL_COMPONENT
    
    def _has_gear_characteristics(self, objects) -> bool:
        """Check if objects have gear-like characteristics"""
        for obj in objects:
            try:
                if not hasattr(obj, 'Shape'):
                    continue
                    
                shape = obj.Shape
                
                # Look for cylindrical shape with many faces (teeth)
                if hasattr(shape, 'Faces') and len(shape.Faces) > 20:
                    # Check for circular symmetry
                    bbox = shape.BoundBox
                    diameter_x = bbox.XLength
                    diameter_y = bbox.YLength
                    height = bbox.ZLength
                    
                    # Gear-like proportions: circular cross-section
                    if abs(diameter_x - diameter_y) / max(diameter_x, diameter_y) < 0.2:
                        # Check if it has a central hole (typical of gears)
                        if self._has_central_hole(shape):
                            return True
                        
            except:
                continue
                
        return False
    
    def _has_central_hole(self, shape) -> bool:
        """Check if shape has a central hole"""
        try:
            center = shape.CenterOfMass
            
            # Look for cylindrical faces near the center
            for face in shape.Faces:
                if hasattr(face, 'Surface') and hasattr(face.Surface, 'Radius'):
                    face_center = face.CenterOfMass
                    distance_to_center = math.sqrt(
                        (face_center.x - center.x)**2 + 
                        (face_center.y - center.y)**2
                    )
                    
                    # If there's a cylindrical face near the center, likely a central hole
                    if distance_to_center < 5.0:
                        return True
                        
        except:
            pass
            
        return False
    
    # Feature extraction methods
    def _extract_all_features(self, doc, geometry: ComprehensiveCADGeometry):
        """Extract all geometric features from the document"""
        
        solid_objects = self._get_solid_objects(doc)
        if not solid_objects:
            print("No solid objects found for feature extraction")
            return
        
        # Extract features from each solid object
        feature_count = 0
        for obj in solid_objects:
            try:
                # Skip invalid shapes
                if not hasattr(obj, 'Shape') or not obj.Shape.isValid():
                    continue
                
                # Extract holes
                holes = self._extract_holes(obj)
                geometry.features.extend(holes)
                feature_count += len(holes)
                
                # Extract pockets
                pockets = self._extract_pockets(obj)
                geometry.features.extend(pockets)
                feature_count += len(pockets)
                
                # Extract bosses
                bosses = self._extract_bosses(obj)
                geometry.features.extend(bosses)
                feature_count += len(bosses)
                
                # Extract ribs
                ribs = self._extract_ribs(obj)
                geometry.features.extend(ribs)
                feature_count += len(ribs)
                
                # Extract fillets
                fillets = self._extract_fillets(obj)
                geometry.features.extend(fillets)
                feature_count += len(fillets)
                
                # Extract thin walls
                thin_walls = self._extract_thin_walls(obj)
                geometry.features.extend(thin_walls)
                feature_count += len(thin_walls)
                
                # Extract undercuts
                undercuts = self._extract_undercuts(obj)
                geometry.features.extend(undercuts)
                feature_count += len(undercuts)
                
            except Exception as e:
                print(f"Error extracting features from {obj.Name}: {e}")
                continue
        
        print(f"Extracted {feature_count} features from {len(solid_objects)} objects")
        
        # Calculate feature density
        if geometry.volume > 0:
            geometry.feature_density = feature_count / geometry.volume * 1000  # Features per 1000 mm³
            
        # Generate comprehensive manufacturability summary
        self._generate_manufacturability_summary(geometry)
    
    def _generate_manufacturability_summary(self, geometry: ComprehensiveCADGeometry):
        """Generate a comprehensive manufacturability summary based on all feature analyses"""
        
        # Initialize summary data
        manufacturability_summary = {
            "overall_complexity": 0.0,
            "critical_issues": [],
            "major_issues": [],
            "minor_issues": [],
            "recommended_processes": set(),
            "cost_drivers": set(),
            "feature_specific_issues": {},
            "overall_rating": ""
        }
        
        # Track feature counts and complexity scores
        feature_counts = {}
        total_complexity = 0.0
        feature_complexities = {}
        
        # Analyze all features
        for feature in geometry.features:
            feature_type = feature.feature_type
            
            # Count features by type
            if feature_type not in feature_counts:
                feature_counts[feature_type] = 0
                feature_complexities[feature_type] = 0.0
            
            feature_counts[feature_type] += 1
            
            # Collect manufacturability data
            if "manufacturability_issues" in feature.properties:
                issues = feature.properties["manufacturability_issues"]
                
                # Track feature-specific issues
                if feature_type not in manufacturability_summary["feature_specific_issues"]:
                    manufacturability_summary["feature_specific_issues"][feature_type] = []
                
                for issue in issues:
                    manufacturability_summary["feature_specific_issues"][feature_type].append(issue)
                    
                    # Categorize issues by severity
                    severity = feature.properties.get("severity", "medium")
                    if severity == "high" or "critical" in issue.lower():
                        if issue not in manufacturability_summary["critical_issues"]:
                            manufacturability_summary["critical_issues"].append(issue)
                    elif "high" in issue.lower() or "severe" in issue.lower():
                        if issue not in manufacturability_summary["major_issues"]:
                            manufacturability_summary["major_issues"].append(issue)
                    else:
                        if issue not in manufacturability_summary["minor_issues"]:
                            manufacturability_summary["minor_issues"].append(issue)
            
            # Collect recommended processes
            if "recommended_processes" in feature.properties:
                for process in feature.properties["recommended_processes"]:
                    manufacturability_summary["recommended_processes"].add(process)
            
            # Collect cost drivers
            if "cost_drivers" in feature.properties:
                for driver in feature.properties["cost_drivers"]:
                    manufacturability_summary["cost_drivers"].add(driver)
            
            # Track complexity
            complexity = feature.properties.get("complexity_score", 1.0)
            total_complexity += complexity
            feature_complexities[feature_type] += complexity
        
        # Calculate overall complexity
        total_features = sum(feature_counts.values())
        if total_features > 0:
            manufacturability_summary["overall_complexity"] = total_complexity / total_features
            
            # Calculate normalized complexity by feature type
            for feature_type, count in feature_counts.items():
                if count > 0:
                    feature_complexities[feature_type] /= count
        
        # Determine overall rating
        if len(manufacturability_summary["critical_issues"]) > 0:
            manufacturability_summary["overall_rating"] = "Poor - Critical issues must be addressed"
        elif len(manufacturability_summary["major_issues"]) > 3:
            manufacturability_summary["overall_rating"] = "Fair - Multiple major issues need attention"
        elif len(manufacturability_summary["major_issues"]) > 0:
            manufacturability_summary["overall_rating"] = "Good - Some issues need attention"
        elif len(manufacturability_summary["minor_issues"]) > 5:
            manufacturability_summary["overall_rating"] = "Very Good - Minor issues to consider"
        else:
            manufacturability_summary["overall_rating"] = "Excellent - Few or no manufacturability concerns"
        
        # Convert sets to lists for JSON serialization
        manufacturability_summary["recommended_processes"] = list(manufacturability_summary["recommended_processes"])
        manufacturability_summary["cost_drivers"] = list(manufacturability_summary["cost_drivers"])
        
        # Add feature counts and complexities
        manufacturability_summary["feature_counts"] = feature_counts
        manufacturability_summary["feature_complexities"] = feature_complexities
        
        # Store the summary in the geometry object
        geometry.manufacturability_summary = manufacturability_summary
    
    def _analyze_wall_thickness(self, doc, geometry: ComprehensiveCADGeometry):
        """Analyze wall thickness throughout the model"""
        
        solid_objects = self._get_solid_objects(doc)
        if not solid_objects:
            return
        
        # Get overall dimensions for reference
        dims = geometry.overall_dimensions
        max_dim = max(dims.get("length", 0), dims.get("width", 0), dims.get("height", 0))
        
        # Define sampling parameters based on part size
        sample_count = min(max(int(max_dim / 5), 20), 200)  # Between 20 and 200 samples
        
        # Combine all shapes for analysis
        combined_shape = None
        for obj in solid_objects:
            try:
                if not hasattr(obj, 'Shape') or not obj.Shape.isValid():
                    continue
                    
                if combined_shape is None:
                    combined_shape = obj.Shape.copy()
                else:
                    combined_shape = combined_shape.fuse(obj.Shape)
            except:
                continue
        
        if not combined_shape:
            return
        
        # Sample points on the surface
        wall_thickness_samples = []
        critical_count = 0
        
        try:
            # Get bounding box for sampling reference
            bbox = combined_shape.BoundBox
            x_range = bbox.XMax - bbox.XMin
            y_range = bbox.YMax - bbox.YMin
            z_range = bbox.ZMax - bbox.ZMin
            
            # Sample points on each face
            for face_idx, face in enumerate(combined_shape.Faces):
                # Skip very small faces
                if face.Area < 0.01 * combined_shape.Area:
                    continue
                    
                # Get face center and normal
                face_center = face.CenterOfMass
                face_normal = face.normalAt(0, 0)  # Approximate normal
                
                # Create sampling points on this face
                for _ in range(max(1, int(sample_count * face.Area / combined_shape.Area))):
                    # Generate random point on face (simplified)
                    u = random.random()
                    v = random.random()
                    
                    # Simple approximation of point on face
                    sample_point = FreeCAD.Vector(
                        face_center.x + (u - 0.5) * x_range * 0.1,
                        face_center.y + (v - 0.5) * y_range * 0.1,
                        face_center.z + (0) * z_range * 0.1
                    )
                    
                    # Project point to face
                    projected_point = face.projectPoint(sample_point, "NormalToSurface")
                    
                    # Measure thickness at this point
                    thickness = self._measure_thickness_at_point(combined_shape, projected_point, face_normal)
                    
                    if thickness > 0:
                        # Determine if this is a critical thin wall
                        is_critical = thickness < 0.5  # Less than 0.5mm is critical
                        severity = "high" if thickness < 0.5 else "medium" if thickness < 1.0 else "low"
                        
                        if is_critical:
                            critical_count += 1
                        
                        # Add to samples
                        wall_thickness_samples.append(WallThicknessAnalysis(
                            location={
                                "x": projected_point.x,
                                "y": projected_point.y,
                                "z": projected_point.z
                            },
                            thickness=thickness,
                            is_critical=is_critical,
                            severity=severity
                        ))
        except Exception as e:
            print(f"Error in wall thickness analysis: {e}")
            traceback.print_exc()
        
        # Store results
        geometry.wall_thickness_analysis = wall_thickness_samples
        print(f"Wall thickness analysis: {len(wall_thickness_samples)} samples, {critical_count} critical")
    
    def _measure_thickness_at_point(self, shape, point, normal, max_distance=1000.0) -> float:
        """Measure wall thickness at a specific point in a specific direction"""
        try:
            # Create a line from the point in the direction of the normal
            line = Part.LineSegment(point, point.add(normal.multiply(max_distance)))
            
            # Create a line in the opposite direction
            line_reverse = Part.LineSegment(point, point.add(normal.multiply(-max_distance)))
            
            # Find intersections with the shape
            intersections_forward = shape.section(line.toShape()).Vertexes
            intersections_reverse = shape.section(line_reverse.toShape()).Vertexes
            
            # Find closest intersection point in forward direction
            min_dist_forward = max_distance
            for v in intersections_forward:
                dist = point.distanceToPoint(v.Point)
                if dist > 0.1 and dist < min_dist_forward:  # Avoid self-intersection
                    min_dist_forward = dist
            
            # Find closest intersection point in reverse direction
            min_dist_reverse = max_distance
            for v in intersections_reverse:
                dist = point.distanceToPoint(v.Point)
                if dist > 0.1 and dist < min_dist_reverse:  # Avoid self-intersection
                    min_dist_reverse = dist
            
            # Calculate thickness (minimum of both directions)
            if min_dist_forward < max_distance or min_dist_reverse < max_distance:
                return min(min_dist_forward, min_dist_reverse)
            else:
                return 0.0  # No intersection found
                
        except Exception as e:
            print(f"Error measuring thickness: {e}")
            return 0.0
    
    def _perform_manufacturing_analysis(self, doc, geometry: ComprehensiveCADGeometry):
        """Perform comprehensive manufacturing-specific analysis"""
        
        print("🔧 Analyzing manufacturing characteristics...")
        
        # Draft analysis for molding processes
        geometry.draft_analysis = self._analyze_draft_angles(doc, geometry)
        
        # Undercut analysis for molding complexity
        geometry.undercut_analysis = self._analyze_undercuts_comprehensive(doc, geometry)
        
        # Stress concentration analysis for structural integrity
        geometry.stress_concentration_analysis = self._analyze_stress_concentrations(doc, geometry)
        
        # Parting line analysis for molding setup
        geometry.parting_line_analysis = self._analyze_parting_lines(doc, geometry)
        
        # Material flow analysis for molding processes
        geometry.material_flow_analysis = self._analyze_material_flow(doc, geometry)
    
    def _analyze_draft_angles(self, doc, geometry):
        """Analyze draft angles for molding processes"""
        
        analysis = {
            "surfaces_analyzed": 0,
            "surfaces_with_draft": 0,
            "surfaces_without_draft": 0,
            "minimum_draft_angle": float('inf'),
            "average_draft_angle": 0.0,
            "maximum_draft_angle": 0.0,
            "draft_violations": []
        }
        
        solid_objects = self._get_solid_objects(doc)
        draft_angles = []
        
        for obj in solid_objects:
            if not hasattr(obj, 'Shape'):
                continue
                
            shape = obj.Shape
            
            for i, face in enumerate(shape.Faces):
                try:
                    analysis["surfaces_analyzed"] += 1
                    
                    # Estimate draft angle
                    draft_angle = self._estimate_draft_angle(face)
                    
                    if draft_angle is not None:
                        draft_angles.append(draft_angle)
                        
                        if draft_angle >= 0.5:  # Minimum acceptable draft
                            analysis["surfaces_with_draft"] += 1
                        else:
                            analysis["surfaces_without_draft"] += 1
                            analysis["draft_violations"].append({
                                "face_id": f"face_{i}",
                                "draft_angle": draft_angle,
                                "location": [face.CenterOfMass.x, face.CenterOfMass.y, face.CenterOfMass.z],
                                "severity": "high" if draft_angle < 0.1 else "medium"
                            })
                    
                except Exception as e:
                    print(f"Warning: Error analyzing draft for face {i}: {e}")
                    continue
        
        # Calculate statistics
        if draft_angles:
            analysis["minimum_draft_angle"] = min(draft_angles)
            analysis["average_draft_angle"] = sum(draft_angles) / len(draft_angles)
            analysis["maximum_draft_angle"] = max(draft_angles)
        
        return analysis
        
    def _estimate_draft_angle(self, face):
        """Estimate draft angle of a face"""
        try:
            # Check if face normal deviates from vertical
            face_normal = face.normalAt(0, 0)
            vertical = FreeCAD.Vector(0, 0, 1)
            
            # Calculate angle from vertical
            dot_product = abs(face_normal.dot(vertical))
            angle_from_vertical = math.degrees(math.acos(min(1.0, dot_product)))
            
            # Draft angle is the deviation from vertical
            draft_angle = min(angle_from_vertical, 90 - angle_from_vertical)
            
            return draft_angle
            
        except:
            return None
    
    def _analyze_undercuts_comprehensive(self, doc, geometry):
        """Perform comprehensive undercut detection and severity assessment"""
        
        analysis = {
            "undercut_count": 0,
            "undercut_features": [],
            "severity_score": 0.0,
            "primary_pull_direction": {"x": 0, "y": 0, "z": 1},  # Default to Z-axis
            "alternative_directions": [],
            "manufacturability_impact": ""
        }
        
        # Get solid objects
        solid_objects = self._get_solid_objects(doc)
        if not solid_objects:
            return analysis
            
        # Define potential pull directions to test
        pull_directions = [
            FreeCAD.Vector(0, 0, 1),   # Z+
            FreeCAD.Vector(0, 0, -1),  # Z-
            FreeCAD.Vector(1, 0, 0),   # X+
            FreeCAD.Vector(-1, 0, 0),  # X-
            FreeCAD.Vector(0, 1, 0),   # Y+
            FreeCAD.Vector(0, -1, 0)   # Y-
        ]
        
        # Test each direction
        direction_results = []
        
        for direction in pull_directions:
            undercuts = []
            total_severity = 0
            
            for obj in solid_objects:
                if not hasattr(obj, 'Shape'):
                    continue
                    
                # Detect undercuts in this object with this pull direction
                obj_undercuts = self._detect_undercuts_in_object(obj.Shape, direction)
                undercuts.extend(obj_undercuts)
                
                # Sum severity scores
                total_severity += sum(u.get("severity_score", 0) for u in obj_undercuts)
            
            direction_results.append({
                "direction": {"x": direction.x, "y": direction.y, "z": direction.z},
                "undercut_count": len(undercuts),
                "total_severity": total_severity,
                "undercuts": undercuts
            })
        
        # Find best direction (with fewest/least severe undercuts)
        direction_results.sort(key=lambda r: (r["undercut_count"], r["total_severity"]))
        best_result = direction_results[0] if direction_results else None
        
        if best_result:
            analysis["primary_pull_direction"] = best_result["direction"]
            analysis["undercut_count"] = best_result["undercut_count"]
            analysis["undercut_features"] = best_result["undercuts"]
            analysis["severity_score"] = best_result["total_severity"]
            
            # Add alternative directions
            for result in direction_results[1:3]:  # Next two best directions
                if result["undercut_count"] <= best_result["undercut_count"] + 2:  # Only if reasonably close
                    analysis["alternative_directions"].append(result["direction"])
        
        # Assess manufacturability impact
        if analysis["undercut_count"] == 0:
            analysis["manufacturability_impact"] = "No impact - no undercuts detected"
        elif analysis["undercut_count"] <= 2 and analysis["severity_score"] < 5:
            analysis["manufacturability_impact"] = "Minor impact - simple side-action may be required"
        elif analysis["undercut_count"] <= 5 and analysis["severity_score"] < 15:
            analysis["manufacturability_impact"] = "Moderate impact - multiple side-actions required"
        else:
            analysis["manufacturability_impact"] = "Severe impact - complex tooling required, consider redesign"
        
        return analysis
        
    def _detect_undercuts_in_object(self, shape, pull_direction):
        """Detect undercuts in an object for a given pull direction"""
        undercuts = []
        
        try:
            for i, face in enumerate(shape.Faces):
                # Get face normal
                face_normal = face.normalAt(0, 0)
                
                # Calculate dot product with pull direction
                dot_product = face_normal.dot(pull_direction)
                
                # If dot product is negative, this face points away from pull direction
                if dot_product < -0.1:  # Small threshold to account for numerical errors
                    # Calculate severity based on angle and area
                    angle = math.degrees(math.acos(min(1.0, max(-1.0, dot_product))))
                    severity = (angle / 180.0) * (face.Area / shape.Area) * 10.0
                    
                    undercuts.append({
                        "face_id": f"face_{i}",
                        "location": [face.CenterOfMass.x, face.CenterOfMass.y, face.CenterOfMass.z],
                        "area": face.Area,
                        "angle": angle,
                        "severity_score": severity,
                        "severity_level": "high" if severity > 5 else "medium" if severity > 2 else "low"
                    })
        except Exception as e:
            print(f"Error in undercut detection: {e}")
        
        return undercuts
        
    def _analyze_stress_concentrations(self, doc, geometry):
        """Analyze stress concentration areas in the model"""
        
        analysis = {
            "concentration_points": [],
            "risk_level": "low",
            "recommendations": []
        }
        
        solid_objects = self._get_solid_objects(doc)
        if not solid_objects:
            return analysis
            
        # Identify sharp internal corners and small fillets
        for obj in solid_objects:
            if not hasattr(obj, 'Shape'):
                continue
                
            shape = obj.Shape
            
            # Analyze edges for sharp angles
            for i, edge in enumerate(shape.Edges):
                try:
                    # Check if edge is curved and has small radius
                    if edge.curvatureAt(0) > 0:  # Curved edge
                        radius = 1.0 / edge.curvatureAt(0)
                        
                        # Small radius indicates stress concentration
                        if radius < 1.0:  # Threshold for small radius
                            # Find adjacent faces
                            adjacent_faces = []
                            for face in shape.Faces:
                                if edge in face.Edges:
                                    adjacent_faces.append(face)
                            
                            # Check if this is an internal corner
                            is_internal = len(adjacent_faces) >= 2
                            if is_internal:
                                # Calculate severity based on radius
                                severity = 1.0 / max(0.1, radius)  # Smaller radius = higher severity
                                
                                # Get edge midpoint
                                param = edge.FirstParameter + (edge.LastParameter - edge.FirstParameter) / 2
                                point = edge.valueAt(param)
                                
                                analysis["concentration_points"].append({
                                    "edge_id": f"edge_{i}",
                                    "location": [point.x, point.y, point.z],
                                    "radius": radius,
                                    "severity": severity,
                                    "severity_level": "high" if severity > 5 else "medium" if severity > 2 else "low"
                                })
                except Exception as e:
                    print(f"Warning: Error analyzing edge {i} for stress concentration: {e}")
                    continue
        
        # Determine overall risk level
        if not analysis["concentration_points"]:
            analysis["risk_level"] = "low"
            analysis["recommendations"].append("No significant stress concentration points detected")
        else:
            # Calculate max severity
            max_severity = max([p["severity"] for p in analysis["concentration_points"]], default=0)
            
            if max_severity > 5:
                analysis["risk_level"] = "high"
                analysis["recommendations"].append("Increase fillet radius in high-stress areas")
                analysis["recommendations"].append("Consider material reinforcement at critical junctions")
            elif max_severity > 2:
                analysis["risk_level"] = "medium"
                analysis["recommendations"].append("Review fillet sizes at medium-severity points")
            else:
                analysis["risk_level"] = "low"
                analysis["recommendations"].append("Minor stress concentrations present but likely acceptable")
        
        return analysis
    
    def _analyze_parting_lines(self, doc, geometry):
        """Analyze potential parting lines for molding"""
        
        analysis = {
            "recommended_parting_line": {},
            "alternative_parting_lines": [],
            "complexity": "medium",
            "recommendations": []
        }
        
        solid_objects = self._get_solid_objects(doc)
        if not solid_objects:
            return analysis
            
        # Get bounding box to find major dimensions
        combined_bbox = None
        for obj in solid_objects:
            if not hasattr(obj, 'Shape'):
                continue
                
            if combined_bbox is None:
                combined_bbox = obj.Shape.BoundBox
            else:
                combined_bbox.add(obj.Shape.BoundBox)
        
        if not combined_bbox:
            return analysis
            
        # Find major dimensions
        x_size = combined_bbox.XLength
        y_size = combined_bbox.YLength
        z_size = combined_bbox.ZLength
        
        # Determine primary parting direction based on largest dimension
        primary_direction = "XY"
        if z_size >= x_size and z_size >= y_size:
            primary_direction = "XY"  # Parting line on XY plane
            parting_z = combined_bbox.ZMin + (combined_bbox.ZLength / 2)
            analysis["recommended_parting_line"] = {
                "direction": "Z",
                "plane": "XY",
                "position": parting_z,
                "complexity": "low" if z_size > 1.5 * max(x_size, y_size) else "medium"
            }
            
        elif y_size >= x_size and y_size >= z_size:
            primary_direction = "XZ"  # Parting line on XZ plane
            parting_y = combined_bbox.YMin + (combined_bbox.YLength / 2)
            analysis["recommended_parting_line"] = {
                "direction": "Y",
                "plane": "XZ",
                "position": parting_y,
                "complexity": "low" if y_size > 1.5 * max(x_size, z_size) else "medium"
            }
            
        else:
            primary_direction = "YZ"  # Parting line on YZ plane
            parting_x = combined_bbox.XMin + (combined_bbox.XLength / 2)
            analysis["recommended_parting_line"] = {
                "direction": "X",
                "plane": "YZ",
                "position": parting_x,
                "complexity": "low" if x_size > 1.5 * max(y_size, z_size) else "medium"
            }
        
        # Add alternative parting lines
        if primary_direction != "XY":
            parting_z = combined_bbox.ZMin + (combined_bbox.ZLength / 2)
            analysis["alternative_parting_lines"].append({
                "direction": "Z",
                "plane": "XY",
                "position": parting_z,
                "complexity": "medium"
            })
            
        if primary_direction != "XZ":
            parting_y = combined_bbox.YMin + (combined_bbox.YLength / 2)
            analysis["alternative_parting_lines"].append({
                "direction": "Y",
                "plane": "XZ",
                "position": parting_y,
                "complexity": "medium"
            })
            
        if primary_direction != "YZ":
            parting_x = combined_bbox.XMin + (combined_bbox.XLength / 2)
            analysis["alternative_parting_lines"].append({
                "direction": "X",
                "plane": "YZ",
                "position": parting_x,
                "complexity": "medium"
            })
        
        # Add recommendations
        if analysis["recommended_parting_line"].get("complexity") == "low":
            analysis["recommendations"].append("Standard parting line along primary axis is recommended")
        else:
            analysis["recommendations"].append("Consider multiple parting lines for complex geometry")
            analysis["recommendations"].append("Evaluate flash and witness line visibility on cosmetic surfaces")
        
        return analysis
        
    def _analyze_material_flow(self, doc, geometry):
        """Analyze material flow for injection molding processes"""
        
        analysis = {
            "flow_characteristics": {},
            "thin_sections": [],
            "thick_sections": [],
            "potential_issues": [],
            "gate_recommendations": []
        }
        
        solid_objects = self._get_solid_objects(doc)
        if not solid_objects:
            return analysis
            
        # Analyze each solid object
        for obj in solid_objects:
            if not hasattr(obj, 'Shape'):
                continue
                
            shape = obj.Shape
            bbox = shape.BoundBox
            
            # Calculate basic flow metrics
            max_dimension = max(bbox.XLength, bbox.YLength, bbox.ZLength)
            min_dimension = min(bbox.XLength, bbox.YLength, bbox.ZLength)
            aspect_ratio = max_dimension / max(min_dimension, 0.001)  # Avoid division by zero
            
            # Find wall thickness variations
            thickness_values = []
            
            # Sample points throughout the model to estimate thickness
            for face in shape.Faces:
                try:
                    # Get face center
                    face_center = face.CenterOfMass
                    face_normal = face.normalAt(0, 0)
                    
                    # Create a line through the part in the normal direction
                    line = Part.Line(face_center, face_center.add(face_normal.multiply(max_dimension * 2)))
                    
                    # Find intersections with the shape
                    intersections = shape.section(line.toShape())
                    
                    if not intersections.Vertexes:
                        continue
                        
                    # Calculate distance between intersection points
                    if len(intersections.Vertexes) >= 2:
                        p1 = intersections.Vertexes[0].Point
                        p2 = intersections.Vertexes[1].Point
                        thickness = p1.distanceToPoint(p2)
                        
                        if thickness > 0.1:  # Ignore very small values
                            thickness_values.append(thickness)
                except Exception as e:
                    continue
            
            # Analyze thickness distribution
            if thickness_values:
                avg_thickness = sum(thickness_values) / len(thickness_values)
                max_thickness = max(thickness_values)
                min_thickness = min(thickness_values)
                thickness_ratio = max_thickness / max(min_thickness, 0.001)
                
                # Record flow characteristics
                analysis["flow_characteristics"] = {
                    "average_wall_thickness": avg_thickness,
                    "min_wall_thickness": min_thickness,
                    "max_wall_thickness": max_thickness,
                    "thickness_ratio": thickness_ratio,
                    "aspect_ratio": aspect_ratio,
                    "volume": shape.Volume,
                    "surface_area": shape.Area
                }
                
                # Identify thin sections (potential flow restrictions)
                for i, thickness in enumerate(thickness_values):
                    if thickness < avg_thickness * 0.6:  # Significantly thinner than average
                        analysis["thin_sections"].append({
                            "thickness": thickness,
                            "severity": "high" if thickness < avg_thickness * 0.4 else "medium",
                            "ratio_to_average": thickness / avg_thickness
                        })
                
                # Identify thick sections (potential sink marks)
                for i, thickness in enumerate(thickness_values):
                    if thickness > avg_thickness * 1.5:  # Significantly thicker than average
                        analysis["thick_sections"].append({
                            "thickness": thickness,
                            "severity": "high" if thickness > avg_thickness * 2 else "medium",
                            "ratio_to_average": thickness / avg_thickness
                        })
        
        # Generate potential issues and recommendations
        if analysis["thin_sections"]:
            analysis["potential_issues"].append({
                "type": "flow_restriction",
                "description": "Thin sections may restrict material flow",
                "severity": "high" if any(s["severity"] == "high" for s in analysis["thin_sections"]) else "medium"
            })
            
        if analysis["thick_sections"]:
            analysis["potential_issues"].append({
                "type": "sink_marks",
                "description": "Thick sections may develop sink marks",
                "severity": "high" if any(s["severity"] == "high" for s in analysis["thick_sections"]) else "medium"
            })
            
        # Add gate recommendations
        if analysis["flow_characteristics"]:
            aspect_ratio = analysis["flow_characteristics"].get("aspect_ratio", 1)
            
            if aspect_ratio > 3:
                analysis["gate_recommendations"].append("Consider multiple gates for balanced flow in elongated part")
            else:
                analysis["gate_recommendations"].append("Single gate at thickest section should provide adequate flow")
                
            if analysis["thin_sections"]:
                analysis["gate_recommendations"].append("Position gate to ensure flow to thin sections before material cools")
        
        return analysis
        
    def _analyze_housing(self, doc, geometry):
        """Analyze housing-specific characteristics"""
        
        analysis = {
            "type": "housing",
            "features": {
                "mounting_points": [],
                "access_panels": [],
                "cable_routing": [],
                "ventilation": []
            },
            "manufacturability": {
                "recommended_process": "",
                "draft_quality": "",
                "wall_consistency": "",
                "assembly_considerations": []
            },
            "recommendations": []
        }
        
        solid_objects = self._get_solid_objects(doc)
        if not solid_objects:
            return analysis
            
        # Analyze housing characteristics
        total_volume = 0
        total_surface_area = 0
        has_thin_walls = False
        has_mounting_features = False
        has_complex_curves = False
        
        for obj in solid_objects:
            if not hasattr(obj, 'Shape'):
                continue
                
            shape = obj.Shape
            total_volume += shape.Volume
            total_surface_area += shape.Area
            
            # Check for mounting holes (cylindrical features)
            for face in shape.Faces:
                if face.Surface.TypeId == 'Part::GeomCylinder':
                    radius = face.Surface.Radius
                    if 1.0 < radius < 10.0:  # Typical mounting hole size range
                        # Get position
                        center = face.CenterOfMass
                        analysis["features"]["mounting_points"].append({
                            "position": [center.x, center.y, center.z],
                            "radius": radius,
                            "type": "threaded" if radius < 5.0 else "through"
                        })
                        has_mounting_features = True
            
            # Check for thin walls
            if geometry.thin_walls and len(geometry.thin_walls) > 0:
                has_thin_walls = True
            
            # Check for complex curved surfaces
            for face in shape.Faces:
                if face.Surface.TypeId in ['Part::GeomBezierSurface', 'Part::GeomBSplineSurface']:
                    has_complex_curves = True
                    break
        
        # Determine manufacturability characteristics
        if total_volume < 125000:  # Small housing
            if has_complex_curves:
                analysis["manufacturability"]["recommended_process"] = "Injection molding"
            else:
                analysis["manufacturability"]["recommended_process"] = "Injection molding or machining"
        else:  # Large housing
            if has_thin_walls:
                analysis["manufacturability"]["recommended_process"] = "Injection molding or die casting"
            else:
                analysis["manufacturability"]["recommended_process"] = "Machining or casting"
        
        # Draft quality assessment
        if geometry.draft_analysis:
            avg_draft = geometry.draft_analysis.get("average_draft_angle", 0)
            if avg_draft > 1.0:
                analysis["manufacturability"]["draft_quality"] = "good"
            elif avg_draft > 0.5:
                analysis["manufacturability"]["draft_quality"] = "acceptable"
            else:
                analysis["manufacturability"]["draft_quality"] = "poor"
        
        # Wall consistency assessment
        if geometry.material_flow_analysis and "flow_characteristics" in geometry.material_flow_analysis:
            thickness_ratio = geometry.material_flow_analysis["flow_characteristics"].get("thickness_ratio", 1)
            if thickness_ratio < 2.0:
                analysis["manufacturability"]["wall_consistency"] = "good"
            elif thickness_ratio < 3.0:
                analysis["manufacturability"]["wall_consistency"] = "acceptable"
            else:
                analysis["manufacturability"]["wall_consistency"] = "poor"
        
        # Add recommendations
        if has_mounting_features and len(analysis["features"]["mounting_points"]) < 3:
            analysis["recommendations"].append("Add additional mounting points for stability")
        
        if has_thin_walls:
            analysis["recommendations"].append("Consider adding ribs to reinforce thin wall sections")
        
        if not has_mounting_features:
            analysis["recommendations"].append("Add mounting features for installation")
        
        if analysis["manufacturability"]["draft_quality"] == "poor":
            analysis["recommendations"].append("Increase draft angles to improve moldability")
        
        return analysis
        
    def _analyze_bracket(self, doc, geometry):
        """Analyze bracket-specific characteristics"""
        
        analysis = {
            "type": "bracket",
            "features": {
                "mounting_holes": [],
                "reinforcement_ribs": [],
                "gussets": []
            },
            "structural": {
                "strength_assessment": "",
                "weak_points": [],
                "load_bearing_capacity": ""
            },
            "manufacturability": {
                "recommended_process": "",
                "complexity": ""
            },
            "recommendations": []
        }
        
        solid_objects = self._get_solid_objects(doc)
        if not solid_objects:
            return analysis
            
        # Analyze bracket characteristics
        total_volume = 0
        has_mounting_holes = False
        has_ribs = False
        has_thin_sections = False
        mounting_hole_count = 0
        
        for obj in solid_objects:
            if not hasattr(obj, 'Shape'):
                continue
                
            shape = obj.Shape
            total_volume += shape.Volume
            bbox = shape.BoundBox
            
            # Check for mounting holes
            for face in shape.Faces:
                if face.Surface.TypeId == 'Part::GeomCylinder':
                    radius = face.Surface.Radius
                    if 1.0 < radius < 8.0:  # Typical mounting hole size range
                        # Get position
                        center = face.CenterOfMass
                        analysis["features"]["mounting_holes"].append({
                            "position": [center.x, center.y, center.z],
                            "radius": radius,
                            "type": "threaded" if radius < 4.0 else "through"
                        })
                        has_mounting_holes = True
                        mounting_hole_count += 1
            
            # Check for ribs
            if geometry.ribs and len(geometry.ribs) > 0:
                has_ribs = True
                for rib in geometry.ribs:
                    analysis["features"]["reinforcement_ribs"].append({
                        "height": rib.properties.get("height", 0),
                        "thickness": rib.properties.get("thickness", 0),
                        "length": rib.properties.get("length", 0)
                    })
            
            # Check for thin sections that might be weak points
            if geometry.material_flow_analysis and "thin_sections" in geometry.material_flow_analysis:
                if geometry.material_flow_analysis["thin_sections"]:
                    has_thin_sections = True
                    for section in geometry.material_flow_analysis["thin_sections"]:
                        if section.get("severity") == "high":
                            analysis["structural"]["weak_points"].append({
                                "type": "thin_section",
                                "thickness": section.get("thickness", 0),
                                "severity": "high"
                            })
        
        # Assess structural strength
        if has_ribs and not has_thin_sections:
            analysis["structural"]["strength_assessment"] = "good"
            analysis["structural"]["load_bearing_capacity"] = "high"
        elif has_ribs and has_thin_sections:
            analysis["structural"]["strength_assessment"] = "moderate"
            analysis["structural"]["load_bearing_capacity"] = "medium"
        elif not has_ribs and not has_thin_sections:
            analysis["structural"]["strength_assessment"] = "moderate"
            analysis["structural"]["load_bearing_capacity"] = "medium"
        else:
            analysis["structural"]["strength_assessment"] = "poor"
            analysis["structural"]["load_bearing_capacity"] = "low"
        
        # Determine manufacturability characteristics
        if total_volume < 50000:  # Small bracket
            if has_ribs:
                analysis["manufacturability"]["recommended_process"] = "Injection molding or die casting"
                analysis["manufacturability"]["complexity"] = "medium"
            else:
                analysis["manufacturability"]["recommended_process"] = "Machining or sheet metal forming"
                analysis["manufacturability"]["complexity"] = "low"
        else:  # Large bracket
            if has_ribs:
                analysis["manufacturability"]["recommended_process"] = "Die casting or investment casting"
                analysis["manufacturability"]["complexity"] = "high"
            else:
                analysis["manufacturability"]["recommended_process"] = "Machining or welded assembly"
                analysis["manufacturability"]["complexity"] = "medium"
        
        # Add recommendations
        if not has_mounting_holes or mounting_hole_count < 2:
            analysis["recommendations"].append("Add sufficient mounting holes for secure attachment")
        
        if has_thin_sections and not has_ribs:
            analysis["recommendations"].append("Add reinforcement ribs to strengthen thin sections")
        
        if analysis["structural"]["strength_assessment"] == "poor":
            analysis["recommendations"].append("Increase material thickness in weak areas")
            analysis["recommendations"].append("Consider adding gussets at high-stress corners")
        
        return analysis
        
    def _analyze_gear(self, doc, geometry):
        """Analyze gear-specific characteristics"""
        
        analysis = {
            "type": "gear",
            "features": {
                "teeth": {
                    "count": 0,
                    "profile": "",
                    "quality": ""
                },
                "hub": {},
                "keyway": {}
            },
            "manufacturability": {
                "recommended_process": "",
                "tolerance_class": "",
                "complexity": ""
            },
            "recommendations": []
        }
        
        solid_objects = self._get_solid_objects(doc)
        if not solid_objects:
            return analysis
            
        # Analyze gear characteristics
        total_volume = 0
        cylindrical_faces = []
        planar_faces = []
        potential_teeth = []
        
        for obj in solid_objects:
            if not hasattr(obj, 'Shape'):
                continue
                
            shape = obj.Shape
            total_volume += shape.Volume
            
            # Categorize faces
            for face in shape.Faces:
                if face.Surface.TypeId == 'Part::GeomCylinder':
                    cylindrical_faces.append(face)
                elif face.Surface.TypeId == 'Part::GeomPlane':
                    planar_faces.append(face)
                elif face.Surface.TypeId == 'Part::GeomBSplineSurface':
                    # Complex surfaces might be gear teeth
                    potential_teeth.append(face)
        
        # Estimate gear parameters
        # Find main cylindrical face (likely the pitch diameter)
        main_cylinder = None
        max_cylinder_radius = 0
        for face in cylindrical_faces:
            radius = face.Surface.Radius
            if radius > max_cylinder_radius:
                max_cylinder_radius = radius
                main_cylinder = face
        
        # Estimate number of teeth based on edge count or face patterns
        estimated_teeth = 0
        if potential_teeth:
            # Group similar faces that might represent teeth
            estimated_teeth = len(potential_teeth) // 2  # Rough estimate, each tooth has multiple faces
        elif main_cylinder:
            # Estimate based on circumference and typical tooth size
            circumference = 2 * math.pi * max_cylinder_radius
            # Assume average tooth width of 3-5mm for medium-sized gears
            estimated_teeth = int(circumference / 4)  # Using 4mm as average tooth width
        
        # Populate gear features
        if estimated_teeth > 0:
            analysis["features"]["teeth"]["count"] = estimated_teeth
            
            # Determine tooth profile based on shape characteristics
            if potential_teeth and any(f.Surface.TypeId == 'Part::GeomBSplineSurface' for f in potential_teeth):
                analysis["features"]["teeth"]["profile"] = "involute"
            else:
                analysis["features"]["teeth"]["profile"] = "straight"
            
            # Assess tooth quality based on geometry precision
            if len(potential_teeth) > estimated_teeth * 3:  # High detail level
                analysis["features"]["teeth"]["quality"] = "high"
            else:
                analysis["features"]["teeth"]["quality"] = "medium"
        
        # Identify hub features
        central_hole = None
        for face in cylindrical_faces:
            if face.Surface.Radius < max_cylinder_radius * 0.3:  # Small central hole
                central_hole = face
                break
        
        if central_hole:
            center = central_hole.CenterOfMass
            analysis["features"]["hub"] = {
                "diameter": central_hole.Surface.Radius * 2,
                "position": [center.x, center.y, center.z]
            }
            
            # Check for keyway
            # A keyway might appear as a small planar face intersecting with the central hole
            for face in planar_faces:
                if self._is_face_near_point(face, center, central_hole.Surface.Radius * 1.5):
                    analysis["features"]["keyway"] = {
                        "detected": True,
                        "type": "standard"
                    }
                    break
        
        # Determine manufacturability characteristics
        if estimated_teeth > 0:
            if estimated_teeth > 50:  # Fine-toothed gear
                analysis["manufacturability"]["recommended_process"] = "Hobbing or wire EDM"
                analysis["manufacturability"]["complexity"] = "high"
                analysis["manufacturability"]["tolerance_class"] = "precision"
            elif estimated_teeth > 20:  # Medium-toothed gear
                analysis["manufacturability"]["recommended_process"] = "Hobbing, milling, or powder metallurgy"
                analysis["manufacturability"]["complexity"] = "medium"
                analysis["manufacturability"]["tolerance_class"] = "standard"
            else:  # Coarse-toothed gear
                analysis["manufacturability"]["recommended_process"] = "Milling, casting, or injection molding"
                analysis["manufacturability"]["complexity"] = "low"
                analysis["manufacturability"]["tolerance_class"] = "general"
        
        # Add recommendations
        if not central_hole:
            analysis["recommendations"].append("Add central bore for mounting on shaft")
        
        if not analysis["features"]["keyway"].get("detected", False) and central_hole:
            analysis["recommendations"].append("Consider adding keyway or spline for torque transfer")
        
        if analysis["features"]["teeth"]["quality"] != "high" and estimated_teeth > 20:
            analysis["recommendations"].append("Increase tooth profile precision for smoother operation")
        
        return analysis
        
    def _analyze_shaft(self, doc, geometry):
        """Analyze shaft-specific characteristics"""
        
        analysis = {
            "type": "shaft",
            "features": {
                "diameter_sections": [],
                "keyways": [],
                "shoulders": [],
                "threads": []
            },
            "manufacturability": {
                "recommended_process": "",
                "tolerance_class": "",
                "complexity": ""
            },
            "recommendations": []
        }
        
        solid_objects = self._get_solid_objects(doc)
        if not solid_objects:
            return analysis
            
        # Analyze shaft characteristics
        cylindrical_faces = []
        planar_faces = []
        helix_faces = []
        
        for obj in solid_objects:
            if not hasattr(obj, 'Shape'):
                continue
                
            shape = obj.Shape
            bbox = shape.BoundBox
            
            # Find primary axis (longest dimension)
            dimensions = [bbox.XLength, bbox.YLength, bbox.ZLength]
            primary_axis_index = dimensions.index(max(dimensions))
            primary_axis = ['X', 'Y', 'Z'][primary_axis_index]
            
            # Categorize faces
            for face in shape.Faces:
                if face.Surface.TypeId == 'Part::GeomCylinder':
                    cylindrical_faces.append(face)
                elif face.Surface.TypeId == 'Part::GeomPlane':
                    planar_faces.append(face)
                elif face.Surface.TypeId == 'Part::GeomHelix':
                    helix_faces.append(face)
        
        # Identify shaft sections by analyzing cylindrical faces
        if cylindrical_faces:
            # Sort cylindrical faces by radius
            cylindrical_faces.sort(key=lambda f: f.Surface.Radius)
            
            # Group faces by similar radius (within tolerance)
            tolerance = 0.1  # mm
            diameter_groups = []
            current_group = [cylindrical_faces[0]]
            current_radius = cylindrical_faces[0].Surface.Radius
            
            for face in cylindrical_faces[1:]:
                if abs(face.Surface.Radius - current_radius) < tolerance:
                    current_group.append(face)
                else:
                    diameter_groups.append(current_group)
                    current_group = [face]
                    current_radius = face.Surface.Radius
            
            diameter_groups.append(current_group)
            
            # Record diameter sections
            for group in diameter_groups:
                avg_radius = sum(face.Surface.Radius for face in group) / len(group)
                analysis["features"]["diameter_sections"].append({
                    "diameter": avg_radius * 2,
                    "count": len(group)
                })
        
        # Identify shoulders (transitions between different diameters)
        if len(analysis["features"]["diameter_sections"]) > 1:
            analysis["features"]["shoulders"] = [
                {"transition": f"Ø{section['diameter']:.2f} to Ø{analysis['features']['diameter_sections'][i+1]['diameter']:.2f}"}
                for i, section in enumerate(analysis["features"]["diameter_sections"][:-1])
            ]
        
        # Identify keyways by looking for planar faces that intersect with cylindrical faces
        for planar in planar_faces:
            for cylindrical in cylindrical_faces:
                # Check if the planar face intersects with the cylindrical face
                try:
                    intersection = planar.common(cylindrical)
                    if not intersection.isNull() and intersection.Area > 0:
                        # This might be a keyway
                        analysis["features"]["keyways"].append({
                            "on_diameter": cylindrical.Surface.Radius * 2,
                            "width": intersection.BoundBox.XLength  # Approximate width
                        })
                        break
                except:
                    continue
        
        # Identify threads from helical faces
        for helix in helix_faces:
            analysis["features"]["threads"].append({
                "detected": True,
                "diameter": helix.BoundBox.DiagonalLength / 2  # Approximate
            })
        
        # Determine manufacturability characteristics
        max_length = max(bbox.XLength, bbox.YLength, bbox.ZLength)
        min_diameter = min([section["diameter"] for section in analysis["features"]["diameter_sections"]]) if analysis["features"]["diameter_sections"] else 0
        
        # Length to diameter ratio affects manufacturing process
        l_to_d_ratio = max_length / min_diameter if min_diameter > 0 else 0
        
        if l_to_d_ratio > 20:  # Very slender shaft
            analysis["manufacturability"]["recommended_process"] = "Turning with steady rest support"
            analysis["manufacturability"]["complexity"] = "high"
        elif l_to_d_ratio > 10:  # Slender shaft
            analysis["manufacturability"]["recommended_process"] = "CNC turning"
            analysis["manufacturability"]["complexity"] = "medium"
        else:  # Standard shaft
            analysis["manufacturability"]["recommended_process"] = "Turning or grinding"
            analysis["manufacturability"]["complexity"] = "low"
        
        # Determine tolerance class based on features
        if analysis["features"]["keyways"] or analysis["features"]["threads"]:
            analysis["manufacturability"]["tolerance_class"] = "precision"
        elif len(analysis["features"]["diameter_sections"]) > 3:
            analysis["manufacturability"]["tolerance_class"] = "standard"
        else:
            analysis["manufacturability"]["tolerance_class"] = "general"
        
        # Add recommendations
        if l_to_d_ratio > 15:
            analysis["recommendations"].append("Consider increasing diameter to reduce deflection risk")
        
        if not analysis["features"]["keyways"] and not analysis["features"]["threads"]:
            analysis["recommendations"].append("Add keyway or spline for torque transfer")
        
        if len(analysis["features"]["shoulders"]) > 0:
            analysis["recommendations"].append("Add fillets at shoulder transitions to reduce stress concentration")
        
        return analysis
        
    def _analyze_thin_walled_part(self, doc, geometry):
        """Analyze thin-walled part characteristics"""
        
        analysis = {
            "type": "thin_walled_part",
            "features": {
                "wall_thickness": {
                    "min": 0,
                    "max": 0,
                    "avg": 0
                },
                "ribs": [],
                "bosses": [],
                "draft_angles": {}
            },
            "manufacturability": {
                "recommended_process": "",
                "warpage_risk": "",
                "fill_challenges": []
            },
            "recommendations": []
        }
        
        solid_objects = self._get_solid_objects(doc)
        if not solid_objects:
            return analysis
            
        # Analyze thin-walled part characteristics
        total_volume = 0
        total_surface_area = 0
        thickness_values = []
        
        for obj in solid_objects:
            if not hasattr(obj, 'Shape'):
                continue
                
            shape = obj.Shape
            total_volume += shape.Volume
            total_surface_area += shape.Area
            
            # Calculate thickness metrics if available from material flow analysis
            if geometry.material_flow_analysis and "flow_characteristics" in geometry.material_flow_analysis:
                flow_chars = geometry.material_flow_analysis["flow_characteristics"]
                if "min_wall_thickness" in flow_chars:
                    analysis["features"]["wall_thickness"]["min"] = flow_chars["min_wall_thickness"]
                if "max_wall_thickness" in flow_chars:
                    analysis["features"]["wall_thickness"]["max"] = flow_chars["max_wall_thickness"]
                if "average_wall_thickness" in flow_chars:
                    analysis["features"]["wall_thickness"]["avg"] = flow_chars["average_wall_thickness"]
            
            # If no material flow analysis, estimate from volume/surface area ratio
            if analysis["features"]["wall_thickness"]["avg"] == 0:
                # Rough estimate for thin-walled parts: 2 * Volume / Surface Area
                estimated_thickness = 2 * shape.Volume / shape.Area if shape.Area > 0 else 0
                analysis["features"]["wall_thickness"]["avg"] = estimated_thickness
                analysis["features"]["wall_thickness"]["min"] = estimated_thickness * 0.8  # Estimate
                analysis["features"]["wall_thickness"]["max"] = estimated_thickness * 1.2  # Estimate
        
        # Get draft angle information if available
        if geometry.draft_analysis:
            analysis["features"]["draft_angles"] = {
                "min": geometry.draft_analysis.get("min_draft_angle", 0),
                "max": geometry.draft_analysis.get("max_draft_angle", 0),
                "avg": geometry.draft_analysis.get("average_draft_angle", 0),
                "insufficient_count": len(geometry.draft_analysis.get("insufficient_draft_faces", []))
            }
        
        # Identify ribs and bosses from geometry features
        if geometry.ribs:
            for rib in geometry.ribs:
                analysis["features"]["ribs"].append({
                    "height": rib.properties.get("height", 0),
                    "thickness": rib.properties.get("thickness", 0),
                    "length": rib.properties.get("length", 0)
                })
        
        if geometry.bosses:
            for boss in geometry.bosses:
                analysis["features"]["bosses"].append({
                    "diameter": boss.properties.get("diameter", 0),
                    "height": boss.properties.get("height", 0)
                })
        
        # Determine manufacturability characteristics
        avg_thickness = analysis["features"]["wall_thickness"]["avg"]
        min_thickness = analysis["features"]["wall_thickness"]["min"]
        
        # Recommend manufacturing process based on thickness
        if avg_thickness < 1.0:
            if total_surface_area > 50000:  # Large thin part
                analysis["manufacturability"]["recommended_process"] = "Injection molding with thin-wall grade material"
            else:
                analysis["manufacturability"]["recommended_process"] = "Injection molding or thermoforming"
        elif avg_thickness < 3.0:
            analysis["manufacturability"]["recommended_process"] = "Standard injection molding"
        else:
            analysis["manufacturability"]["recommended_process"] = "Structural foam molding or rotational molding"
        
        # Assess warpage risk
        thickness_variation = analysis["features"]["wall_thickness"]["max"] / max(analysis["features"]["wall_thickness"]["min"], 0.1)
        if thickness_variation > 2.0:
            analysis["manufacturability"]["warpage_risk"] = "high"
        elif thickness_variation > 1.5:
            analysis["manufacturability"]["warpage_risk"] = "medium"
        else:
            analysis["manufacturability"]["warpage_risk"] = "low"
        
        # Identify fill challenges
        if min_thickness < 0.8:
            analysis["manufacturability"]["fill_challenges"].append({
                "type": "thin_sections",
                "description": "Extremely thin walls may cause incomplete filling",
                "severity": "high"
            })
        
        if total_surface_area / total_volume > 1.0 and avg_thickness < 2.0:
            analysis["manufacturability"]["fill_challenges"].append({
                "type": "flow_length",
                "description": "Long flow paths may require higher injection pressure",
                "severity": "medium"
            })
        
        # Add recommendations
        if analysis["manufacturability"]["warpage_risk"] == "high":
            analysis["recommendations"].append("Maintain uniform wall thickness to reduce warpage")
        
        if min_thickness < 0.8:
            analysis["recommendations"].append("Increase minimum wall thickness to improve moldability")
        
        if not analysis["features"]["ribs"] and avg_thickness < 2.0:
            analysis["recommendations"].append("Consider adding reinforcement ribs to improve stiffness")
        
        if analysis["features"]["draft_angles"].get("insufficient_count", 0) > 0:
            analysis["recommendations"].append("Increase draft angles to facilitate part ejection")
        
        return analysis
        
    def _analyze_mechanical_component(self, doc, geometry):
        """Analyze general mechanical component characteristics"""
        
        analysis = {
            "type": "mechanical_component",
            "features": {
                "functional_surfaces": [],
                "precision_features": [],
                "mating_interfaces": []
            },
            "manufacturability": {
                "recommended_process": "",
                "tolerance_requirements": "",
                "surface_finish_requirements": ""
            },
            "recommendations": []
        }
        
        solid_objects = self._get_solid_objects(doc)
        if not solid_objects:
            return analysis
            
        # Analyze mechanical component characteristics
        total_volume = 0
        cylindrical_faces = []
        planar_faces = []
        precision_features_count = 0
        
        for obj in solid_objects:
            if not hasattr(obj, 'Shape'):
                continue
                
            shape = obj.Shape
            total_volume += shape.Volume
            bbox = shape.BoundBox
            
            # Categorize faces by type
            for face in shape.Faces:
                if face.Surface.TypeId == 'Part::GeomCylinder':
                    cylindrical_faces.append(face)
                    
                    # Check if this might be a precision feature (small diameter)
                    radius = face.Surface.Radius
                    if 0.5 < radius < 10.0:  # Typical precision feature size range
                        precision_features_count += 1
                        analysis["features"]["precision_features"].append({
                            "type": "cylindrical",
                            "diameter": radius * 2,
                            "tolerance_class": "H7" if radius < 5.0 else "H8"  # Estimate common tolerance classes
                        })
                        
                elif face.Surface.TypeId == 'Part::GeomPlane':
                    planar_faces.append(face)
                    
                    # Check if this might be a functional surface (large flat area)
                    if face.Area > 100:  # Significant planar face
                        analysis["features"]["functional_surfaces"].append({
                            "type": "planar",
                            "area": face.Area,
                            "flatness_requirement": "high" if face.Area > 1000 else "medium"
                        })
        
        # Identify potential mating interfaces
        # Look for pairs of features that might mate with other components
        if cylindrical_faces and planar_faces:
            for cyl_face in cylindrical_faces:
                cyl_center = cyl_face.CenterOfMass
                
                # Find nearby planar faces that might form a mating interface
                for planar_face in planar_faces:
                    if self._is_face_near_point(planar_face, cyl_center, cyl_face.Surface.Radius * 3):
                        analysis["features"]["mating_interfaces"].append({
                            "type": "hole_and_face",
                            "hole_diameter": cyl_face.Surface.Radius * 2,
                            "face_area": planar_face.Area
                        })
                        break
        
        # Determine manufacturability characteristics
        # Base recommendations on feature complexity and precision requirements
        if precision_features_count > 5:
            analysis["manufacturability"]["recommended_process"] = "CNC machining"
            analysis["manufacturability"]["tolerance_requirements"] = "high"
        elif precision_features_count > 2:
            analysis["manufacturability"]["recommended_process"] = "CNC machining or high-precision casting"
            analysis["manufacturability"]["tolerance_requirements"] = "medium"
        else:
            analysis["manufacturability"]["recommended_process"] = "Machining, casting, or molding"
            analysis["manufacturability"]["tolerance_requirements"] = "standard"
        
        # Determine surface finish requirements based on functional surfaces
        functional_surface_count = len(analysis["features"]["functional_surfaces"])
        if functional_surface_count > 3:
            analysis["manufacturability"]["surface_finish_requirements"] = "high"
        elif functional_surface_count > 0:
            analysis["manufacturability"]["surface_finish_requirements"] = "medium"
        else:
            analysis["manufacturability"]["surface_finish_requirements"] = "standard"
        
        # Add recommendations
        if precision_features_count > 0:
            analysis["recommendations"].append("Ensure proper tolerancing for precision features")
        
        if analysis["manufacturability"]["tolerance_requirements"] == "high":
            analysis["recommendations"].append("Consider post-machining operations for critical dimensions")
        
        if analysis["manufacturability"]["surface_finish_requirements"] == "high":
            analysis["recommendations"].append("Specify surface finish requirements for functional surfaces")
        
        return analysis
        
    def _is_face_near_point(self, face, point, max_distance):
        """Helper method to check if a face is near a point"""
        try:
            face_center = face.CenterOfMass
            distance = face_center.distanceToPoint(point)
            return distance < max_distance
        except:
            return False
        
    def _calculate_complexity_metrics(self, doc, geometry):
        """Calculate complexity metrics for the model"""
        
        metrics = {
            "geometric_complexity": 0,
            "manufacturing_complexity": 0,
            "feature_density": 0,
            "overall_complexity": 0,
            "complexity_factors": []
        }
        
        solid_objects = self._get_solid_objects(doc)
        if not solid_objects:
            return metrics
            
        # Calculate basic metrics
        total_volume = 0
        total_surface_area = 0
        total_edge_count = 0
        total_face_count = 0
        total_vertex_count = 0
        
        for obj in solid_objects:
            if not hasattr(obj, 'Shape'):
                continue
                
            shape = obj.Shape
            total_volume += shape.Volume
            total_surface_area += shape.Area
            total_face_count += len(shape.Faces)
            total_edge_count += len(shape.Edges)
            total_vertex_count += len(shape.Vertexes)
        
        # Calculate feature density (features per unit volume)
        if total_volume > 0:
            metrics["feature_density"] = (total_face_count + total_edge_count) / total_volume * 100
        
        # Calculate geometric complexity based on face count, edge count, and surface area to volume ratio
        surface_volume_ratio = total_surface_area / total_volume if total_volume > 0 else 0
        
        # Normalize metrics to a 0-100 scale
        face_complexity = min(100, total_face_count / 10)  # Assuming 1000 faces is very complex
        edge_complexity = min(100, total_edge_count / 20)  # Assuming 2000 edges is very complex
        sv_ratio_complexity = min(100, surface_volume_ratio * 10)  # Normalize surface to volume ratio
        
        # Geometric complexity is weighted average of these factors
        metrics["geometric_complexity"] = int(0.4 * face_complexity + 0.4 * edge_complexity + 0.2 * sv_ratio_complexity)
        
        # Calculate manufacturing complexity based on analysis results
        manufacturing_factors = []
        
        # Factor 1: Draft angle issues
        if geometry.draft_analysis:
            insufficient_draft_count = len(geometry.draft_analysis.get("insufficient_draft_faces", []))
            if insufficient_draft_count > 0:
                draft_factor = min(100, insufficient_draft_count * 5)  # 20 issues = 100% complex
                manufacturing_factors.append(draft_factor)
                metrics["complexity_factors"].append({
                    "factor": "insufficient_draft_angles",
                    "score": draft_factor,
                    "impact": "high" if draft_factor > 50 else "medium"
                })
        
        # Factor 2: Undercut issues
        if geometry.undercut_analysis:
            undercut_count = len(geometry.undercut_analysis.get("undercuts", []))
            if undercut_count > 0:
                undercut_factor = min(100, undercut_count * 10)  # 10 undercuts = 100% complex
                manufacturing_factors.append(undercut_factor)
                metrics["complexity_factors"].append({
                    "factor": "undercuts",
                    "score": undercut_factor,
                    "impact": "high" if undercut_factor > 50 else "medium"
                })
        
        # Factor 3: Stress concentration issues
        if geometry.stress_concentration_analysis:
            stress_count = len(geometry.stress_concentration_analysis.get("stress_points", []))
            if stress_count > 0:
                stress_factor = min(100, stress_count * 5)  # 20 stress points = 100% complex
                manufacturing_factors.append(stress_factor)
                metrics["complexity_factors"].append({
                    "factor": "stress_concentrations",
                    "score": stress_factor,
                    "impact": "medium"
                })
        
        # Factor 4: Material flow issues
        if geometry.material_flow_analysis:
            flow_issues = len(geometry.material_flow_analysis.get("potential_issues", []))
            if flow_issues > 0:
                flow_factor = min(100, flow_issues * 20)  # 5 flow issues = 100% complex
                manufacturing_factors.append(flow_factor)
                metrics["complexity_factors"].append({
                    "factor": "material_flow_issues",
                    "score": flow_factor,
                    "impact": "high" if flow_factor > 50 else "medium"
                })
        
        # Calculate overall manufacturing complexity
        if manufacturing_factors:
            metrics["manufacturing_complexity"] = int(sum(manufacturing_factors) / len(manufacturing_factors))
        else:
            metrics["manufacturing_complexity"] = 0
        
        # Calculate overall complexity as weighted average of geometric and manufacturing complexity
        metrics["overall_complexity"] = int(0.4 * metrics["geometric_complexity"] + 0.6 * metrics["manufacturing_complexity"])
        
        return metrics
        
    def _validate_quality(self, doc, geometry):
        """Validate the quality of the model and analysis"""
        
        validation = {
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "quality_score": 100
        }
        
        solid_objects = self._get_solid_objects(doc)
        if not solid_objects:
            validation["is_valid"] = False
            validation["issues"].append("No solid objects found in document")
            validation["quality_score"] = 0
            return validation
        
        # Check for basic geometry issues
        for obj in solid_objects:
            if not hasattr(obj, 'Shape'):
                continue
                
            shape = obj.Shape
            
            # Check if shape is valid
            if not shape.isValid():
                validation["is_valid"] = False
                validation["issues"].append(f"Invalid shape in object {obj.Name}")
                validation["quality_score"] -= 50
            
            # Check for zero volume
            if shape.Volume < 0.001:
                validation["warnings"].append(f"Object {obj.Name} has near-zero volume")
                validation["quality_score"] -= 10
            
            # Check for degenerate faces
            for i, face in enumerate(shape.Faces):
                if face.Area < 0.001:
                    validation["warnings"].append(f"Degenerate face detected in object {obj.Name}")
                    validation["quality_score"] -= 5
                    break  # Only report once per object
        
        # Check for analysis completeness
        if not geometry.draft_analysis:
            validation["warnings"].append("Draft angle analysis not performed")
            validation["quality_score"] -= 10
        
        if not geometry.undercut_analysis:
            validation["warnings"].append("Undercut analysis not performed")
            validation["quality_score"] -= 10
        
        if not geometry.stress_concentration_analysis:
            validation["warnings"].append("Stress concentration analysis not performed")
            validation["quality_score"] -= 10
        
        if not geometry.parting_line_analysis:
            validation["warnings"].append("Parting line analysis not performed")
            validation["quality_score"] -= 10
        
        if not geometry.material_flow_analysis:
            validation["warnings"].append("Material flow analysis not performed")
            validation["quality_score"] -= 10
        
        # Ensure quality score is within bounds
        validation["quality_score"] = max(0, min(100, validation["quality_score"]))
        
        return validation
    
    def _analyze_stress_concentrations(self, shape, geometry: ComprehensiveCADGeometry):
        """Analyze potential stress concentration areas"""
        
        # This is a simplified analysis based on geometry
        # A full FEA simulation would be needed for accurate results
        
        stress_concentrations = []
        
        # Check for sharp internal corners (common stress concentration points)
        for edge_idx, edge in enumerate(shape.Edges):
            try:
                # Skip non-linear edges
                if not hasattr(edge, 'Curve') or not str(edge.Curve).startswith('<Line'):
                    continue
                    
                # Find connected edges
                connected_edges = []
                for other_edge in shape.Edges:
                    if edge != other_edge:
                        # Check if edges share a vertex
                        if (edge.Vertexes[0].Point.isEqual(other_edge.Vertexes[0].Point, 1e-6) or
                            edge.Vertexes[0].Point.isEqual(other_edge.Vertexes[1].Point, 1e-6) or
                            edge.Vertexes[1].Point.isEqual(other_edge.Vertexes[0].Point, 1e-6) or
                            edge.Vertexes[1].Point.isEqual(other_edge.Vertexes[1].Point, 1e-6)):
                            connected_edges.append(other_edge)
                
                # Check for sharp angles between edges
                for conn_edge in connected_edges:
                    if hasattr(conn_edge, 'Curve') and str(conn_edge.Curve).startswith('<Line'):
                        # Get edge directions
                        dir1 = edge.Vertexes[1].Point.sub(edge.Vertexes[0].Point)
                        dir2 = conn_edge.Vertexes[1].Point.sub(conn_edge.Vertexes[0].Point)
                        
                        # Normalize directions
                        len1 = math.sqrt(dir1.x**2 + dir1.y**2 + dir1.z**2)
                        len2 = math.sqrt(dir2.x**2 + dir2.y**2 + dir2.z**2)
                        
                        if len1 > 0 and len2 > 0:
                            dir1.scale(1/len1, 1/len1, 1/len1)
                            dir2.scale(1/len2, 1/len2, 1/len2)
                            
                            # Calculate angle between edges
                            dot_product = dir1.x * dir2.x + dir1.y * dir2.y + dir1.z * dir2.z
                            # Clamp to valid range due to floating point errors
                            dot_product = max(-1.0, min(1.0, dot_product))
                            angle_rad = math.acos(dot_product)
                            angle_deg = math.degrees(angle_rad)
                            
                            # Sharp internal corners can cause stress concentrations
                            if angle_deg < 45:  # Arbitrary threshold
                                # Find intersection point
                                intersection = None
                                for v1 in edge.Vertexes:
                                    for v2 in conn_edge.Vertexes:
                                        if v1.Point.isEqual(v2.Point, 1e-6):
                                            intersection = v1.Point
                                            break
                                
                                if intersection:
                                    stress_concentrations.append({
                                        "location": {
                                            "x": intersection.x,
                                            "y": intersection.y,
                                            "z": intersection.z
                                        },
                                        "angle": angle_deg,
                                        "severity": "high" if angle_deg < 30 else "medium",
                                        "edge_indices": [edge_idx, shape.Edges.index(conn_edge)]
                                    })
            except:
                continue
        
        # Store results
        geometry.stress_concentration_analysis = {
            "concentrations": stress_concentrations,
            "count": len(stress_concentrations)
        }
        
        print(f"Stress concentration analysis: {len(stress_concentrations)} areas identified")
    
    def _perform_model_specific_analysis(self, doc, geometry: ComprehensiveCADGeometry):
        """Perform model-specific analysis based on part type"""
        
        # Get part type
        part_type = geometry.part_type
        
        # Run appropriate analyzer based on part type
        if part_type in self.model_analyzers:
            analyzer = self.model_analyzers[part_type]
            analyzer(doc, geometry)
            print(f"Performed model-specific analysis for {part_type.value}")
        else:
            print(f"No model-specific analyzer available for {part_type.value}")
    
    def _calculate_complexity_metrics(self, geometry: ComprehensiveCADGeometry):
        """Calculate complexity metrics for the model"""
        
        # Basic complexity metrics
        feature_count = len(geometry.features)
        surface_area = geometry.surface_area
        volume = geometry.volume
        
        # Calculate feature density (features per unit volume)
        feature_density = feature_count / volume * 1000 if volume > 0 else 0  # Features per 1000 mm³
        
        # Calculate surface complexity (ratio of surface area to volume)
        surface_complexity = surface_area / math.pow(volume, 2/3) if volume > 0 else 0
        
        # Calculate manufacturing complexity based on analysis results
        mfg_complexity = 0
        
        # Add complexity for wall thickness issues
        thin_wall_count = sum(1 for wt in geometry.wall_thickness_analysis if wt.is_critical)
        mfg_complexity += thin_wall_count * 0.5
        
        # Add complexity for draft angle issues
        if geometry.draft_analysis and "min_negative_draft_count" in geometry.draft_analysis:
            negative_draft_count = geometry.draft_analysis["min_negative_draft_count"]
            mfg_complexity += negative_draft_count * 0.3
        
        # Add complexity for undercuts
        if geometry.undercut_analysis and "count" in geometry.undercut_analysis:
            undercut_count = geometry.undercut_analysis["count"]
            mfg_complexity += undercut_count * 0.7
        
        # Add complexity for material flow issues
        flow_issue_count = len(geometry.material_flow_analysis)
        mfg_complexity += flow_issue_count * 0.4
        
        # Add complexity for stress concentrations
        if geometry.stress_concentration_analysis and "count" in geometry.stress_concentration_analysis:
            stress_concentration_count = geometry.stress_concentration_analysis["count"]
            mfg_complexity += stress_concentration_count * 0.2
        
        # Calculate geometric complexity index (normalized to 0-10 scale)
        # This combines feature density, surface complexity, and manufacturing complexity
        geometric_complexity = (feature_density * 0.4 + surface_complexity * 0.3 + mfg_complexity * 0.3)
        geometric_complexity_index = min(10, geometric_complexity * 2)  # Scale to 0-10
        
        # Store results
        geometry.complexity_metrics = {
            "feature_count": feature_count,
            "feature_density": feature_density,
            "surface_complexity": surface_complexity,
            "manufacturing_complexity": mfg_complexity,
            "thin_wall_count": thin_wall_count,
            "flow_issue_count": flow_issue_count
        }
        
        geometry.feature_density = feature_density
        geometry.geometric_complexity_index = geometric_complexity_index
        
        print(f"Complexity metrics: GCI={geometric_complexity_index:.2f}, Features={feature_count}")
    
    def _validate_extraction_quality(self, geometry: ComprehensiveCADGeometry):
        """Validate extraction quality and completeness"""
        
        # Initialize validation
        validation_errors = []
        completeness_score = 100.0  # Start with perfect score
        
        # Check for basic geometric properties
        if geometry.volume <= 0:
            validation_errors.append("Invalid or zero volume")
            completeness_score -= 20
        
        if geometry.surface_area <= 0:
            validation_errors.append("Invalid or zero surface area")
            completeness_score -= 10
        
        if not geometry.overall_dimensions:
            validation_errors.append("Missing overall dimensions")
            completeness_score -= 10
        
        # Check for feature extraction
        if not geometry.features:
            validation_errors.append("No features extracted")
            completeness_score -= 15
        
        # Check for wall thickness analysis
        if not geometry.wall_thickness_analysis:
            validation_errors.append("Wall thickness analysis missing")
            completeness_score -= 10
        
        # Check for manufacturing analysis
        if not geometry.draft_analysis:
            validation_errors.append("Draft angle analysis missing")
            completeness_score -= 5
        
        if not geometry.undercut_analysis:
            validation_errors.append("Undercut analysis missing")
            completeness_score -= 5
        
        # Check for complexity metrics
        if geometry.geometric_complexity_index <= 0:
            validation_errors.append("Complexity metrics missing")
            completeness_score -= 5
        
        # Determine extraction quality based on completeness score
        if completeness_score >= 90:
            extraction_quality = "excellent"
        elif completeness_score >= 75:
            extraction_quality = "good"
        elif completeness_score >= 50:
            extraction_quality = "fair"
        else:
            extraction_quality = "poor"
        
        # Store results
        geometry.validation_errors = validation_errors
        geometry.completeness_score = completeness_score
        geometry.extraction_quality = extraction_quality
        
        print(f"Validation: {extraction_quality} ({completeness_score:.1f}%), {len(validation_errors)} errors")
        if validation_errors:
            print(f"Validation errors: {validation_errors}")

    
    # Feature extraction methods
    def _extract_holes(self, obj) -> List[DetailedFeature]:
        """Extract hole features from an object"""
        holes = []
        
        try:
            if not hasattr(obj, 'Shape') or not obj.Shape.isValid():
                return holes
                
            shape = obj.Shape
            
            # Look for cylindrical faces that might be holes
            for face_idx, face in enumerate(shape.Faces):
                # Skip non-cylindrical faces
                if not hasattr(face, 'Surface') or not hasattr(face.Surface, 'Radius'):
                    continue
                    
                # Get face properties
                radius = face.Surface.Radius
                face_center = face.CenterOfMass
                
                # Skip very large cylinders (likely not holes)
                if radius > 50.0:  # Arbitrary threshold
                    continue
                    
                # Check if this is an internal cylindrical face (hole)
                is_internal = self._is_internal_face(face, shape)
                if not is_internal:
                    continue
                    
                # Determine hole axis and depth
                axis, depth, is_through = self._analyze_hole_geometry(face, shape)
                
                # Skip if we couldn't determine depth
                if depth <= 0:
                    continue
                    
                # Determine hole type
                hole_type = FeatureType.HOLE_THROUGH if is_through else FeatureType.HOLE_BLIND
                
                # Look for counterbore or countersink features
                # This is a simplified approach - a more robust implementation would analyze
                # the adjacent faces and geometry in detail
                try:
                    # Check for counterbore (larger diameter section at entrance)
                    for other_face in shape.Faces:
                        if hasattr(other_face, 'Surface') and hasattr(other_face.Surface, 'Radius'):
                            other_radius = other_face.Surface.Radius
                            other_center = other_face.CenterOfMass
                            
                            # If centers are aligned and this is a larger hole
                            distance = math.sqrt((face_center.x - other_center.x)**2 + 
                                               (face_center.y - other_center.y)**2)
                            
                            if distance < 0.1 * radius and other_radius > radius * 1.2:
                                hole_type = FeatureType.HOLE_COUNTERBORE
                                break
                                
                    # Check for countersink (conical face at entrance)
                    if hole_type not in [FeatureType.HOLE_COUNTERBORE]:
                        for other_face in shape.Faces:
                            if hasattr(other_face, 'Surface') and isinstance(other_face.Surface, Part.Cone):
                                other_center = other_face.CenterOfMass
                                
                                # If centers are aligned
                                distance = math.sqrt((face_center.x - other_center.x)**2 + 
                                                   (face_center.y - other_center.y)**2)
                                
                                if distance < 0.1 * radius:
                                    hole_type = FeatureType.HOLE_COUNTERSINK
                                    break
                except Exception as e:
                    print(f"Warning: Error checking for counterbore/countersink: {e}")
                
                # Create hole feature
                hole = DetailedFeature(
                    feature_id=f"hole_{len(holes) + 1}",
                    feature_type=hole_type,
                    location={
                        "x": face_center.x,
                        "y": face_center.y,
                        "z": face_center.z
                    },
                    dimensions={
                        "diameter": radius * 2,
                        "radius": radius,
                        "depth": depth
                    },
                    orientation={
                        "x": axis.x,
                        "y": axis.y,
                        "z": axis.z
                    },
                    properties={
                        "is_through": is_through,
                        "face_index": face_idx,
                        "volume": math.pi * radius * radius * depth
                    }
                )
                
                # Analyze manufacturability
                self._analyze_hole_manufacturability(hole)
                
                holes.append(hole)
                
        except Exception as e:
            print(f"Error extracting holes: {e}")
            traceback.print_exc()
            
        return holes
    
    def _is_internal_face(self, face, shape) -> bool:
        """Check if a face is internal (hole) or external (boss)"""
        try:
            # Get face center and normal
            face_center = face.CenterOfMass
            face_normal = face.normalAt(0, 0)
            
            # Create a test point slightly offset from face center along normal
            test_point = face_center.add(face_normal.multiply(0.1))
            
            # Check if test point is inside the shape
            # This is a simplified approach - a more robust method would use
            # shape.isInside() but that's not always reliable
            
            # Create a line from test point to outside the bounding box
            bbox = shape.BoundBox
            bbox_diagonal = math.sqrt(bbox.XLength**2 + bbox.YLength**2 + bbox.ZLength**2)
            far_point = test_point.add(FreeCAD.Vector(bbox_diagonal, bbox_diagonal, bbox_diagonal))
            
            # Count intersections with shape boundary
            line = Part.LineSegment(test_point, far_point)
            intersections = shape.section(line.toShape()).Vertexes
            
            # If odd number of intersections, test point is inside (internal face)
            return len(intersections) % 2 == 1
            
        except Exception as e:
            print(f"Error checking if face is internal: {e}")
            return False
    
    def _analyze_hole_geometry(self, face, shape):
        """Analyze hole geometry to determine axis, depth, and if it's through-hole"""
        try:
            # Get face center and normal (axis)
            face_center = face.CenterOfMass
            face_normal = face.normalAt(0, 0)
            
            # Normalize axis
            axis_length = math.sqrt(face_normal.x**2 + face_normal.y**2 + face_normal.z**2)
            if axis_length > 0:
                axis = FreeCAD.Vector(
                    face_normal.x / axis_length,
                    face_normal.y / axis_length,
                    face_normal.z / axis_length
                )
            else:
                axis = FreeCAD.Vector(0, 0, 1)  # Default
            
            # Get bounding box for reference
            bbox = shape.BoundBox
            bbox_diagonal = math.sqrt(bbox.XLength**2 + bbox.YLength**2 + bbox.ZLength**2)
            
            # Create lines in both directions of the axis
            line_forward = Part.LineSegment(
                face_center, 
                face_center.add(axis.multiply(bbox_diagonal))
            )
            
            line_reverse = Part.LineSegment(
                face_center, 
                face_center.add(axis.multiply(-bbox_diagonal))
            )
            
            # Find intersections
            intersections_forward = shape.section(line_forward.toShape()).Vertexes
            intersections_reverse = shape.section(line_reverse.toShape()).Vertexes
            
            # Calculate distances to intersections
            distances_forward = [face_center.distanceToPoint(v.Point) for v in intersections_forward]
            distances_reverse = [face_center.distanceToPoint(v.Point) for v in intersections_reverse]
            
            # Filter out very small distances (self-intersections)
            distances_forward = [d for d in distances_forward if d > 0.1]
            distances_reverse = [d for d in distances_reverse if d > 0.1]
            
            # Determine if it's a through hole
            is_through = len(distances_forward) > 0 and len(distances_reverse) > 0
            
            # Calculate depth
            if is_through:
                # For through holes, depth is the minimum distance through the part
                depth = min(distances_forward + distances_reverse) if distances_forward and distances_reverse else 0
            else:
                # For blind holes, depth is the maximum distance in either direction
                depth = max(distances_forward + distances_reverse) if distances_forward or distances_reverse else 0
            
            return axis, depth, is_through
            
        except Exception as e:
            print(f"Error analyzing hole geometry: {e}")
            return FreeCAD.Vector(0, 0, 1), 0, False
            
    def _analyze_hole_manufacturability(self, hole_feature):
        """Analyze hole manufacturability characteristics"""
        
        diameter = hole_feature.dimensions.get("diameter", 0)
        depth = hole_feature.dimensions.get("depth", 0)
        is_through = hole_feature.properties.get("is_through", False)
        
        # Calculate aspect ratio
        aspect_ratio = depth / diameter if diameter > 0 else 1.0
        hole_feature.properties["aspect_ratio"] = aspect_ratio
        
        manufacturability_issues = []
        cost_drivers = []
        recommended_processes = []
        
        # Accessibility analysis
        if aspect_ratio > 10:
            hole_feature.properties["accessibility"] = "limited"
            manufacturability_issues.append("High aspect ratio may require special drilling")
            cost_drivers.append("Deep hole drilling operations")
        elif aspect_ratio > 5:
            manufacturability_issues.append("Moderate aspect ratio - may need peck drilling")
        
        # Diameter analysis
        if diameter < 1.0:
            manufacturability_issues.append("Very small hole - may require micro-drilling")
            cost_drivers.append("Micro-drilling operations")
            recommended_processes.extend(["laser_drilling", "EDM"])
        elif diameter < 2.0:
            manufacturability_issues.append("Small hole - requires precision drilling")
            recommended_processes.extend(["precision_drilling", "reaming"])
        elif diameter > 50.0:
            manufacturability_issues.append("Large hole - consider alternative methods")
            recommended_processes.extend(["boring", "milling"])
        else:
            recommended_processes.extend(["standard_drilling"])
        
        # Depth analysis
        if depth > diameter * 8:
            cost_drivers.append("Very deep hole - specialized tooling required")
            recommended_processes.extend(["gun_drilling", "deep_hole_drilling"])
        
        # Process recommendations based on hole type
        if hole_feature.feature_type == FeatureType.HOLE_COUNTERBORE:
            recommended_processes.extend(["drilling_counterboring", "end_milling"])
            cost_drivers.append("Multi-step machining process")
        elif hole_feature.feature_type == FeatureType.HOLE_COUNTERSINK:
            recommended_processes.extend(["drilling_countersinking"])
            cost_drivers.append("Secondary operation required")
        
        # Calculate complexity score
        complexity = 1.0
        complexity += aspect_ratio * 0.1
        complexity += len(manufacturability_issues) * 0.5
        
        # Update the hole feature with analysis results
        hole_feature.properties["manufacturability_issues"] = manufacturability_issues
        hole_feature.properties["cost_drivers"] = cost_drivers
        hole_feature.properties["recommended_processes"] = recommended_processes
        hole_feature.properties["complexity_score"] = min(10.0, complexity)
    
    def _extract_pockets(self, obj) -> List[DetailedFeature]:
        """Extract pocket features from an object"""
        pockets = []
        
        try:
            if not hasattr(obj, 'Shape') or not obj.Shape.isValid():
                return pockets
                
            shape = obj.Shape
            
            # Look for planar faces that might be pocket bottoms
            for face_idx, face in enumerate(shape.Faces):
                # Skip non-planar faces
                if not hasattr(face, 'Surface') or not str(face.Surface).startswith('<Plane'):
                    continue
                    
                # Get face properties
                face_center = face.CenterOfMass
                face_normal = face.normalAt(0, 0)
                
                # Check if this is a potential pocket bottom (normal points into solid)
                if not self._is_internal_face(face, shape):
                    continue
                    
                # Analyze pocket geometry
                pocket_type, dimensions, depth = self._analyze_pocket_geometry(face, shape)
                
                # Skip if we couldn't determine depth or dimensions
                if depth <= 0 or not dimensions:
                    continue
                    
                # Create pocket feature
                pocket = DetailedFeature(
                    feature_id=f"pocket_{len(pockets) + 1}",
                    feature_type=pocket_type,
                    location={
                        "x": face_center.x,
                        "y": face_center.y,
                        "z": face_center.z
                    },
                    dimensions=dimensions,
                    orientation={
                        "x": face_normal.x,
                        "y": face_normal.y,
                        "z": face_normal.z
                    },
                    properties={
                        "depth": depth,
                        "face_index": face_idx,
                        "volume": face.Area * depth  # Approximate volume calculation
                    }
                )
                
                # Analyze manufacturability
                self._analyze_pocket_manufacturability(pocket)
                
                # Check for complex pocket features
                try:
                    # Analyze edge characteristics to detect complex pockets
                    edge_count = len(face.Edges)
                    if edge_count > 4 and pocket_type == FeatureType.POCKET_RECTANGULAR:
                        # This might be a complex pocket with multiple edges
                        pocket.feature_type = FeatureType.POCKET_COMPLEX
                        pocket.properties["edge_count"] = edge_count
                        pocket.properties["manufacturability_issues"].append(
                            "Complex pocket shape - may require advanced machining strategies")
                        pocket.properties["cost_drivers"].append("Complex toolpath generation")
                except Exception as e:
                    print(f"Warning: Error analyzing pocket complexity: {e}")
                
                pockets.append(pocket)
                
        except Exception as e:
            print(f"Error extracting pockets: {e}")
            traceback.print_exc()
            
        return pockets
    
    def _analyze_pocket_geometry(self, face, shape):
        """Analyze pocket geometry to determine type, dimensions, and depth"""
        try:
            # Get face properties
            face_center = face.CenterOfMass
            face_normal = face.normalAt(0, 0)
            
            # Get face bounds
            face_bounds = face.BoundBox
            width = face_bounds.XLength
            length = face_bounds.YLength
            
            # Determine pocket type based on shape
            pocket_type = FeatureType.POCKET_RECTANGULAR
            dimensions = {
                "width": width,
                "length": length,
                "area": face.Area
            }
            
            # Check if it's more circular
            if abs(width - length) / max(width, length) < 0.2:  # Nearly equal dimensions
                # Check if perimeter is close to circular
                perimeter = 0
                for edge in face.Edges:
                    perimeter += edge.Length
                
                # Calculate equivalent circle perimeter
                radius = math.sqrt(face.Area / math.pi)
                circle_perimeter = 2 * math.pi * radius
                
                # If perimeter is close to that of a circle, classify as circular
                if abs(perimeter - circle_perimeter) / circle_perimeter < 0.2:
                    pocket_type = FeatureType.POCKET_CIRCULAR
                    dimensions = {
                        "radius": radius,
                        "diameter": radius * 2,
                        "area": face.Area
                    }
            
            # Determine pocket depth
            depth = self._measure_pocket_depth(face, face_normal, shape)
            
            return pocket_type, dimensions, depth
            
        except Exception as e:
            print(f"Error analyzing pocket geometry: {e}")
            return FeatureType.POCKET_RECTANGULAR, {}, 0
    
    def _measure_pocket_depth(self, face, normal, shape, max_distance=1000.0) -> float:
        """Measure pocket depth from face along normal"""
        try:
            # Get face center
            face_center = face.CenterOfMass
            
            # Create a line from the face center in the direction of the normal
            line = Part.LineSegment(
                face_center, 
                face_center.add(normal.multiply(max_distance))
            )
            
            # Find intersections with the shape
            intersections = shape.section(line.toShape()).Vertexes
            
            # Calculate distances to intersections
            distances = [face_center.distanceToPoint(v.Point) for v in intersections]
            
            # Filter out very small distances (self-intersections)
            distances = [d for d in distances if d > 0.1]
            
            # Pocket depth is the minimum distance to an intersection
            return min(distances) if distances else 0
            
        except Exception as e:
            print(f"Error measuring pocket depth: {e}")
            return 0
            
    def _analyze_pocket_manufacturability(self, pocket_feature):
        """Analyze pocket manufacturability characteristics"""
        
        pocket_type = pocket_feature.feature_type
        depth = pocket_feature.properties.get("depth", 0)
        
        manufacturability_issues = []
        cost_drivers = []
        recommended_processes = []
        
        # Get dimensions based on pocket type
        if pocket_type == FeatureType.POCKET_CIRCULAR:
            radius = pocket_feature.dimensions.get("radius", 0)
            diameter = pocket_feature.dimensions.get("diameter", 0)
            
            # Calculate aspect ratio (depth to diameter)
            aspect_ratio = depth / diameter if diameter > 0 else 1.0
            pocket_feature.properties["aspect_ratio"] = aspect_ratio
            
            # Analyze circular pocket manufacturability
            if radius < 1.0:
                manufacturability_issues.append("Very small pocket radius - requires precision tooling")
                cost_drivers.append("Precision machining operations")
            
            if aspect_ratio > 3:
                manufacturability_issues.append("Deep pocket relative to diameter - may require specialized tooling")
                cost_drivers.append("Deep pocket machining")
                
            # Recommend processes
            if radius < 2.0:
                recommended_processes.extend(["micro_milling", "EDM"])
            else:
                recommended_processes.extend(["end_milling", "plunge_milling"])
                
        elif pocket_type == FeatureType.POCKET_RECTANGULAR:
            width = pocket_feature.dimensions.get("width", 0)
            length = pocket_feature.dimensions.get("length", 0)
            
            # Calculate aspect ratios
            depth_to_width = depth / width if width > 0 else 1.0
            pocket_feature.properties["depth_to_width_ratio"] = depth_to_width
            
            # Analyze rectangular pocket manufacturability
            if min(width, length) < 2.0:
                manufacturability_issues.append("Narrow pocket dimensions - requires small tooling")
                cost_drivers.append("Small tool operations")
                
            if depth_to_width > 3:
                manufacturability_issues.append("Deep pocket relative to width - may require specialized tooling")
                cost_drivers.append("Deep pocket machining")
                
            # Check for sharp internal corners
            # This would require more detailed geometry analysis in a full implementation
            # For now, we'll assume sharp corners in rectangular pockets
            manufacturability_issues.append("Potential sharp internal corners - consider design for manufacturability")
            cost_drivers.append("Additional operations for internal corners")
            
            # Recommend processes
            recommended_processes.extend(["end_milling", "side_milling"])
            if depth_to_width > 2:
                recommended_processes.append("plunge_milling")
                
        # Common manufacturability checks for all pocket types
        if depth < 0.5:
            manufacturability_issues.append("Very shallow pocket - consider surface machining")
            recommended_processes.extend(["face_milling", "surface_grinding"])
            
        elif depth > 50:
            manufacturability_issues.append("Very deep pocket - consider alternative designs")
            cost_drivers.append("Deep machining operations")
            
        # Calculate complexity score
        complexity = 1.0
        complexity += len(manufacturability_issues) * 0.5
        if pocket_type == FeatureType.POCKET_RECTANGULAR:
            complexity += 0.5  # Rectangular pockets are generally more complex due to corners
            
        # Update the pocket feature with analysis results
        pocket_feature.properties["manufacturability_issues"] = manufacturability_issues
        pocket_feature.properties["cost_drivers"] = cost_drivers
        pocket_feature.properties["recommended_processes"] = recommended_processes
        pocket_feature.properties["complexity_score"] = min(10.0, complexity)
    
    def _extract_bosses(self, obj) -> List[DetailedFeature]:
        """Extract boss features (cylindrical or rectangular protrusions) from the object"""
        bosses = []
        
        try:
            if not hasattr(obj, 'Shape') or not obj.Shape.isValid():
                return bosses
                
            # Get all faces
            faces = obj.Shape.Faces
            if not faces:
                return bosses
                
            # Find potential boss features
            for face_idx, face in enumerate(faces):
                try:
                    # Skip small faces
                    if face.Area < 0.01 * obj.Shape.Area:
                        continue
                        
                    # Check if this is a planar face that could be the top of a boss
                    if str(face.Surface).startswith('<Plane'):
                        # Get face normal
                        face_normal = face.normalAt(0, 0)
                        
                        # Find adjacent faces that could form the sides of a boss
                        adjacent_faces = self._find_adjacent_faces(face, faces)
                        
                        # Check if we have enough adjacent faces to form a boss
                        if len(adjacent_faces) >= 3:  # At least 3 side faces for a boss
                            # Check if adjacent faces are cylindrical (for cylindrical boss)
                            cylindrical_faces = [f for f in adjacent_faces if str(f.Surface).startswith('<Cylinder')]
                            
                            # Check for cylindrical boss
                            if len(cylindrical_faces) == 1 and cylindrical_faces[0].Area > 0.1 * face.Area:
                                # This is likely a cylindrical boss
                                cylinder_face = cylindrical_faces[0]
                                
                                # Get cylinder properties
                                cylinder = cylinder_face.Surface
                                radius = cylinder.Radius
                                axis = cylinder.Axis
                                location = cylinder.Location
                                
                                # Calculate height by projecting face center onto axis
                                face_center = face.CenterOfMass
                                base_center = location
                                height_vector = face_center.sub(base_center)
                                height = abs(height_vector.dot(axis))
                                
                                # Calculate volume
                                volume = math.pi * radius * radius * height
                                
                                # Create boss feature
                                boss = DetailedFeature(
                                    feature_id=f"boss_cylindrical_{face_idx}",
                                    feature_type=FeatureType.BOSS_CIRCULAR,
                                    location={
                                        "x": face_center.x,
                                        "y": face_center.y,
                                        "z": face_center.z
                                    },
                                    dimensions={
                                        "radius": radius,
                                        "height": height,
                                        "diameter": 2 * radius
                                    },
                                    orientation={
                                        "x": axis.x,
                                        "y": axis.y,
                                        "z": axis.z
                                    },
                                    properties={
                                        "shape": "cylindrical",
                                        "top_face_idx": face_idx,
                                        "side_face_idx": faces.index(cylinder_face),
                                        "top_face_area": face.Area,
                                        "side_face_area": cylinder_face.Area,
                                        "volume": volume,
                                        "aspect_ratio": height / (2 * radius) if radius > 0 else 1.0
                                    }
                                )
                                
                                # Analyze manufacturability
                                self._analyze_boss_manufacturability(boss)
                                
                                bosses.append(boss)
                                continue
                            
                            # Check for rectangular boss
                            planar_side_faces = [f for f in adjacent_faces if str(f.Surface).startswith('<Plane')]
                            if len(planar_side_faces) >= 4:  # At least 4 side faces for a rectangular boss
                                # Calculate the average height of the side faces
                                heights = []
                                for side_face in planar_side_faces:
                                    side_normal = side_face.normalAt(0, 0)
                                    # Check if side face is perpendicular to top face
                                    dot_product = abs(side_normal.dot(face_normal))
                                    if dot_product < 0.1:  # Nearly perpendicular
                                        # Calculate height based on bounding box
                                        side_bbox = side_face.BoundBox
                                        height = max(side_bbox.ZLength, side_bbox.YLength, side_bbox.XLength)
                                        heights.append(height)
                                
                                if heights:  # If we found valid side faces
                                    avg_height = sum(heights) / len(heights)
                                    
                                    # Get dimensions from the top face
                                    face_bbox = face.BoundBox
                                    length = face_bbox.XLength
                                    width = face_bbox.YLength
                                    
                                    # Create boss feature
                                    boss = DetailedFeature(
                                        feature_id=f"boss_rectangular_{face_idx}",
                                        feature_type=FeatureType.BOSS_RECTANGULAR,
                                        location={
                                            "x": face.CenterOfMass.x,
                                            "y": face.CenterOfMass.y,
                                            "z": face.CenterOfMass.z
                                        },
                                        dimensions={
                                            "length": length,
                                            "width": width,
                                            "height": avg_height
                                        },
                                        orientation={
                                            "x": face_normal.x,
                                            "y": face_normal.y,
                                            "z": face_normal.z
                                        },
                                        properties={
                                            "shape": "rectangular",
                                            "top_face_idx": face_idx,
                                            "side_face_count": len(planar_side_faces),
                                            "top_face_area": face.Area
                                        }
                                    )
                                    bosses.append(boss)
                except Exception as e:
                    print(f"Error analyzing potential boss at face {face_idx}: {e}")
                    continue
                    
            print(f"Found {len(bosses)} boss features")
            return bosses
            
        except Exception as e:
            print(f"Error extracting bosses: {e}")
            return []
    
    def _find_adjacent_faces(self, face, all_faces):
        """Helper method to find faces adjacent to the given face"""
        adjacent_faces = []
        
        # Get edges of the face
        face_edges = face.Edges
        
        # For each face, check if it shares an edge with our face
        for other_face in all_faces:
            if other_face.isEqual(face):  # Skip the same face
                continue
                
            other_edges = other_face.Edges
            
            # Check if any edge is shared
            for edge in face_edges:
                for other_edge in other_edges:
                    if edge.isEqual(other_edge):  # Found a shared edge
                        adjacent_faces.append(other_face)
                        break
                else:
                    continue
                break
                
        return adjacent_faces
        
    def _analyze_boss_manufacturability(self, boss_feature):
        """Analyze boss manufacturability characteristics"""
        
        boss_type = boss_feature.feature_type
        
        # Get common properties
        height = boss_feature.dimensions.get("height", 0)
        aspect_ratio = boss_feature.properties.get("aspect_ratio", 1.0)
        
        manufacturability_issues = []
        cost_drivers = []
        recommended_processes = []
        
        # Analyze based on boss type
        if boss_type == FeatureType.BOSS_CIRCULAR:
            radius = boss_feature.dimensions.get("radius", 0)
            diameter = boss_feature.dimensions.get("diameter", 0)
            
            # Analyze circular boss manufacturability
            if radius < 1.0:
                manufacturability_issues.append("Very small boss radius - requires precision machining")
                cost_drivers.append("Precision machining operations")
            
            # Check aspect ratio (height to diameter)
            if aspect_ratio > 3:
                manufacturability_issues.append("Tall, thin boss - may have stability issues during machining")
                cost_drivers.append("Special fixturing or support")
                
            # Check for draft angle issues
            # In a complete implementation, we would analyze the actual draft angle
            # For now, we'll assume vertical walls which may cause issues
            manufacturability_issues.append("Potential draft angle issues for molding/casting")
            
            # Recommend processes
            if diameter < 5.0:
                recommended_processes.extend(["CNC milling", "EDM"])
            else:
                recommended_processes.extend(["CNC milling", "turning"])
                
        elif boss_type == FeatureType.BOSS_RECTANGULAR:
            width = boss_feature.dimensions.get("width", 0)
            length = boss_feature.dimensions.get("length", 0)
            
            # Analyze rectangular boss manufacturability
            if min(width, length) < 2.0:
                manufacturability_issues.append("Narrow boss dimensions - requires small tooling")
                cost_drivers.append("Small tool operations")
                
            # Check aspect ratio (height to min width/length)
            min_dimension = min(width, length)
            height_to_width_ratio = height / min_dimension if min_dimension > 0 else 1.0
            
            if height_to_width_ratio > 3:
                manufacturability_issues.append("Tall, thin boss - may have stability issues during machining")
                cost_drivers.append("Special fixturing or support")
                
            # Check for sharp corners
            manufacturability_issues.append("Sharp corners may cause stress concentration")
            recommended_processes.append("Consider adding fillets to corners")
            
            # Recommend processes
            recommended_processes.extend(["CNC milling", "end_milling"])
            
        # Common manufacturability checks for all boss types
        if height < 0.5:
            manufacturability_issues.append("Very short boss - consider alternative design")
            
        elif height > 50:
            manufacturability_issues.append("Very tall boss - consider support structures")
            cost_drivers.append("Stability during machining")
            
        # Calculate complexity score
        complexity = 1.0
        complexity += len(manufacturability_issues) * 0.5
        complexity += aspect_ratio * 0.2
        
        # Update the boss feature with analysis results
        boss_feature.properties["manufacturability_issues"] = manufacturability_issues
        boss_feature.properties["cost_drivers"] = cost_drivers
        boss_feature.properties["recommended_processes"] = recommended_processes
        boss_feature.properties["complexity_score"] = min(10.0, complexity)
    
    def _extract_ribs(self, obj) -> List[DetailedFeature]:
        """Extract rib features (thin, wall-like supporting structures) from the object"""
        ribs = []
        
        try:
            if not hasattr(obj, 'Shape') or not obj.Shape.isValid():
                return ribs
                
            # Get all faces
            faces = obj.Shape.Faces
            if not faces:
                return ribs
            
            # Find potential rib features
            for face_idx, face in enumerate(faces):
                try:
                    # Skip very small faces
                    if face.Area < 0.005 * obj.Shape.Area:
                        continue
                    
                    # Ribs are typically thin, planar faces
                    if str(face.Surface).startswith('<Plane'):
                        # Get face normal
                        face_normal = face.normalAt(0, 0)
                        
                        # Get face bounding box
                        face_bbox = face.BoundBox
                        length = face_bbox.XLength
                        width = face_bbox.YLength
                        height = face_bbox.ZLength
                        
                        # Calculate aspect ratio - ribs are typically thin in one dimension
                        dimensions = [length, width, height]
                        dimensions.sort()
                        thickness = dimensions[0]  # Smallest dimension
                        rib_length = dimensions[2]  # Largest dimension
                        rib_width = dimensions[1]  # Middle dimension
                        
                        # Ribs typically have high aspect ratio (length/thickness)
                        aspect_ratio = rib_length / thickness if thickness > 0 else 0
                        
                        # Check if this could be a rib (high aspect ratio, relatively thin)
                        if aspect_ratio > 5 and thickness < 0.2 * rib_width:
                            # Find adjacent faces
                            adjacent_faces = self._find_adjacent_faces(face, faces)
                            
                            # Ribs typically connect to other faces on both ends
                            if len(adjacent_faces) >= 2:
                                # Calculate rib orientation (along longest dimension)
                                if length >= width and length >= height:
                                    orientation = FreeCAD.Vector(1, 0, 0)  # X-axis
                                elif width >= length and width >= height:
                                    orientation = FreeCAD.Vector(0, 1, 0)  # Y-axis
                                else:
                                    orientation = FreeCAD.Vector(0, 0, 1)  # Z-axis
                                
                                # Adjust orientation to be perpendicular to face normal
                                if abs(orientation.dot(face_normal)) > 0.7:  # If nearly parallel
                                    # Choose a different orientation
                                    if orientation.x == 1:
                                        orientation = FreeCAD.Vector(0, 1, 0)
                                    else:
                                        orientation = FreeCAD.Vector(1, 0, 0)
                                
                                # Determine if this is a structural or cooling rib
                                # (simplified - in reality would need more analysis)
                                is_cooling = False
                                if len(adjacent_faces) > 4:  # More connections suggest cooling function
                                    # Check if any adjacent faces are curved (typical for cooling ribs)
                                    for adj_face in adjacent_faces:
                                        if not str(adj_face.Surface).startswith('<Plane'):
                                            is_cooling = True
                                            break
                                
                                # Create rib feature
                                rib = DetailedFeature(
                                    feature_id=f"rib_{face_idx}",
                                    feature_type=FeatureType.RIB_COOLING if is_cooling else FeatureType.RIB_STRUCTURAL,
                                    location={
                                        "x": face.CenterOfMass.x,
                                        "y": face.CenterOfMass.y,
                                        "z": face.CenterOfMass.z
                                    },
                                    dimensions={
                                        "length": rib_length,
                                        "width": rib_width,
                                        "thickness": thickness
                                    },
                                    orientation={
                                        "x": orientation.x,
                                        "y": orientation.y,
                                        "z": orientation.z
                                    },
                                    properties={
                                        "aspect_ratio": aspect_ratio,
                                        "is_cooling": is_cooling,
                                        "face_idx": face_idx,
                                        "adjacent_face_count": len(adjacent_faces),
                                        "face_area": face.Area,
                                        "volume": face.Area * thickness  # Approximate volume
                                    }
                                )
                                
                                # Analyze manufacturability
                                self._analyze_rib_manufacturability(rib)
                                
                                ribs.append(rib)
                except Exception as e:
                    print(f"Error analyzing potential rib at face {face_idx}: {e}")
                    continue
            
            print(f"Found {len(ribs)} rib features")
            return ribs
            
        except Exception as e:
            print(f"Error extracting ribs: {e}")
            return []
    
    def _analyze_rib_manufacturability(self, rib_feature):
        """Analyze rib manufacturability characteristics"""
        
        # Get rib properties
        thickness = rib_feature.dimensions.get("thickness", 0)
        length = rib_feature.dimensions.get("length", 0)
        width = rib_feature.dimensions.get("width", 0)
        aspect_ratio = rib_feature.properties.get("aspect_ratio", 1.0)
        is_cooling = rib_feature.properties.get("is_cooling", False)
        
        manufacturability_issues = []
        cost_drivers = []
        recommended_processes = []
        
        # Analyze thickness
        if thickness < 0.8:
            manufacturability_issues.append("Very thin rib - may cause molding/machining issues")
            cost_drivers.append("Precision machining requirements")
            recommended_processes.extend(["high_precision_milling", "thin_wall_molding"])
        
        # Analyze aspect ratio (length to thickness)
        if aspect_ratio > 10:
            manufacturability_issues.append("High aspect ratio - potential warping or deflection")
            cost_drivers.append("Special tooling or support structures")
            
        # Analyze draft angle (simplified - would need more detailed geometry analysis)
        manufacturability_issues.append("Check draft angles for molding/casting")
        
        # Analyze based on rib type
        if is_cooling:
            # Cooling ribs specific analysis
            manufacturability_issues.append("Ensure adequate spacing between cooling ribs")
            if thickness > 2.0:
                manufacturability_issues.append("Thick cooling rib - may reduce thermal efficiency")
            recommended_processes.extend(["die_casting", "investment_casting"])
        else:
            # Structural ribs specific analysis
            if thickness < 0.3 * width:
                manufacturability_issues.append("Thin structural rib relative to width - potential stability issues")
            recommended_processes.extend(["injection_molding", "CNC_milling"])
        
        # Analyze rib base transition
        manufacturability_issues.append("Check for proper fillets at rib base to reduce stress concentration")
        
        # Calculate complexity score
        complexity = 1.0
        complexity += len(manufacturability_issues) * 0.5
        complexity += aspect_ratio * 0.1
        if is_cooling:
            complexity += 0.5  # Cooling ribs are generally more complex
        
        # Update the rib feature with analysis results
        rib_feature.properties["manufacturability_issues"] = manufacturability_issues
        rib_feature.properties["cost_drivers"] = cost_drivers
        rib_feature.properties["recommended_processes"] = recommended_processes
        rib_feature.properties["complexity_score"] = min(10.0, complexity)
    
    def _extract_fillets(self, obj) -> List[DetailedFeature]:
        """Extract fillet features (rounded edges or corners) from the object"""
        fillets = []
        
        try:
            if not hasattr(obj, 'Shape') or not obj.Shape.isValid():
                return fillets
                
            # Get all faces and edges
            faces = obj.Shape.Faces
            edges = obj.Shape.Edges
            if not faces or not edges:
                return fillets
            
            # Find cylindrical and toroidal faces (potential fillets)
            for face_idx, face in enumerate(faces):
                try:
                    # Check for cylindrical faces (potential fillets)
                    if str(face.Surface).startswith('<Cylinder'):
                        # Get cylinder properties
                        cylinder = face.Surface
                        radius = cylinder.Radius
                        
                        # Fillets typically have small radii relative to the part size
                        if radius < 0.1 * max(obj.Shape.BoundBox.XLength, 
                                            obj.Shape.BoundBox.YLength, 
                                            obj.Shape.BoundBox.ZLength):
                            
                            # Find adjacent faces
                            adjacent_faces = self._find_adjacent_faces(face, faces)
                            
                            # Fillets typically connect two planar faces
                            planar_adjacent = [f for f in adjacent_faces if str(f.Surface).startswith('<Plane')]
                            
                            if len(planar_adjacent) >= 2:
                                # Determine if internal or external fillet
                                # For internal fillets, the cylinder axis points away from the part center
                                is_internal = False
                                
                                # Get part center and face center
                                part_center = obj.Shape.CenterOfMass
                                face_center = face.CenterOfMass
                                
                                # Vector from part center to face center
                                center_vector = face_center.sub(part_center)
                                
                                # Get cylinder axis
                                axis = cylinder.Axis
                                
                                # If dot product is positive, vectors point in similar direction
                                # suggesting an external fillet
                                dot_product = center_vector.dot(axis)
                                is_internal = dot_product < 0
                                
                                # Create fillet feature
                                fillet = DetailedFeature(
                                    feature_id=f"fillet_{face_idx}",
                                    feature_type=FeatureType.FILLET_INTERNAL if is_internal else FeatureType.FILLET_EXTERNAL,
                                    location={
                                        "x": face_center.x,
                                        "y": face_center.y,
                                        "z": face_center.z
                                    },
                                    dimensions={
                                        "radius": radius,
                                        "length": face.BoundBox.DiagonalLength
                                    },
                                    orientation={
                                        "x": axis.x,
                                        "y": axis.y,
                                        "z": axis.z
                                    },
                                    properties={
                                        "is_internal": is_internal,
                                        "face_idx": face_idx,
                                        "face_area": face.Area,
                                        "adjacent_face_count": len(adjacent_faces)
                                    }
                                )
                                fillets.append(fillet)
                    
                    # Check for toroidal faces (potential fillets at corners)
                    elif str(face.Surface).startswith('<Toroid'):
                        # Get torus properties
                        torus = face.Surface
                        major_radius = torus.MajorRadius
                        minor_radius = torus.MinorRadius
                        
                        # Fillets typically have small radii relative to the part size
                        if minor_radius < 0.1 * max(obj.Shape.BoundBox.XLength, 
                                                obj.Shape.BoundBox.YLength, 
                                                obj.Shape.BoundBox.ZLength):
                            
                            # Find adjacent faces
                            adjacent_faces = self._find_adjacent_faces(face, faces)
                            
                            # Corner fillets typically connect three or more faces
                            if len(adjacent_faces) >= 3:
                                # Determine if internal or external fillet (similar to cylindrical case)
                                is_internal = False
                                
                                # Get part center and face center
                                part_center = obj.Shape.CenterOfMass
                                face_center = face.CenterOfMass
                                
                                # Vector from part center to face center
                                center_vector = face_center.sub(part_center)
                                
                                # Get torus axis
                                axis = torus.Axis
                                
                                # If dot product is positive, vectors point in similar direction
                                # suggesting an external fillet
                                dot_product = center_vector.dot(axis)
                                is_internal = dot_product < 0
                                
                                # Create fillet feature
                                fillet = DetailedFeature(
                                    feature_id=f"corner_fillet_{face_idx}",
                                    feature_type=FeatureType.FILLET_INTERNAL if is_internal else FeatureType.FILLET_EXTERNAL,
                                    location={
                                        "x": face_center.x,
                                        "y": face_center.y,
                                        "z": face_center.z
                                    },
                                    dimensions={
                                        "radius": minor_radius,
                                        "major_radius": major_radius
                                    },
                                    orientation={
                                        "x": axis.x,
                                        "y": axis.y,
                                        "z": axis.z
                                    },
                                    properties={
                                        "is_internal": is_internal,
                                        "is_corner": True,
                                        "face_idx": face_idx,
                                        "face_area": face.Area,
                                        "adjacent_face_count": len(adjacent_faces)
                                    }
                                )
                                fillets.append(fillet)
                                
                except Exception as e:
                    print(f"Error analyzing potential fillet at face {face_idx}: {e}")
                    continue
            
            print(f"Found {len(fillets)} fillet features")
            return fillets
            
        except Exception as e:
            print(f"Error extracting fillets: {e}")
            return []
    
    def _analyze_fillet_manufacturability(self, fillet_feature):
        """Analyze fillet manufacturability characteristics"""
        
        # Get fillet properties
        radius = fillet_feature.dimensions.get("radius", 0)
        is_internal = fillet_feature.properties.get("is_internal", False)
        is_corner = fillet_feature.properties.get("is_corner", False)
        
        manufacturability_issues = []
        cost_drivers = []
        recommended_processes = []
        
        # Analyze radius
        if radius < 0.5:
            manufacturability_issues.append("Very small fillet radius - may require precision machining")
            cost_drivers.append("Precision tooling requirements")
            recommended_processes.extend(["EDM", "precision_milling"])
        
        # Analyze based on fillet type
        if is_internal:
            # Internal fillets specific analysis
            if radius < 1.0:
                manufacturability_issues.append("Small internal radius - tool access limitations")
                cost_drivers.append("Special tooling requirements")
            
            # Internal corners are particularly challenging
            if is_corner:
                manufacturability_issues.append("Internal corner fillet - difficult to machine")
                cost_drivers.append("Complex machining operations")
                recommended_processes.append("Consider redesign if possible")
            
            recommended_processes.extend(["milling_with_radius_tool", "broaching"])
        else:
            # External fillets specific analysis
            if radius > 5.0:
                manufacturability_issues.append("Large external fillet - material removal considerations")
            
            recommended_processes.extend(["standard_milling", "turning"])
        
        # Analyze consistency
        manufacturability_issues.append("Check for consistent fillet radius throughout the model")
        
        # Calculate complexity score
        complexity = 1.0
        complexity += len(manufacturability_issues) * 0.5
        
        if is_internal:
            complexity += 1.0  # Internal fillets are generally more complex
        
        if is_corner:
            complexity += 1.0  # Corner fillets are more complex
        
        if radius < 1.0:
            complexity += (1.0 - radius)  # Smaller radii increase complexity
        
        # Update the fillet feature with analysis results
        fillet_feature.properties["manufacturability_issues"] = manufacturability_issues
        fillet_feature.properties["cost_drivers"] = cost_drivers
        fillet_feature.properties["recommended_processes"] = recommended_processes
        fillet_feature.properties["complexity_score"] = min(10.0, complexity)
    
    def _extract_thin_walls(self, obj) -> List[DetailedFeature]:
        """Extract thin wall features from the object"""
        thin_walls = []
        
        try:
            if not hasattr(obj, 'Shape') or not obj.Shape.isValid():
                return thin_walls
                
            # Get all faces
            faces = obj.Shape.Faces
            if not faces:
                return thin_walls
            
            # Use wall thickness analysis to identify thin walls
            # First, sample points on the surface
            sample_points = []
            face_normals = []
            face_indices = []
            
            # Sample points from each face
            for face_idx, face in enumerate(faces):
                try:
                    # Skip very small faces
                    if face.Area < 0.01 * obj.Shape.Area:
                        continue
                        
                    # Get face center and normal
                    face_center = face.CenterOfMass
                    face_normal = face.normalAt(0, 0)
                    
                    # Add center point
                    sample_points.append(face_center)
                    face_normals.append(face_normal)
                    face_indices.append(face_idx)
                    
                    # Add additional points for larger faces
                    if face.Area > 0.05 * obj.Shape.Area:
                        # Sample additional points using UV parameters
                        try:
                            u_range = face.ParameterRange[1] - face.ParameterRange[0]
                            v_range = face.ParameterRange[3] - face.ParameterRange[2]
                            
                            # Sample 4 additional points
                            for u_frac in [0.25, 0.75]:
                                for v_frac in [0.25, 0.75]:
                                    u = face.ParameterRange[0] + u_frac * u_range
                                    v = face.ParameterRange[2] + v_frac * v_range
                                    
                                    point = face.valueAt(u, v)
                                    normal = face.normalAt(u, v)
                                    
                                    sample_points.append(point)
                                    face_normals.append(normal)
                                    face_indices.append(face_idx)
                        except:
                            # Fall back to simple sampling if UV parameterization fails
                            pass
                except:
                    continue
            
            # Measure thickness at each sample point
            thin_wall_threshold = 1.0  # Define thin wall as < 1mm thick
            critical_threshold = 0.5   # Define critical thin wall as < 0.5mm thick
            
            # Track processed regions to avoid duplicates
            processed_regions = set()
            
            for i, (point, normal, face_idx) in enumerate(zip(sample_points, face_normals, face_indices)):
                try:
                    # Skip if we've already processed a nearby point
                    skip = False
                    point_key = (round(point.x, 1), round(point.y, 1), round(point.z, 1))
                    if point_key in processed_regions:
                        continue
                    
                    # Measure thickness along normal direction
                    thickness = self._measure_thickness_at_point(obj.Shape, point, normal)
                    
                    # If thin wall detected
                    if thickness > 0 and thickness < thin_wall_threshold:
                        # Create thin wall feature
                        thin_wall = DetailedFeature(
                            feature_id=f"thin_wall_{len(thin_walls)}",
                            feature_type=FeatureType.THIN_WALL,
                            location={
                                "x": point.x,
                                "y": point.y,
                                "z": point.z
                            },
                            dimensions={
                                "thickness": thickness,
                                "area": faces[face_idx].Area if face_idx < len(faces) else 0
                            },
                            orientation={
                                "x": normal.x,
                                "y": normal.y,
                                "z": normal.z
                            },
                            properties={
                                "is_critical": thickness < critical_threshold,
                                "face_idx": face_idx,
                                "severity": "high" if thickness < critical_threshold else "medium",
                                "material_volume": thickness * (faces[face_idx].Area if face_idx < len(faces) else 1.0)
                            }
                        )
                        
                        # Analyze manufacturability
                        self._analyze_thin_wall_manufacturability(thin_wall)
                        
                        thin_walls.append(thin_wall)
                        
                        # Mark this region as processed
                        processed_regions.add(point_key)
                except Exception as e:
                    print(f"Error analyzing potential thin wall at point {i}: {e}")
                    continue
            
            print(f"Found {len(thin_walls)} thin wall features")
            return thin_walls
            
        except Exception as e:
            print(f"Error extracting thin walls: {e}")
            return []
    
    def _analyze_thin_wall_manufacturability(self, thin_wall_feature):
        """Analyze thin wall manufacturability characteristics"""
        
        # Get thin wall properties
        thickness = thin_wall_feature.dimensions.get("thickness", 0)
        area = thin_wall_feature.dimensions.get("area", 0)
        is_critical = thin_wall_feature.properties.get("is_critical", False)
        
        manufacturability_issues = []
        cost_drivers = []
        recommended_processes = []
        
        # Analyze thickness
        if thickness < 0.5:
            manufacturability_issues.append("Critically thin wall - high risk of warping, breakage during manufacturing")
            cost_drivers.append("Special handling requirements")
            recommended_processes.append("Consider redesign to increase wall thickness")
        elif thickness < 0.8:
            manufacturability_issues.append("Very thin wall - risk of warping during manufacturing")
            cost_drivers.append("Slower cooling cycles")
        elif thickness < 1.2:
            manufacturability_issues.append("Thin wall - monitor for potential issues")
        
        # Analyze area to thickness ratio
        if area > 0:
            area_to_thickness_ratio = area / thickness if thickness > 0 else float('inf')
            if area_to_thickness_ratio > 1000:
                manufacturability_issues.append("Large thin wall area - high risk of warping")
                cost_drivers.append("Custom support structures")
                recommended_processes.append("Consider adding ribs or increasing thickness")
        
        # Recommend manufacturing processes based on thickness
        if thickness < 0.5:
            recommended_processes.extend(["thin_wall_injection_molding", "die_casting_with_vacuum"])
        elif thickness < 1.0:
            recommended_processes.extend(["standard_injection_molding", "die_casting"])
        else:
            recommended_processes.extend(["standard_manufacturing_processes"])
        
        # Material recommendations
        if thickness < 0.8:
            manufacturability_issues.append("Material selection critical for thin walls")
            recommended_processes.append("Consider high-flow materials")
        
        # Calculate complexity score
        complexity = 1.0
        if thickness < 0.5:
            complexity += 3.0
        elif thickness < 0.8:
            complexity += 2.0
        elif thickness < 1.2:
            complexity += 1.0
            
        complexity += len(manufacturability_issues) * 0.5
        
        if is_critical:
            complexity += 2.0
        
        # Update the thin wall feature with analysis results
        thin_wall_feature.properties["manufacturability_issues"] = manufacturability_issues
        thin_wall_feature.properties["cost_drivers"] = cost_drivers
        thin_wall_feature.properties["recommended_processes"] = recommended_processes
        thin_wall_feature.properties["complexity_score"] = min(10.0, complexity)
    
    def _extract_undercuts(self, obj) -> List[DetailedFeature]:
        """Extract undercut features (areas that prevent direct part ejection) from the object"""
        undercuts = []
        
        try:
            if not hasattr(obj, 'Shape') or not obj.Shape.isValid():
                return undercuts
                
            # Get all faces
            faces = obj.Shape.Faces
            if not faces:
                return undercuts
            
            # Define primary pull directions (typically along major axes)
            pull_directions = [
                FreeCAD.Vector(0, 0, 1),   # Z+
                FreeCAD.Vector(0, 0, -1),  # Z-
                FreeCAD.Vector(1, 0, 0),   # X+
                FreeCAD.Vector(-1, 0, 0),  # X-
                FreeCAD.Vector(0, 1, 0),   # Y+
                FreeCAD.Vector(0, -1, 0)   # Y-
            ]
            
            # Find best pull direction (with fewest negative draft angles)
            best_direction = None
            min_negative_count = float('inf')
            
            for pull_direction in pull_directions:
                negative_count = 0
                
                for face in faces:
                    try:
                        # Skip very small faces
                        if face.Area < 0.01 * obj.Shape.Area:
                            continue
                            
                        # Get face normal
                        face_normal = face.normalAt(0, 0)
                        
                        # Calculate draft angle (angle between face normal and pull direction)
                        dot_product = face_normal.x * pull_direction.x + \
                                     face_normal.y * pull_direction.y + \
                                     face_normal.z * pull_direction.z
                                     
                        normal_length = math.sqrt(face_normal.x**2 + face_normal.y**2 + face_normal.z**2)
                        direction_length = math.sqrt(pull_direction.x**2 + pull_direction.y**2 + pull_direction.z**2)
                        
                        if normal_length > 0 and direction_length > 0:
                            cos_angle = dot_product / (normal_length * direction_length)
                            # Clamp to valid range due to floating point errors
                            cos_angle = max(-1.0, min(1.0, cos_angle))
                            angle_rad = math.acos(cos_angle)
                            angle_deg = math.degrees(angle_rad)
                            
                            # Adjust angle to be relative to pull direction (0° is parallel, 90° is perpendicular)
                            draft_angle = 90 - angle_deg
                            
                            # Check if it's negative draft (undercut)
                            if draft_angle < 0:
                                negative_count += 1
                    except:
                        continue
                
                # Update best direction if this one has fewer negative drafts
                if negative_count < min_negative_count:
                    min_negative_count = negative_count
                    best_direction = pull_direction
            
            # If no best direction found, use Z+ as default
            if not best_direction:
                best_direction = FreeCAD.Vector(0, 0, 1)
            
            # Now identify undercuts using the best pull direction
            for face_idx, face in enumerate(faces):
                try:
                    # Skip very small faces
                    if face.Area < 0.01 * obj.Shape.Area:
                        continue
                        
                    # Get face normal
                    face_normal = face.normalAt(0, 0)
                    
                    # Calculate draft angle
                    dot_product = face_normal.x * best_direction.x + \
                                 face_normal.y * best_direction.y + \
                                 face_normal.z * best_direction.z
                                 
                    normal_length = math.sqrt(face_normal.x**2 + face_normal.y**2 + face_normal.z**2)
                    direction_length = math.sqrt(best_direction.x**2 + best_direction.y**2 + best_direction.z**2)
                    
                    if normal_length > 0 and direction_length > 0:
                        cos_angle = dot_product / (normal_length * direction_length)
                        # Clamp to valid range due to floating point errors
                        cos_angle = max(-1.0, min(1.0, cos_angle))
                        angle_rad = math.acos(cos_angle)
                        angle_deg = math.degrees(angle_rad)
                        
                        # Adjust angle to be relative to pull direction
                        draft_angle = 90 - angle_deg
                        
                        # Check if it's a significant undercut
                        if draft_angle < -5:  # More than 5 degrees negative draft
                            # Determine undercut type (groove or relief)
                            # This is a simplified heuristic - in reality would need more analysis
                            is_groove = False
                            
                            # Find adjacent faces
                            adjacent_faces = self._find_adjacent_faces(face, faces)
                            
                            # If this face connects to many others, it's more likely a groove
                            if len(adjacent_faces) > 3:
                                is_groove = True
                            
                            # Create undercut feature
                            undercut = DetailedFeature(
                                feature_id=f"undercut_{face_idx}",
                                feature_type=FeatureType.UNDERCUT_GROOVE if is_groove else FeatureType.UNDERCUT_RELIEF,
                                location={
                                    "x": face.CenterOfMass.x,
                                    "y": face.CenterOfMass.y,
                                    "z": face.CenterOfMass.z
                                },
                                dimensions={
                                    "area": face.Area,
                                    "draft_angle": draft_angle,
                                    "depth": face.BoundBox.DiagonalLength * 0.5  # Approximate depth
                                },
                                orientation={
                                    "x": face_normal.x,
                                    "y": face_normal.y,
                                    "z": face_normal.z
                                },
                                properties={
                                    "is_groove": is_groove,
                                    "face_idx": face_idx,
                                    "pull_direction": {
                                        "x": best_direction.x,
                                        "y": best_direction.y,
                                        "z": best_direction.z
                                    },
                                    "severity": "high" if draft_angle < -15 else "medium",
                                    "adjacent_face_count": len(adjacent_faces)
                                }
                            )
                            
                            # Analyze manufacturability
                            self._analyze_undercut_manufacturability(undercut)
                            
                            undercuts.append(undercut)
                except Exception as e:
                    print(f"Error analyzing potential undercut at face {face_idx}: {e}")
                    continue
            
            print(f"Found {len(undercuts)} undercut features")
            return undercuts
            
        except Exception as e:
            print(f"Error extracting undercuts: {e}")
            return []
    
    def _analyze_undercut_manufacturability(self, undercut_feature):
        """Analyze undercut manufacturability characteristics"""
        
        # Get undercut properties
        draft_angle = undercut_feature.dimensions.get("draft_angle", 0)
        area = undercut_feature.dimensions.get("area", 0)
        depth = undercut_feature.dimensions.get("depth", 0)
        is_groove = undercut_feature.properties.get("is_groove", False)
        severity = undercut_feature.properties.get("severity", "medium")
        
        manufacturability_issues = []
        cost_drivers = []
        recommended_processes = []
        
        # Analyze draft angle
        if draft_angle < -30:
            manufacturability_issues.append("Extreme negative draft angle - cannot be molded without side actions")
            cost_drivers.append("Complex mold with side actions")
            recommended_processes.append("Consider redesign to eliminate or reduce undercut")
        elif draft_angle < -15:
            manufacturability_issues.append("Severe negative draft angle - requires side actions in mold")
            cost_drivers.append("Side action mechanisms")
        elif draft_angle < -5:
            manufacturability_issues.append("Moderate negative draft angle - may require special considerations")
        
        # Analyze based on undercut type
        if is_groove:
            # Groove-specific analysis
            manufacturability_issues.append("Internal groove requires special tooling")
            
            if depth > 10:
                manufacturability_issues.append("Deep groove - difficult to machine")
                cost_drivers.append("Special tooling for deep grooves")
            
            if area > 1000:
                manufacturability_issues.append("Large groove area - consider segmenting")
            
            recommended_processes.extend(["side_action_mold", "collapsible_core"])
        else:
            # Relief undercut analysis
            if area > 500:
                manufacturability_issues.append("Large relief area - may cause ejection issues")
            
            recommended_processes.extend(["side_action_mold", "hand_loaded_insert"])
        
        # Common manufacturability checks
        if severity == "high":
            manufacturability_issues.append("Critical undercut - significant impact on moldability")
            cost_drivers.append("Complex mold design")
            recommended_processes.append("Consider redesign if possible")
        
        # Calculate complexity score
        complexity = 1.0
        complexity += abs(draft_angle) * 0.1  # More negative angle = higher complexity
        complexity += len(manufacturability_issues) * 0.5
        
        if is_groove:
            complexity += 1.0  # Grooves are generally more complex
        
        if severity == "high":
            complexity += 2.0
        
        # Update the undercut feature with analysis results
        undercut_feature.properties["manufacturability_issues"] = manufacturability_issues
        undercut_feature.properties["cost_drivers"] = cost_drivers
        undercut_feature.properties["recommended_processes"] = recommended_processes
        undercut_feature.properties["complexity_score"] = min(10.0, complexity)
    
    # Placeholder analysis methods - implemented in Part 3
    def _analyze_housing(self, doc, geometry):
        pass
    
    def _analyze_bracket(self, doc, geometry):
        pass
    
    def _analyze_gear(self, doc, geometry):
        pass
    
    def _analyze_shaft(self, doc, geometry):
        pass
    
    def _analyze_thin_walled_part(self, doc, geometry):
        pass
    
    def _analyze_mechanical_component(self, doc, geometry):
        pass


# ==========================================
# API FORMAT CONVERTER
# ==========================================

class DFMAPIFormatConverter:
    """Converts comprehensive CAD geometry to DFM API format"""
    
    def __init__(self):
        self.feature_converters = {}
        self._initialize_converters()
    
    def _initialize_converters(self):
        """Initialize feature-specific converters"""
        self.feature_converters = {
            FeatureType.HOLE_THROUGH: self._convert_hole,
            FeatureType.HOLE_BLIND: self._convert_hole,
            FeatureType.POCKET_RECTANGULAR: self._convert_pocket,
            FeatureType.POCKET_CIRCULAR: self._convert_pocket,
            FeatureType.BOSS_CIRCULAR: self._convert_boss,
            FeatureType.RIB_STRUCTURAL: self._convert_rib,
            FeatureType.FILLET_INTERNAL: self._convert_fillet,
            FeatureType.THIN_WALL: self._convert_thin_wall,
            FeatureType.UNDERCUT_GROOVE: self._convert_undercut
        }
    
    def convert_to_api_format(self, geometry: ComprehensiveCADGeometry) -> Dict[str, Any]:
        """
        Convert comprehensive CAD geometry to DFM API format
        
        Args:
            geometry: ComprehensiveCADGeometry object with complete analysis
            
        Returns:
            Dictionary in DFM API format
        """
        
        try:
            # Basic properties
            api_data = {
                "part_name": geometry.part_name,
                "part_type": geometry.part_type.value,
                "volume": geometry.volume,
                "surface_area": geometry.surface_area,
                "dimensions": geometry.overall_dimensions,
                "bounding_box": geometry.bounding_box,
                "center_of_mass": geometry.center_of_mass,
                "extraction_quality": geometry.extraction_quality,
                "complexity_index": geometry.geometric_complexity_index,
                "features": [],
                "manufacturing_analysis": {}
            }
            
            # Convert features
            for feature in geometry.features:
                if feature.feature_type in self.feature_converters:
                    converter = self.feature_converters[feature.feature_type]
                    api_feature = converter(feature)
                    if api_feature:
                        api_data["features"].append(api_feature)
            
            # Add wall thickness analysis
            if geometry.wall_thickness_analysis:
                api_data["manufacturing_analysis"]["wall_thickness"] = [
                    {
                        "location": wt.location,
                        "thickness": wt.thickness,
                        "is_critical": wt.is_critical,
                        "severity": wt.severity
                    } for wt in geometry.wall_thickness_analysis
                ]
            
            # Add material flow analysis
            if geometry.material_flow_analysis:
                api_data["manufacturing_analysis"]["material_flow"] = [
                    {
                        "location": mf.location,
                        "flow_quality": mf.flow_quality,
                        "is_critical": mf.is_critical,
                        "severity": mf.severity
                    } for mf in geometry.material_flow_analysis
                ]
            
            # Add draft analysis
            if geometry.draft_analysis:
                api_data["manufacturing_analysis"]["draft_angles"] = geometry.draft_analysis
            
            # Add undercut analysis
            if geometry.undercut_analysis:
                api_data["manufacturing_analysis"]["undercuts"] = geometry.undercut_analysis
            
            # Add stress concentration analysis
            if geometry.stress_concentration_analysis:
                api_data["manufacturing_analysis"]["stress_concentrations"] = geometry.stress_concentration_analysis
            
            # Add tolerances and surface finishes
            if geometry.tolerances:
                api_data["specifications"] = {
                    "tolerances": [
                        {
                            "type": tol.tolerance_type.value,
                            "value": tol.value,
                            "feature_id": tol.feature_id,
                            "description": tol.description
                        } for tol in geometry.tolerances
                    ],
                    "surface_finishes": [
                        {
                            "type": sf.finish_type.value,
                            "value": sf.value,
                            "feature_id": sf.feature_id,
                            "description": sf.description
                        } for sf in geometry.surface_finishes
                    ]
                }
            
            # Add validation errors if any
            if geometry.validation_errors:
                api_data["validation_errors"] = geometry.validation_errors
            
            return api_data
            
        except Exception as e:
            print(f"Error converting to API format: {e}")
            traceback.print_exc()
            
            # Return minimal data with error info
            return {
                "part_name": geometry.part_name,
                "part_type": geometry.part_type.value if hasattr(geometry.part_type, 'value') else "unknown",
                "extraction_quality": "poor",
                "validation_errors": [f"API conversion failed: {str(e)}"] + geometry.validation_errors
            }
    
    # Feature conversion methods - placeholders for now
    def _convert_hole(self, feature: DetailedFeature) -> Dict[str, Any]:
        return {
            "id": feature.feature_id,
            "type": feature.feature_type.value,
            "location": feature.location,
            "dimensions": feature.dimensions,
            "orientation": feature.orientation,
            "properties": feature.properties
        }
    
    def _convert_pocket(self, feature: DetailedFeature) -> Dict[str, Any]:
        return {
            "id": feature.feature_id,
            "type": feature.feature_type.value,
            "location": feature.location,
            "dimensions": feature.dimensions,
            "orientation": feature.orientation,
            "properties": feature.properties
        }
    
    def _convert_boss(self, feature: DetailedFeature) -> Dict[str, Any]:
        return {
            "id": feature.feature_id,
            "type": feature.feature_type.value,
            "location": feature.location,
            "dimensions": feature.dimensions,
            "orientation": feature.orientation,
            "properties": feature.properties
        }
    
    def _convert_rib(self, feature: DetailedFeature) -> Dict[str, Any]:
        return {
            "id": feature.feature_id,
            "type": feature.feature_type.value,
            "location": feature.location,
            "dimensions": feature.dimensions,
            "orientation": feature.orientation,
            "properties": feature.properties
        }
    
    def _convert_fillet(self, feature: DetailedFeature) -> Dict[str, Any]:
        return {
            "id": feature.feature_id,
            "type": feature.feature_type.value,
            "location": feature.location,
            "dimensions": {"radius": feature.dimensions.get("radius", 0.0)},
            "properties": feature.properties
        }
    
    def _convert_thin_wall(self, feature: DetailedFeature) -> Dict[str, Any]:
        return {
            "id": feature.feature_id,
            "type": feature.feature_type.value,
            "location": feature.location,
            "dimensions": {"thickness": feature.dimensions.get("thickness", 0.0)},
            "orientation": feature.orientation,
            "properties": feature.properties
        }
    
    def _convert_undercut(self, feature: DetailedFeature) -> Dict[str, Any]:
        return {
            "id": feature.feature_id,
            "type": feature.feature_type.value,
            "location": feature.location,
            "dimensions": feature.dimensions,
            "orientation": feature.orientation,
            "properties": feature.properties
        }


# ==========================================
# INTEGRATION FUNCTIONS
# ==========================================

def analyze_freecad_document(document_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze FreeCAD document and return comprehensive geometry in API format
    
    Args:
        document_name: Name of FreeCAD document to analyze (None for active)
        
    Returns:
        Dictionary with comprehensive geometry in DFM API format
    """
    
    analyzer = ProductionCADAnalyzer()
    converter = DFMAPIFormatConverter()
    
    try:
        # Extract comprehensive geometry
        geometry = analyzer.extract_comprehensive_geometry(document_name)
        
        # Convert to API format
        api_data = converter.convert_to_api_format(geometry)
        
        return api_data
        
    except Exception as e:
        print(f"Error analyzing document: {e}")
        traceback.print_exc()
        
        # Return error data
        return {
            "part_name": document_name if document_name else "Unknown",
            "part_type": "unknown",
            "extraction_quality": "poor",
            "validation_errors": [f"Analysis failed: {str(e)}"]
        }


def analyze_freecad_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze FreeCAD file and return comprehensive geometry in API format
    
    Args:
        file_path: Path to FreeCAD file
        
    Returns:
        Dictionary with comprehensive geometry in DFM API format
    """
    
    if not FREECAD_AVAILABLE:
        return {
            "part_name": os.path.basename(file_path),
            "part_type": "unknown",
            "extraction_quality": "poor",
            "validation_errors": ["FreeCAD modules not available"]
        }
    
    try:
        # Open document
        doc = FreeCAD.openDocument(file_path)
        
        # Analyze document
        result = analyze_freecad_document(doc.Name)
        
        # Close document
        FreeCAD.closeDocument(doc.Name)
        
        return result
        
    except Exception as e:
        print(f"Error analyzing file: {e}")
        traceback.print_exc()
        
        # Return error data
        return {
            "part_name": os.path.basename(file_path),
            "part_type": "unknown",
            "extraction_quality": "poor",
            "validation_errors": [f"File analysis failed: {str(e)}"]
        }


# ==========================================
# TESTING FRAMEWORK
# ==========================================

def test_analyzer(test_file_path: Optional[str] = None):
    """
    Test the production CAD analyzer with a sample file
    
    Args:
        test_file_path: Path to test FreeCAD file (None for built-in test)
    """
    
    if not FREECAD_AVAILABLE:
        print("\n❌ FreeCAD modules not available. Cannot run test.")
        return
    
    print("\n🧪 Testing Production CAD Analyzer...")
    
    try:
        # Create test document if no file provided
        if not test_file_path:
            print("\n📐 Creating test geometry...")
            doc = FreeCAD.newDocument("TestGeometry")
            
            # Create a simple box
            box = doc.addObject("Part::Box", "Box")
            box.Length = 100.0
            box.Width = 50.0
            box.Height = 25.0
            
            # Create a cylinder
            cylinder = doc.addObject("Part::Cylinder", "Cylinder")
            cylinder.Radius = 10.0
            cylinder.Height = 30.0
            cylinder.Placement.Base = FreeCAD.Vector(25, 25, 0)
            
            # Update document
            doc.recompute()
            
            test_doc_name = doc.Name
        else:
            # Open provided file
            print(f"\n📂 Opening test file: {test_file_path}")
            doc = FreeCAD.openDocument(test_file_path)
            test_doc_name = doc.Name
        
        # Run analyzer
        print("\n🔍 Running analyzer...")
        result = analyze_freecad_document(test_doc_name)
        
        # Print results
        print("\n📊 Analysis Results:")
        print(f"Part Name: {result.get('part_name')}")
        print(f"Part Type: {result.get('part_type')}")
        print(f"Volume: {result.get('volume', 0):.2f} mm³")
        print(f"Surface Area: {result.get('surface_area', 0):.2f} mm²")
        print(f"Dimensions: {result.get('dimensions', {})}")
        print(f"Extraction Quality: {result.get('extraction_quality')}")
        
        # Print features
        features = result.get('features', [])
        print(f"\n🧩 Features Extracted: {len(features)}")
        for i, feature in enumerate(features[:5]):  # Show first 5 features
            print(f"  Feature {i+1}: {feature.get('type')} at {feature.get('location')}")
        
        # Print manufacturing analysis
        mfg_analysis = result.get('manufacturing_analysis', {})
        print(f"\n⚙️ Manufacturing Analysis:")
        for key, value in mfg_analysis.items():
            if isinstance(value, list):
                print(f"  {key}: {len(value)} issues")
            else:
                print(f"  {key}: {value}")
        
        # Print validation errors
        errors = result.get('validation_errors', [])
        if errors:
            print(f"\n❌ Validation Errors: {len(errors)}")
            for error in errors:
                print(f"  - {error}")
        else:
            print("\n✅ No validation errors")
        
        # Clean up
        if not test_file_path:
            FreeCAD.closeDocument(test_doc_name)
        
        print("\n✅ Test completed successfully")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()


# Run test if executed directly
if __name__ == "__main__":
    test_analyzer()
