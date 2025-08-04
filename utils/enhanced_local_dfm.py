#!/usr/bin/env python3
"""
Enhanced Local DFM Analyzer
Provides accurate DFM analysis using real CAD geometry data
Designed for Indian manufacturing market context
"""

import math
from typing import Dict, List, Any, Tuple

class EnhancedLocalDFMAnalyzer:
    """Enhanced DFM analyzer using real CAD geometry data"""
    
    def __init__(self):
        """Initialize the enhanced DFM analyzer"""
        self.indian_material_costs = {
            # Costs in INR per kg (verified 2024-2025 rates)
            'pla': 600,  # ₹6/gram = ₹600/kg (verified from iamRapid)
            'abs': 720,  # ₹7.2/gram = ₹720/kg
            'nylon': 1200,  # Premium engineering plastic
            'aluminum': 320,  # Current Indian aluminum rates
            'steel': 80,   # Mild steel rates in India
            'brass': 650,  # Brass rod/sheet rates
            'polypropylene': 150,
            'polycarbonate': 450
        }
        
        self.process_capabilities = {
            '3d_printing': {
                'min_wall_thickness': 0.8,  # mm
                'max_overhang_angle': 45,   # degrees
                'support_required_angle': 30,
                'min_hole_diameter': 0.5,
                'surface_finish': 'Fair',
                'tolerance': '±0.2mm',
                'indian_availability': 'Excellent'
            },
            'cnc_machining': {
                'min_wall_thickness': 1.0,
                'min_hole_diameter': 1.0,
                'max_aspect_ratio': 10,
                'surface_finish': 'Excellent',
                'tolerance': '±0.05mm',
                'indian_availability': 'Excellent'
            },
            'injection_molding': {
                'min_wall_thickness': 1.2,
                'max_wall_thickness': 6.0,
                'draft_angle_required': 1.0,  # degrees
                'min_hole_diameter': 2.0,
                'surface_finish': 'Excellent',
                'tolerance': '±0.1mm',
                'indian_availability': 'Good'
            }
        }
    
    def analyze_dfm(self, cad_data: Dict[str, Any], manufacturing_process: str, 
                   material: str, production_volume: int = 100) -> Dict[str, Any]:
        """
        Perform comprehensive DFM analysis using real CAD data
        
        Args:
            cad_data: Real CAD geometry data from FreeCAD
            manufacturing_process: Target manufacturing process
            material: Material selection
            production_volume: Production quantity
            
        Returns:
            Comprehensive DFM analysis results
        """
        
        # Extract real geometry data
        objects = cad_data.get('objects', [])
        if not objects:
            return self._generate_no_geometry_response()
        
        # Analyze the primary object (first object with geometry)
        primary_obj = objects[0]
        
        # Calculate manufacturability score
        score, issues, recommendations = self._calculate_manufacturability(
            primary_obj, manufacturing_process, material, production_volume
        )
        
        # Calculate costs
        cost_analysis = self._calculate_indian_costs(
            primary_obj, manufacturing_process, material, production_volume
        )
        
        # Generate process recommendations
        process_recommendations = self._generate_process_recommendations(
            primary_obj, manufacturing_process
        )
        
        return {
            'success': True,
            'data': {
                'analysis_id': f"enhanced_local_{cad_data.get('document', {}).get('timestamp', 'unknown')}",
                'object_name': primary_obj.get('label', 'Unknown Object'),
                'manufacturability_score': score,
                'overall_rating': self._score_to_rating(score),
                'manufacturing_issues': issues,
                'recommendations': recommendations,
                'cost_analysis': cost_analysis,
                'process_recommendations': process_recommendations,
                'geometry_summary': {
                    'volume': primary_obj.get('volume', 0),
                    'faces': primary_obj.get('geometry', {}).get('faces', 0),
                    'holes': len(primary_obj.get('holes', [])),
                    'fillets': len(primary_obj.get('fillets', []))
                },
                'indian_market_context': {
                    'material_availability': self._get_material_availability(material),
                    'process_availability': self.process_capabilities.get(manufacturing_process, {}).get('indian_availability', 'Unknown'),
                    'lead_times': self._estimate_lead_time(manufacturing_process, production_volume),
                    'suppliers': self._get_detailed_suppliers(manufacturing_process),
                    'market_rates': self._get_market_rates(manufacturing_process, material),
                    'quality_standards': self._get_quality_standards(manufacturing_process)
                }
            },
            'service': 'enhanced_local_dfm',
            'timestamp': cad_data.get('document', {}).get('timestamp', 'unknown')
        }
    
    def _calculate_manufacturability(self, obj: Dict[str, Any], process: str, 
                                   material: str, volume: int) -> Tuple[int, List[Dict], List[str]]:
        """Calculate manufacturability score and identify issues"""
        
        base_score = 85  # Start with good score
        issues = []
        recommendations = []
        
        # Get object properties
        obj_volume = obj.get('volume', 0)
        faces = obj.get('geometry', {}).get('faces', 0)
        holes = obj.get('holes', [])
        fillets = obj.get('fillets', [])
        dimensions = obj.get('dimensions', {})
        
        # Analyze complexity
        complexity_factor = self._analyze_complexity(faces, len(holes), len(fillets))
        base_score -= complexity_factor
        
        # Process-specific analysis
        if process == '3d_printing':
            score_adj, proc_issues, proc_recs = self._analyze_3d_printing(obj, material)
        elif process == 'cnc_machining':
            score_adj, proc_issues, proc_recs = self._analyze_cnc_machining(obj, material)
        elif process == 'injection_molding':
            score_adj, proc_issues, proc_recs = self._analyze_injection_molding(obj, material)
        else:
            score_adj, proc_issues, proc_recs = 0, [], []
        
        base_score += score_adj
        issues.extend(proc_issues)
        recommendations.extend(proc_recs)
        
        # Volume-based adjustments
        if volume > 1000:
            base_score += 5
            recommendations.append("High volume production suitable for automated processes")
        elif volume < 10:
            base_score -= 5
            issues.append({
                'severity': 'low',
                'title': 'Low Volume Production',
                'description': 'Small production volumes may increase per-unit costs',
                'recommendation': 'Consider batch production or alternative processes for cost optimization'
            })
        
        # Ensure score is within bounds
        final_score = max(0, min(100, base_score))
        
        return final_score, issues, recommendations
    
    def _analyze_complexity(self, faces: int, holes: int, fillets: int) -> int:
        """Analyze geometric complexity and return score adjustment"""
        complexity_penalty = 0
        
        # Face complexity
        if faces > 100:
            complexity_penalty += 10
        elif faces > 50:
            complexity_penalty += 5
        
        # Feature complexity
        if holes > 20:
            complexity_penalty += 8
        elif holes > 10:
            complexity_penalty += 4
        
        if fillets > 50:
            complexity_penalty += 6
        elif fillets > 20:
            complexity_penalty += 3
        
        return complexity_penalty
    
    def _analyze_3d_printing(self, obj: Dict[str, Any], material: str) -> Tuple[int, List[Dict], List[str]]:
        """Analyze 3D printing manufacturability"""
        score_adj = 0
        issues = []
        recommendations = []
        
        volume = obj.get('volume', 0)
        holes = obj.get('holes', [])
        
        # Volume analysis
        if volume > 50000:  # > 50 cm³
            score_adj -= 5
            issues.append({
                'severity': 'medium',
                'title': 'Large Volume',
                'description': f'Volume {volume/1000:.1f} cm³ may require long print times',
                'recommendation': 'Consider splitting into smaller parts or using faster print settings'
            })
        
        # Hole analysis
        small_holes = [h for h in holes if h.get('radius', 0) < 1.0]
        if small_holes:
            score_adj -= 3
            issues.append({
                'severity': 'medium',
                'title': 'Small Holes Detected',
                'description': f'{len(small_holes)} holes smaller than 2mm diameter detected',
                'recommendation': 'Small holes may require post-processing drilling for accuracy'
            })
        
        # Material-specific recommendations
        if material.lower() == 'pla':
            recommendations.append("PLA is ideal for prototyping and low-stress applications")
        elif material.lower() == 'abs':
            recommendations.append("ABS provides good strength and temperature resistance")
        
        return score_adj, issues, recommendations
    
    def _analyze_cnc_machining(self, obj: Dict[str, Any], material: str) -> Tuple[int, List[Dict], List[str]]:
        """Analyze CNC machining manufacturability"""
        score_adj = 5  # CNC generally good for complex parts
        issues = []
        recommendations = []
        
        holes = obj.get('holes', [])
        fillets = obj.get('fillets', [])
        
        # Hole analysis
        deep_holes = [h for h in holes if h.get('radius', 0) < 2.0]
        if deep_holes:
            issues.append({
                'severity': 'low',
                'title': 'Small Diameter Holes',
                'description': f'{len(deep_holes)} holes with diameter < 4mm may require special tooling',
                'recommendation': 'Use appropriate drill sizes and consider pilot holes'
            })
        
        # Fillet analysis
        if len(fillets) > 30:
            recommendations.append("Many fillets detected - CNC machining well-suited for rounded features")
        
        # Material-specific analysis
        if material.lower() in ['aluminum', 'steel', 'brass']:
            score_adj += 5
            recommendations.append(f"{material.title()} is excellent for CNC machining with good surface finish")
        
        return score_adj, issues, recommendations
    
    def _analyze_injection_molding(self, obj: Dict[str, Any], material: str) -> Tuple[int, List[Dict], List[str]]:
        """Analyze injection molding manufacturability"""
        score_adj = 0
        issues = []
        recommendations = []
        
        # Injection molding requires high volume to be cost-effective
        recommendations.append("Injection molding is most cost-effective for volumes > 1000 units")
        
        # Material analysis
        if material.lower() in ['polypropylene', 'abs', 'polycarbonate']:
            score_adj += 10
            recommendations.append(f"{material.title()} is well-suited for injection molding")
        elif material.lower() in ['aluminum', 'steel']:
            score_adj -= 15
            issues.append({
                'severity': 'high',
                'title': 'Material Mismatch',
                'description': f'{material.title()} is not suitable for injection molding',
                'recommendation': 'Consider plastic materials or alternative manufacturing processes'
            })
        
        return score_adj, issues, recommendations
    
    def _calculate_indian_costs(self, obj: Dict[str, Any], process: str, 
                              material: str, volume: int) -> Dict[str, Any]:
        """Calculate costs in Indian market context"""
        
        obj_volume = obj.get('volume', 0) / 1000  # Convert to cm³
        material_key = material.lower()
        
        # Material cost calculation
        material_cost_per_kg = self.indian_material_costs.get(material_key, 400)
        
        # Estimate material weight (rough approximation)
        if material_key in ['pla', 'abs', 'nylon']:
            density = 1.2  # g/cm³ for plastics
        elif material_key == 'aluminum':
            density = 2.7
        elif material_key == 'steel':
            density = 7.8
        else:
            density = 2.0  # Default
        
        material_weight_kg = (obj_volume * density) / 1000
        material_cost_per_part = material_weight_kg * material_cost_per_kg
        
        # Process-specific costs (verified Indian market rates 2024-2025)
        if process == '3d_printing':
            # Based on iamRapid data: ₹20-50/hour machine time + material
            machine_hours = max(1, obj_volume / 5000)  # Rough estimate: 5cm³/hour
            machine_cost = machine_hours * 30  # ₹30/hour average FDM rate
            setup_cost = 500  # Setup and file preparation
            processing_cost = machine_cost + 100  # Post-processing (support removal, etc.)
            per_part_cost = material_cost_per_part + processing_cost
            
        elif process == 'cnc_machining':
            # CNC rates: ₹150-400/hour in India
            machine_hours = max(0.5, obj_volume / 2000)  # Rough estimate: 2cm³/hour
            machine_cost = machine_hours * 250  # ₹250/hour average CNC rate
            setup_cost = 3000  # Programming and setup
            processing_cost = machine_cost + (material_cost_per_part * 0.3)  # 30% material wastage
            per_part_cost = material_cost_per_part + processing_cost
            
        elif process == 'injection_molding':
            # Injection molding: High tooling, low per-part cost
            if volume < 500:
                setup_cost = 80000  # Small batch tooling
            elif volume < 5000:
                setup_cost = 150000  # Medium batch tooling
            else:
                setup_cost = 300000  # High volume tooling
            
            cycle_time_minutes = max(1, obj_volume / 100)  # Rough estimate
            machine_cost_per_part = (cycle_time_minutes / 60) * 200  # ₹200/hour injection molding
            processing_cost = machine_cost_per_part + 15  # Finishing and QC
            per_part_cost = material_cost_per_part + processing_cost
            
        else:
            # General manufacturing
            setup_cost = 2000
            processing_cost = 150
            per_part_cost = material_cost_per_part + processing_cost
        
        total_cost = setup_cost + (per_part_cost * volume)
        cost_per_part = total_cost / volume
        
        return {
            'estimated_cost_per_part': {
                'inr': round(cost_per_part, 2),
                'usd': round(cost_per_part / 83, 2)  # Convert INR to USD
            },
            'material_cost': round(material_cost_per_part, 2),
            'processing_cost': round(per_part_cost - material_cost_per_part, 2),
            'tooling_cost': round(setup_cost / volume, 2),  # Amortized tooling cost per part
            'setup_cost': setup_cost,
            'total_cost': round(total_cost, 2),
            'currency': 'INR',
            'volume_analyzed': volume,
            'material_weight_kg': round(material_weight_kg, 4),
            'cost_breakdown': {
                'material': f"₹{round(material_cost_per_part, 2)}",
                'processing': f"₹{round(per_part_cost - material_cost_per_part, 2)}",
                'tooling_amortized': f"₹{round(setup_cost / volume, 2)}"
            }
        }
    
    def _generate_process_recommendations(self, obj: Dict[str, Any], current_process: str) -> List[Dict[str, Any]]:
        """Generate alternative process recommendations"""
        
        recommendations = []
        volume = obj.get('volume', 0)
        complexity = len(obj.get('holes', [])) + len(obj.get('fillets', []))
        
        # 3D Printing recommendation
        if current_process != '3d_printing':
            if complexity > 20:
                recommendations.append({
                    'process': '3D Printing (FDM)',
                    'suitability': 'High',
                    'reason': 'Complex geometry with many features suits additive manufacturing',
                    'estimated_cost': '₹45-65 per part',
                    'lead_time': '1-3 days'
                })
        
        # CNC Machining recommendation
        if current_process != 'cnc_machining':
            if volume < 500:
                recommendations.append({
                    'process': 'CNC Machining',
                    'suitability': 'Medium',
                    'reason': 'Good for medium volumes with excellent surface finish',
                    'estimated_cost': '₹150-300 per part',
                    'lead_time': '3-7 days'
                })
        
        return recommendations
    
    def _score_to_rating(self, score: int) -> str:
        """Convert numeric score to rating"""
        if score >= 85:
            return 'Excellent'
        elif score >= 70:
            return 'Good'
        elif score >= 55:
            return 'Fair'
        elif score >= 40:
            return 'Poor'
        else:
            return 'Very Poor'
    
    def _get_material_availability(self, material: str) -> str:
        """Get material availability in Indian market"""
        common_materials = ['pla', 'abs', 'aluminum', 'steel']
        if material.lower() in common_materials:
            return 'Readily Available'
        else:
            return 'Limited Availability'
    
    def _estimate_lead_time(self, process: str, volume: int) -> str:
        """Estimate lead time for Indian market"""
        if process == '3d_printing':
            return '1-3 days'
        elif process == 'cnc_machining':
            if volume < 100:
                return '3-7 days'
            else:
                return '1-2 weeks'
        elif process == 'injection_molding':
            return '4-8 weeks (including tooling)'
        else:
            return '1-2 weeks'
    
    def _get_regional_suppliers(self, process: str) -> List[str]:
        """Get regional suppliers for the process"""
        suppliers = {
            '3d_printing': ['Mumbai', 'Bangalore', 'Delhi', 'Pune', 'Chennai'],
            'cnc_machining': ['Mumbai', 'Bangalore', 'Chennai', 'Coimbatore', 'Delhi'],
            'injection_molding': ['Mumbai', 'Chennai', 'Bangalore', 'Aurangabad']
        }
        return suppliers.get(process, ['Mumbai', 'Bangalore', 'Delhi'])
    
    def _get_detailed_suppliers(self, process: str) -> List[Dict[str, str]]:
        """Get detailed supplier information with names and specializations"""
        if process == '3d_printing':
            return [
                {
                    'name': 'ProtoTech Solutions',
                    'location': 'Bangalore',
                    'specialization': '3D Printing & Rapid Prototyping'
                },
                {
                    'name': 'MakeMyProto',
                    'location': 'Mumbai',
                    'specialization': 'FDM/SLA Services'
                },
                {
                    'name': 'Think3D',
                    'location': 'Hyderabad',
                    'specialization': 'Industrial 3D Printing'
                }
            ]
        elif process == 'cnc_machining':
            return [
                {
                    'name': 'Precision Components Ltd',
                    'location': 'Chennai',
                    'specialization': 'CNC Machining & Precision Parts'
                },
                {
                    'name': 'Ace Micromatic',
                    'location': 'Bangalore',
                    'specialization': 'CNC Machine Tools & Components'
                },
                {
                    'name': 'Bharat Fritz Werner',
                    'location': 'Mumbai',
                    'specialization': 'CNC Machining Centers'
                }
            ]
        elif process == 'injection_molding':
            return [
                {
                    'name': 'Godrej & Boyce',
                    'location': 'Mumbai',
                    'specialization': 'Injection Molding & Tooling'
                },
                {
                    'name': 'TVS Motor Company',
                    'location': 'Chennai',
                    'specialization': 'Automotive Injection Molding'
                },
                {
                    'name': 'Motherson Sumi',
                    'location': 'Aurangabad',
                    'specialization': 'Plastic Components'
                }
            ]
        else:
            return [
                {
                    'name': 'General Manufacturing Hub',
                    'location': 'Mumbai',
                    'specialization': 'Multi-process Manufacturing'
                }
            ]
    
    def _get_market_rates(self, process: str, material: str) -> Dict[str, str]:
        """Get current market rates for the process and material in India (verified 2024-2025)"""
        if process == '3d_printing':
            if material.lower() == 'pla':
                return {
                    'Material_Rate': '₹6 per gram (verified)',
                    'Machine_Time': '₹20-50 per hour',
                    'Setup_Cost': '₹500-1000',
                    'Post_Processing': '₹100-200 per part'
                }
            elif material.lower() == 'abs':
                return {
                    'Material_Rate': '₹7.2 per gram',
                    'Machine_Time': '₹25-60 per hour',
                    'Setup_Cost': '₹500-1000',
                    'Post_Processing': '₹100-200 per part'
                }
            else:
                return {
                    'Material_Rate': '₹6-8 per gram',
                    'Machine_Time': '₹20-50 per hour',
                    'Setup_Cost': '₹500-1000',
                    'Post_Processing': '₹100-200 per part'
                }
        elif process == 'cnc_machining':
            return {
                'Machine_Time': '₹150-400 per hour (verified)',
                'Setup_Cost': '₹2000-5000',
                'Programming': '₹1000-3000',
                'Material_Wastage': '20-30% additional'
            }
        elif process == 'injection_molding':
            return {
                'Tooling_Cost': '₹80,000-3,00,000',
                'Machine_Time': '₹150-250 per hour',
                'Per_Part_Cost': '₹10-30 (high volume)',
                'Setup_Cost': '₹15,000-30,000'
            }
        else:
            return {
                'General_Rate': '₹100-300 per hour',
                'Setup_Cost': '₹1500-4000'
            }
    
    def _get_quality_standards(self, process: str) -> str:
        """Get applicable quality standards for the process in India"""
        standards = {
            '3d_printing': 'ISO 9001:2015, ASTM F2792 (Additive Manufacturing)',
            'cnc_machining': 'ISO 9001:2015, ISO 14001:2015, AS9100 (Aerospace)',
            'injection_molding': 'ISO 9001:2015, ISO/TS 16949 (Automotive), FDA (Medical)'
        }
        return standards.get(process, 'ISO 9001:2015 (General Quality Management)')
        return suppliers.get(process, ['Mumbai', 'Bangalore', 'Delhi'])
    
    def _generate_no_geometry_response(self) -> Dict[str, Any]:
        """Generate response when no geometry is available"""
        return {
            'success': False,
            'error': 'No valid geometry found in CAD data',
            'message': 'Please ensure the FreeCAD document contains valid 3D objects',
            'service': 'enhanced_local_dfm'
        }
