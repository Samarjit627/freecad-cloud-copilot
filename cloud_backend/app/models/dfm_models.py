"""
Industry-Grade DFM Analysis Models
Provides data models for advanced Design for Manufacturing analysis
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union, Literal
from enum import Enum


class ProcessType(str, Enum):
    INJECTION_MOLDING = "injection_molding"
    CNC_MILLING = "cnc_milling"
    CNC_TURNING = "cnc_turning"
    FDM_PRINTING = "fdm_printing"
    SLA_PRINTING = "sla_printing"
    SLS_PRINTING = "sls_printing"
    SHEET_METAL = "sheet_metal"
    CASTING = "casting"
    FORGING = "forging"
    EXTRUSION = "extrusion"


class MaterialType(str, Enum):
    # Plastics
    ABS = "abs"
    PLA = "pla"
    PETG = "petg"
    NYLON = "nylon"
    POLYCARBONATE = "polycarbonate"
    POM = "pom"
    PEEK = "peek"
    
    # Metals
    ALUMINUM = "aluminum"
    STEEL = "steel"
    STAINLESS_STEEL = "stainless_steel"
    TITANIUM = "titanium"
    COPPER = "copper"
    BRASS = "brass"
    
    # Composites
    CARBON_FIBER = "carbon_fiber"
    GLASS_FIBER = "glass_fiber"


class Point3D(BaseModel):
    x: float
    y: float
    z: float


class BoundingBox(BaseModel):
    length: float
    width: float
    height: float


class Hole(BaseModel):
    diameter: float
    depth: float
    location: List[float] = Field(..., min_items=3, max_items=3)


class ThinWall(BaseModel):
    thickness: float
    location: List[float] = Field(..., min_items=3, max_items=3)


class CADGeometry(BaseModel):
    part_name: str
    volume: float
    surface_area: float
    bounding_box: BoundingBox
    center_of_mass: Point3D
    holes: List[Hole] = []
    thin_walls: List[ThinWall] = []
    faces: Optional[int] = None


class DFMAnalysisRequest(BaseModel):
    cad_geometry: CADGeometry
    target_process: ProcessType
    material: MaterialType
    production_volume: int = 1000
    advanced_analysis: bool = True
    include_cost_analysis: bool = True
    include_alternative_processes: bool = True
    include_optimization_suggestions: bool = True


class ManufacturingIssue(BaseModel):
    title: str
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    recommendation: str
    cost_impact: Optional[float] = None
    position: Optional[Point3D] = None


class CostAnalysis(BaseModel):
    cost_per_part: float
    material_cost: float
    labor_cost: float
    tooling_cost: float
    setup_cost: Optional[float] = None
    finishing_cost: Optional[float] = None
    overhead_cost: Optional[float] = None


class ProcessSuitability(BaseModel):
    process: ProcessType
    suitability_score: float
    manufacturability: Literal["poor", "fair", "good", "excellent"]
    estimated_unit_cost: float
    estimated_lead_time: int
    advantages: List[str]
    limitations: List[str]


class DFMAnalysisResponse(BaseModel):
    analysis_id: str
    overall_manufacturability_score: float
    overall_rating: Literal["poor", "fair", "good", "excellent"]
    primary_process: ProcessSuitability
    critical_issues: List[ManufacturingIssue] = []
    manufacturing_issues: List[ManufacturingIssue] = []
    cost_analysis: Optional[CostAnalysis] = None
    alternative_processes: Optional[List[ProcessSuitability]] = None
    expert_recommendations: List[str] = []


class QuickDFMRequest(BaseModel):
    cad_geometry: CADGeometry
    target_process: ProcessType


class QuickDFMResponse(BaseModel):
    analysis_id: str
    manufacturability_score: float
    major_issues: List[str]
    estimated_cost_range: Dict[str, float]


class ProcessComparisonRequest(BaseModel):
    cad_geometry: CADGeometry
    processes: List[ProcessType]
    material: MaterialType
    production_volume: int = 1000


class ProcessComparisonResponse(BaseModel):
    analysis_id: str
    process_comparisons: List[ProcessSuitability]
    recommended_process: ProcessType
    cost_comparison: Dict[str, float]
    lead_time_comparison: Dict[str, int]
