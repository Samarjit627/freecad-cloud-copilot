"""
Advanced CAD Analyzer for the FreeCAD Manufacturing Co-Pilot
Handles local analysis of FreeCAD documents
"""

import os
from datetime import datetime
import FreeCAD
import Part

# Import local modules
try:
    import cloud_client
    import config
except ImportError:
    import cloud_client
    import config

class AdvancedCADAnalyzer:
    """Advanced CAD analyzer with comprehensive manufacturing intelligence"""
    
    def __init__(self):
        self.feature_cache = {}
        self.cloud_client = cloud_client.get_client() if config.USE_CLOUD_BACKEND else None
        print("🔍 Advanced CAD Analyzer initialized")
    
    def analyze_document(self, document):
        """Comprehensive CAD analysis with manufacturing intelligence"""
        if not document:
            return self.empty_analysis()
        
        try:
            print(f"🔍 Analyzing document: {document.Name}")
            
            # Document metadata
            display_name = document.Name
            if hasattr(document, 'FileName') and document.FileName:
                display_name = os.path.splitext(os.path.basename(document.FileName))[0]
            
            analysis = {
                "document_name": display_name,
                "file_path": getattr(document, 'FileName', 'Unsaved'),
                "object_count": len(document.Objects),
                "timestamp": datetime.now().isoformat(),
                "dimensions": {},
                "manufacturing_features": {},
                "surface_area": 0,
                "volume": 0,
                "analysis_method": "advanced_production_grade"
            }
            
            # Analyze all objects
            shape_objects = []
            all_bboxes = []
            total_surface_area = 0
            total_volume = 0
            
            for obj in document.Objects:
                if hasattr(obj, 'Shape') and obj.Shape and hasattr(obj.Shape, 'BoundBox'):
                    bbox = obj.Shape.BoundBox
                    if bbox.XLength > 0.001 and bbox.YLength > 0.001 and bbox.ZLength > 0.001:
                        obj_analysis = self.analyze_object_comprehensive(obj)
                        if obj_analysis:
                            shape_objects.append(obj_analysis)
                            all_bboxes.append(bbox)
                            total_surface_area += obj_analysis.get("surface_area", 0)
                            total_volume += obj_analysis.get("volume", 0)
            
            analysis["surface_area"] = round(total_surface_area, 1)
            analysis["volume"] = round(total_volume, 1)
            
            # Comprehensive analysis
            if shape_objects:
                analysis["dimensions"] = self.calculate_overall_dimensions(shape_objects, all_bboxes)
                analysis["manufacturing_features"] = self.analyze_manufacturing_features(shape_objects)
            
            # Enhance with cloud if available
            if config.USE_CLOUD_BACKEND and self.cloud_client and self.cloud_client.connected:
                try:
                    enhanced_analysis = self.cloud_client.enhance_cad_analysis(analysis)
                    analysis = enhanced_analysis
                    analysis["analysis_method"] = "cloud_enhanced"
                except Exception as e:
                    print(f"⚠️ Cloud enhancement failed: {e}")
            
            print(f"✅ Analysis complete: {analysis['manufacturing_features']}")
            return analysis
            
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return self.error_analysis(document, str(e))
    
    def analyze_object_comprehensive(self, obj):
        """Comprehensive object analysis"""
        try:
            bbox = obj.Shape.BoundBox
            
            obj_analysis = {
                "name": obj.Name,
                "type": obj.TypeId,
                "dimensions": {
                    "length": round(bbox.XLength, 1),
                    "width": round(bbox.YLength, 1),
                    "height": round(bbox.ZLength, 1)
                },
                "features": self.detect_all_features(obj.Shape),
                "wall_thickness": self.calculate_wall_thickness(obj.Shape),
                "surface_area": 0,
                "volume": 0
            }
            
            # Surface area and volume
            if hasattr(obj.Shape, 'Area'):
                obj_analysis["surface_area"] = round(obj.Shape.Area / 100, 1)
            
            if hasattr(obj.Shape, 'Volume'):
                obj_analysis["volume"] = round(obj.Shape.Volume / 1000, 1)
            
            return obj_analysis
            
        except Exception as e:
            print(f"⚠️ Object analysis error for {obj.Name}: {e}")
            return None
    
    def detect_all_features(self, shape):
        """Comprehensive feature detection"""
        features = {
            "holes": [],
            "ribs": [],
            "fillets": [],
            "bosses": [],
            "feature_summary": {}
        }
        
        try:
            # Hole detection
            holes = self.detect_holes_advanced(shape)
            features["holes"] = holes
            
            # Rib detection
            ribs = self.detect_ribs_advanced(shape)
            features["ribs"] = ribs
            
            # Fillet detection
            fillets = self.detect_fillets_advanced(shape)
            features["fillets"] = fillets
            
            # Boss detection
            bosses = self.detect_bosses_advanced(shape)
            features["bosses"] = bosses
            
            # Feature summary
            features["feature_summary"] = {
                "total_holes": len(holes),
                "total_ribs": len(ribs),
                "total_fillets": len(fillets),
                "total_bosses": len(bosses)
            }
            
        except Exception as e:
            print(f"⚠️ Feature detection error: {e}")
        
        return features
    
    def detect_holes_advanced(self, shape):
        """Advanced hole detection"""
        holes = []
        
        try:
            for face in shape.Faces:
                if hasattr(face, 'Surface') and face.Surface.TypeId == 'Part::GeomCylinder':
                    surf = face.Surface
                    radius = surf.Radius
                    
                    if 0.5 <= radius <= 100.0:  # Reasonable hole range
                        hole_info = {
                            "center": [surf.Location.x, surf.Location.y, surf.Location.z],
                            "radius": round(radius, 3),
                            "diameter": round(radius * 2, 3),
                            "area": round(face.Area, 2),
                            "type": "through_hole" if face.Area < 2000 else "blind_hole",
                            "classification": "mounting" if 3 <= radius <= 10 else "fastener"
                        }
                        holes.append(hole_info)
                        
        except Exception as e:
            print(f"⚠️ Hole detection error: {e}")
        
        return holes
    
    def detect_ribs_advanced(self, shape):
        """Advanced rib detection"""
        ribs = []
        
        try:
            for face in shape.Faces:
                bb = face.BoundBox
                dims = [bb.XLength, bb.YLength, bb.ZLength]
                dims.sort()
                
                if len(dims) >= 3:
                    thickness, width, length = dims
                    aspect_ratio = length / thickness if thickness > 0 else 0
                    
                    if thickness < 5.0 and aspect_ratio > 3.0 and thickness > 0.1:
                        rib_info = {
                            "center": [(bb.XMin + bb.XMax) / 2, (bb.YMin + bb.YMax) / 2, (bb.ZMin + bb.ZMax) / 2],
                            "thickness": round(thickness, 2),
                            "width": round(width, 2),
                            "length": round(length, 2),
                            "aspect_ratio": round(aspect_ratio, 2),
                            "type": "structural_rib" if length > 20 else "reinforcement_rib"
                        }
                        ribs.append(rib_info)
                        
        except Exception as e:
            print(f"⚠️ Rib detection error: {e}")
        
        return ribs
    
    def detect_fillets_advanced(self, shape):
        """Advanced fillet detection"""
        fillets = []
        
        try:
            for edge in shape.Edges:
                if hasattr(edge, 'Curve') and hasattr(edge.Curve, 'Radius'):
                    if edge.Curve.TypeId == 'Part::GeomCircle':
                        radius = edge.Curve.Radius
                        if 0.1 <= radius <= 50.0:
                            fillet_info = {
                                "center": [edge.Curve.Center.x, edge.Curve.Center.y, edge.Curve.Center.z],
                                "radius": round(radius, 3),
                                "length": round(edge.Length, 2),
                                "type": "internal_fillet" if radius < 2.0 else "external_fillet"
                            }
                            fillets.append(fillet_info)
                            
        except Exception as e:
            print(f"⚠️ Fillet detection error: {e}")
        
        return fillets
    
    def detect_bosses_advanced(self, shape):
        """Advanced boss detection"""
        bosses = []
        
        try:
            for face in shape.Faces:
                if hasattr(face, 'Surface') and face.Surface.TypeId == 'Part::GeomCylinder':
                    surf = face.Surface
                    radius = surf.Radius
                    
                    if 2.0 <= radius <= 50.0 and face.Area > 1000:
                        boss_info = {
                            "center": [surf.Location.x, surf.Location.y, surf.Location.z],
                            "radius": round(radius, 3),
                            "diameter": round(radius * 2, 3),
                            "type": "mounting_boss" if radius > 5 else "guide_boss"
                        }
                        bosses.append(boss_info)
                        
        except Exception as e:
            print(f"⚠️ Boss detection error: {e}")
        
        return bosses
    
    def calculate_wall_thickness(self, shape):
        """Calculate wall thickness"""
        try:
            bbox = shape.BoundBox
            dims = [bbox.XLength, bbox.YLength, bbox.ZLength]
            dims.sort()
            
            smallest, middle, largest = dims
            
            if smallest < middle * 0.1:
                return round(smallest * 0.95, 2)
            elif smallest < middle * 0.3:
                return round(smallest * 0.8, 2)
            elif smallest < middle * 0.6:
                return round(smallest * 0.7, 2)
            else:
                return round(smallest * 0.15, 2)
                
        except Exception as e:
            print(f"⚠️ Wall thickness calculation error: {e}")
            return 2.0
    
    def calculate_overall_dimensions(self, shape_objects, all_bboxes):
        """Calculate overall dimensions"""
        if len(shape_objects) == 1:
            obj = shape_objects[0]
            dims = obj["dimensions"].copy()
            dims["thickness"] = obj.get("wall_thickness", 0)
            return dims
        
        elif len(shape_objects) > 1:
            try:
                min_x = min(bbox.XMin for bbox in all_bboxes)
                max_x = max(bbox.XMax for bbox in all_bboxes)
                min_y = min(bbox.YMin for bbox in all_bboxes)
                max_y = max(bbox.YMax for bbox in all_bboxes)
                min_z = min(bbox.ZMin for bbox in all_bboxes)
                max_z = max(bbox.ZMax for bbox in all_bboxes)
                
                dims = {
                    "length": round(max_x - min_x, 1),
                    "width": round(max_y - min_y, 1),
                    "height": round(max_z - min_z, 1)
                }
                
                # Average thickness
                all_thicknesses = [obj.get("wall_thickness", 0) for obj in shape_objects if obj.get("wall_thickness", 0) > 0]
                dims["thickness"] = round(sum(all_thicknesses) / len(all_thicknesses), 2) if all_thicknesses else 0
                
                return dims
                
            except Exception as e:
                print(f"⚠️ Overall dimensions calculation error: {e}")
                return {"length": 0, "width": 0, "height": 0, "thickness": 0}
        
        return {"length": 0, "width": 0, "height": 0, "thickness": 0}
    
    def analyze_manufacturing_features(self, shape_objects):
        """Analyze manufacturing features"""
        features = {
            "holes": 0,
            "ribs": 0,
            "fillets": 0,
            "bosses": 0,
            "complexity_rating": "Medium",
            "moldability_score": 8.0,
            "manufacturability_index": 85,
            "tooling_complexity": "Medium"
        }
        
        try:
            # Aggregate all features
            for obj in shape_objects:
                obj_features = obj.get("features", {})
                
                if "feature_summary" in obj_features:
                    summary = obj_features["feature_summary"]
                    features["holes"] += summary.get("total_holes", 0)
                    features["ribs"] += summary.get("total_ribs", 0)
                    features["fillets"] += summary.get("total_fillets", 0)
                    features["bosses"] += summary.get("total_bosses", 0)
            
            # Calculate complexity
            total_features = features["holes"] + features["ribs"] + features["bosses"]
            
            if total_features > 15:
                features["complexity_rating"] = "Very High"
                features["moldability_score"] = 6.0
                features["manufacturability_index"] = 60
                features["tooling_complexity"] = "Very High"
            elif total_features > 10:
                features["complexity_rating"] = "High"
                features["moldability_score"] = 7.0
                features["manufacturability_index"] = 70
                features["tooling_complexity"] = "High"
            elif total_features > 5:
                features["complexity_rating"] = "Medium"
                features["moldability_score"] = 8.0
                features["manufacturability_index"] = 85
                features["tooling_complexity"] = "Medium"
            else:
                features["complexity_rating"] = "Low"
                features["moldability_score"] = 9.0
                features["manufacturability_index"] = 95
                features["tooling_complexity"] = "Low"
            
        except Exception as e:
            print(f"⚠️ Manufacturing features analysis error: {e}")
        
        return features
    
    def empty_analysis(self):
        """Return empty analysis structure"""
        return {
            "document_name": "No Document",
            "object_count": 0,
            "timestamp": datetime.now().isoformat(),
            "dimensions": {"length": 0, "width": 0, "height": 0, "thickness": 0},
            "manufacturing_features": {"holes": 0, "ribs": 0, "complexity_rating": "None"},
            "surface_area": 0,
            "volume": 0,
            "error": "No document provided"
        }
    
    def error_analysis(self, document, error_msg):
        """Return error analysis structure"""
        return {
            "document_name": document.Name if document else "Unknown",
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "dimensions": {"length": 0, "width": 0, "height": 0, "thickness": 0},
            "manufacturing_features": {"holes": 0, "ribs": 0, "complexity_rating": "Error"},
            "surface_area": 0,
            "volume": 0
        }
