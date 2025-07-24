"""
Unit and Integration Tests for Enhanced API Converter and Advanced Integration

This module contains comprehensive tests for the Enhanced API Converter
and Advanced Integration Manager components of the CAD Geometry Extraction System.
"""

import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime
from pathlib import Path

from ..models.dfm_models import (
    CADGeometry, 
    DFMAnalysisRequest, 
    DFMAnalysisResponse,
    ProcessType,
    MaterialType,
    BoundingBox,
    Point3D,
    Hole,
    ThinWall,
    ManufacturingIssue,
    ProcessSuitability
)
from ..services.enhanced_api_converter import EnhancedAPIFormatConverter
from ..services.advanced_integration import (
    AdvancedIntegrationManager,
    process_dfm_request,
    process_legacy_cad_request,
    process_batch_requests
)


class TestEnhancedAPIConverter(unittest.TestCase):
    """Test cases for the EnhancedAPIConverter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.converter = EnhancedAPIFormatConverter()
        
        # Sample legacy data
        self.legacy_data = {
            "part_name": "test_part",
            "dimensions": {
                "length": 100.0,
                "width": 50.0,
                "height": 25.0
            },
            "volume": 125000.0,
            "surface_area": 15000.0,
            "center_of_mass": {
                "x": 50.0,
                "y": 25.0,
                "z": 12.5
            },
            "features": {
                "holes": [
                    {
                        "diameter": 10.0,
                        "depth": 25.0,
                        "position": {"x": 25.0, "y": 25.0, "z": 0.0}
                    }
                ],
                "thin_walls": [
                    {
                        "thickness": 2.0,
                        "area": 500.0,
                        "position": {"x": 50.0, "y": 0.0, "z": 12.5}
                    }
                ]
            }
        }
        
        # Sample CADGeometry
        self.cad_geometry = CADGeometry(
            part_name="test_part",
            volume=125000.0,
            surface_area=15000.0,
            bounding_box=BoundingBox(length=100.0, width=50.0, height=25.0),
            center_of_mass=Point3D(x=50.0, y=25.0, z=12.5),
            holes=[
                Hole(
                    diameter=10.0,
                    depth=25.0,
                    position=Point3D(x=25.0, y=25.0, z=0.0)
                )
            ],
            thin_walls=[
                ThinWall(
                    thickness=2.0,
                    area=500.0,
                    position=Point3D(x=50.0, y=0.0, z=12.5)
                )
            ],
            faces=24
        )
    
    def test_legacy_to_enhanced_format(self):
        """Test conversion from legacy to enhanced format"""
        result = self.converter.legacy_to_enhanced_format(self.legacy_data)
        
        self.assertEqual(result.part_name, "test_part")
        self.assertEqual(result.volume, 125000.0)
        self.assertEqual(result.surface_area, 15000.0)
        self.assertEqual(result.bounding_box.length, 100.0)
        self.assertEqual(result.bounding_box.width, 50.0)
        self.assertEqual(result.bounding_box.height, 25.0)
        self.assertEqual(result.center_of_mass.x, 50.0)
        self.assertEqual(result.center_of_mass.y, 25.0)
        self.assertEqual(result.center_of_mass.z, 12.5)
        
        # Check features
        self.assertEqual(len(result.holes), 1)
        self.assertEqual(result.holes[0].diameter, 10.0)
        self.assertEqual(result.holes[0].depth, 25.0)
        self.assertEqual(result.holes[0].position.x, 25.0)
        
        self.assertEqual(len(result.thin_walls), 1)
        self.assertEqual(result.thin_walls[0].thickness, 2.0)
        self.assertEqual(result.thin_walls[0].area, 500.0)
        self.assertEqual(result.thin_walls[0].position.x, 50.0)
    
    def test_enhanced_to_legacy_format(self):
        """Test conversion from enhanced to legacy format"""
        result = self.converter.enhanced_to_legacy_format(self.cad_geometry)
        
        self.assertEqual(result["part_name"], "test_part")
        self.assertEqual(result["volume"], 125000.0)
        self.assertEqual(result["surface_area"], 15000.0)
        self.assertEqual(result["dimensions"]["length"], 100.0)
        self.assertEqual(result["dimensions"]["width"], 50.0)
        self.assertEqual(result["dimensions"]["height"], 25.0)
        self.assertEqual(result["center_of_mass"]["x"], 50.0)
        self.assertEqual(result["center_of_mass"]["y"], 25.0)
        self.assertEqual(result["center_of_mass"]["z"], 12.5)
        
        # Check features
        self.assertEqual(len(result["features"]["holes"]), 1)
        self.assertEqual(result["features"]["holes"][0]["diameter"], 10.0)
        self.assertEqual(result["features"]["holes"][0]["depth"], 25.0)
        self.assertEqual(result["features"]["holes"][0]["position"]["x"], 25.0)
        
        self.assertEqual(len(result["features"]["thin_walls"]), 1)
        self.assertEqual(result["features"]["thin_walls"][0]["thickness"], 2.0)
        self.assertEqual(result["features"]["thin_walls"][0]["area"], 500.0)
        self.assertEqual(result["features"]["thin_walls"][0]["position"]["x"], 50.0)
    
    def test_analyze_complexity(self):
        """Test complexity analysis"""
        result = self.converter.analyze_complexity(self.cad_geometry)
        
        # Check result structure
        self.assertIn("complexity_score", result)
        self.assertIn("complexity_rating", result)
        self.assertIn("complexity_factors", result)
        self.assertIn("manufacturing_implications", result)
        
        # Check complexity factors
        factors = result["complexity_factors"]
        self.assertIn("surface_volume_ratio", factors)
        self.assertIn("feature_density", factors)
        self.assertIn("aspect_ratio", factors)
        self.assertIn("feature_count", factors)
        
        # Check score range
        self.assertGreaterEqual(result["complexity_score"], 0.0)
        self.assertLessEqual(result["complexity_score"], 100.0)
        
        # Check rating is valid
        self.assertIn(result["complexity_rating"], 
                     ["Very Low", "Low", "Medium", "High", "Very High"])
    
    def test_assess_manufacturability(self):
        """Test manufacturability assessment"""
        # Test for injection molding
        result_im = self.converter.assess_manufacturability(
            self.cad_geometry, 
            ProcessType.INJECTION_MOLDING
        )
        
        # Check result structure
        self.assertIn("manufacturability_score", result_im)
        self.assertIn("manufacturability_rating", result_im)
        self.assertIn("issues", result_im)
        self.assertIn("warnings", result_im)
        self.assertIn("recommendations", result_im)
        
        # Check score range
        self.assertGreaterEqual(result_im["manufacturability_score"], 0.0)
        self.assertLessEqual(result_im["manufacturability_score"], 100.0)
        
        # Check rating is valid
        self.assertIn(result_im["manufacturability_rating"], 
                     ["poor", "fair", "good", "excellent"])
        
        # Test for CNC milling
        result_cnc = self.converter.assess_manufacturability(
            self.cad_geometry, 
            ProcessType.CNC_MILLING
        )
        
        # Check result structure
        self.assertIn("manufacturability_score", result_cnc)
        self.assertIn("manufacturability_rating", result_cnc)
    
    def test_estimate_machining_time(self):
        """Test machining time estimation"""
        result = self.converter.estimate_machining_time(
            self.cad_geometry,
            MaterialType.ALUMINUM
        )
        
        # Check result structure
        self.assertIn("total_time_minutes", result)
        self.assertIn("setup_time_minutes", result)
        self.assertIn("rough_machining_minutes", result)
        self.assertIn("finish_machining_minutes", result)
        self.assertIn("hole_operations_minutes", result)
        
        # Check times are positive
        self.assertGreater(result["total_time_minutes"], 0.0)
        self.assertGreater(result["setup_time_minutes"], 0.0)
        
        # Check total time is sum of components
        expected_total = (
            result["setup_time_minutes"] +
            result["rough_machining_minutes"] +
            result["finish_machining_minutes"] +
            result["hole_operations_minutes"]
        )
        self.assertAlmostEqual(result["total_time_minutes"], expected_total, places=1)
    
    def test_recommend_processes(self):
        """Test process recommendation"""
        result = self.converter.recommend_processes(
            self.cad_geometry,
            MaterialType.ALUMINUM,
            100
        )
        
        # Check we have recommendations
        self.assertGreater(len(result), 0)
        
        # Check first recommendation structure
        first_rec = result[0]
        self.assertIsInstance(first_rec, ProcessSuitability)
        self.assertIn(first_rec.process, list(ProcessType))
        self.assertGreaterEqual(first_rec.suitability_score, 0.0)
        self.assertLessEqual(first_rec.suitability_score, 100.0)
        self.assertIn(first_rec.manufacturability, ["poor", "fair", "good", "excellent"])
        self.assertGreater(first_rec.estimated_unit_cost, 0.0)
        self.assertGreater(first_rec.estimated_lead_time, 0)
        self.assertGreater(len(first_rec.advantages), 0)
        self.assertGreater(len(first_rec.limitations), 0)
        
        # Check recommendations are sorted by suitability score
        for i in range(len(result) - 1):
            self.assertGreaterEqual(
                result[i].suitability_score,
                result[i + 1].suitability_score
            )
    
    def test_extract_production_cad_data(self):
        """Test production CAD data extraction"""
        result = self.converter.extract_production_cad_data(
            self.cad_geometry,
            MaterialType.ALUMINUM,
            100
        )
        
        # Check result structure
        self.assertIn("analysis_id", result)
        self.assertIn("part_info", result)
        self.assertIn("complexity_analysis", result)
        self.assertIn("manufacturability", result)
        self.assertIn("machining_estimates", result)
        self.assertIn("process_recommendations", result)
        self.assertIn("features", result)
        self.assertIn("timestamp", result)
        
        # Check part info
        part_info = result["part_info"]
        self.assertEqual(part_info["name"], "test_part")
        self.assertEqual(part_info["volume_cm3"], 125000.0)
        self.assertEqual(part_info["material"], "ALUMINUM")
        self.assertEqual(part_info["production_volume"], 100)
        
        # Check process recommendations
        self.assertGreaterEqual(len(result["process_recommendations"]), 1)
        self.assertLessEqual(len(result["process_recommendations"]), 3)  # Max 3
        
        # Check recommended approach if present
        if "recommended_approach" in result:
            approach = result["recommended_approach"]
            self.assertIn("process", approach)
            self.assertIn("estimated_unit_cost", approach)
            self.assertIn("estimated_lead_time_days", approach)
            self.assertIn("key_considerations", approach)


class TestAdvancedIntegrationManager(unittest.TestCase):
    """Test cases for the AdvancedIntegrationManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary cache directory
        self.temp_cache_dir = tempfile.TemporaryDirectory()
        
        # Mock the cache directory path
        patcher = patch("app.services.advanced_integration.CACHE_DIR", Path(self.temp_cache_dir.name))
        patcher.start()
        self.addCleanup(patcher.stop)
        
        self.manager = AdvancedIntegrationManager()
        
        # Sample CADGeometry
        self.cad_geometry = CADGeometry(
            part_name="test_part",
            volume=125000.0,
            surface_area=15000.0,
            bounding_box=BoundingBox(length=100.0, width=50.0, height=25.0),
            center_of_mass=Point3D(x=50.0, y=25.0, z=12.5),
            holes=[
                Hole(
                    diameter=10.0,
                    depth=25.0,
                    position=Point3D(x=25.0, y=25.0, z=0.0)
                )
            ],
            thin_walls=[
                ThinWall(
                    thickness=2.0,
                    area=500.0,
                    position=Point3D(x=50.0, y=0.0, z=12.5)
                )
            ],
            faces=24
        )
        
        # Sample request
        self.request = DFMAnalysisRequest(
            cad_data=self.cad_geometry,
            material=MaterialType.ALUMINUM,
            production_volume=100,
            processes=[ProcessType.CNC_MILLING, ProcessType.INJECTION_MOLDING]
        )
        
        # Sample legacy data
        self.legacy_data = {
            "part_name": "test_part",
            "dimensions": {
                "length": 100.0,
                "width": 50.0,
                "height": 25.0
            },
            "volume": 125000.0,
            "surface_area": 15000.0,
            "center_of_mass": {
                "x": 50.0,
                "y": 25.0,
                "z": 12.5
            },
            "features": {
                "holes": [
                    {
                        "diameter": 10.0,
                        "depth": 25.0,
                        "position": {"x": 25.0, "y": 25.0, "z": 0.0}
                    }
                ],
                "thin_walls": [
                    {
                        "thickness": 2.0,
                        "area": 500.0,
                        "position": {"x": 50.0, "y": 0.0, "z": 12.5}
                    }
                ]
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.temp_cache_dir.cleanup()
    
    @patch("app.services.dfm_engine.DFMEngine.analyze")
    def test_process_analysis_request(self, mock_analyze):
        """Test processing a single analysis request"""
        # Mock DFMEngine.analyze to return a response
        mock_response = DFMAnalysisResponse(
            cad_data=self.cad_geometry,
            manufacturability_score=85.0,
            issues=[],
            process_suitability=[
                ProcessSuitability(
                    process=ProcessType.CNC_MILLING,
                    suitability_score=85.0,
                    manufacturability="good",
                    estimated_unit_cost=150.0,
                    estimated_lead_time=7,
                    advantages=["Good for prototypes"],
                    limitations=["Higher cost"]
                )
            ],
            cost_analysis={"total_cost": 150.0},
            metadata={}
        )
        mock_analyze.return_value = mock_response
        
        # Process request
        result = self.manager.process_analysis_request(self.request)
        
        # Check mock was called
        mock_analyze.assert_called_once_with(self.request)
        
        # Check result
        self.assertEqual(result.manufacturability_score, 85.0)
        self.assertEqual(len(result.process_suitability), 1)
        self.assertEqual(result.process_suitability[0].process, ProcessType.CNC_MILLING)
        
        # Check metadata was enhanced
        self.assertIn("complexity_score", result.metadata)
        self.assertIn("complexity_rating", result.metadata)
    
    @patch("app.services.dfm_engine.DFMEngine.analyze")
    def test_cache_functionality(self, mock_analyze):
        """Test caching functionality"""
        # Mock DFMEngine.analyze to return a response
        mock_response = DFMAnalysisResponse(
            cad_data=self.cad_geometry,
            manufacturability_score=85.0,
            issues=[],
            process_suitability=[],
            cost_analysis={},
            metadata={}
        )
        mock_analyze.return_value = mock_response
        
        # Process request first time
        result1 = self.manager.process_analysis_request(self.request)
        
        # Process same request second time
        result2 = self.manager.process_analysis_request(self.request)
        
        # Check mock was called only once
        mock_analyze.assert_called_once()
        
        # Check both results are equal
        self.assertEqual(result1.manufacturability_score, result2.manufacturability_score)
    
    @patch("app.services.dfm_engine.DFMEngine.analyze")
    def test_process_batch_requests(self, mock_analyze):
        """Test batch processing"""
        # Mock DFMEngine.analyze to return a response
        mock_response = DFMAnalysisResponse(
            cad_data=self.cad_geometry,
            manufacturability_score=85.0,
            issues=[],
            process_suitability=[],
            cost_analysis={},
            metadata={}
        )
        mock_analyze.return_value = mock_response
        
        # Create batch of requests
        requests = [self.request] * 3
        
        # Process batch
        results = self.manager.process_batch_requests(requests)
        
        # Check results
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertEqual(result.manufacturability_score, 85.0)
    
    @patch("app.services.enhanced_api_converter.EnhancedAPIFormatConverter.legacy_to_enhanced_format")
    @patch("app.services.advanced_integration.AdvancedIntegrationManager.process_analysis_request")
    def test_process_legacy_request(self, mock_process, mock_convert):
        """Test processing a legacy request"""
        # Mock converter to return CADGeometry
        mock_convert.return_value = self.cad_geometry
        
        # Mock process_analysis_request to return a response
        mock_response = DFMAnalysisResponse(
            cad_data=self.cad_geometry,
            manufacturability_score=85.0,
            issues=[],
            process_suitability=[
                ProcessSuitability(
                    process=ProcessType.CNC_MILLING,
                    suitability_score=85.0,
                    manufacturability="good",
                    estimated_unit_cost=150.0,
                    estimated_lead_time=7,
                    advantages=["Good for prototypes"],
                    limitations=["Higher cost"]
                )
            ],
            cost_analysis={},
            metadata={}
        )
        mock_process.return_value = mock_response
        
        # Process legacy request
        result = self.manager.process_legacy_request(
            self.legacy_data,
            "ALUMINUM",
            100
        )
        
        # Check result
        self.assertEqual(result["part_name"], "test_part")
        self.assertEqual(result["manufacturability_score"], 85.0)
        self.assertIn("recommended_processes", result)
        self.assertGreaterEqual(len(result["recommended_processes"]), 1)
    
    def test_error_handling(self):
        """Test error handling"""
        # Create a request that will cause an error
        bad_request = DFMAnalysisRequest(
            cad_data=None,  # This will cause an error
            material=MaterialType.ALUMINUM,
            production_volume=100,
            processes=[ProcessType.CNC_MILLING]
        )
        
        # Process request
        result = self.manager.process_analysis_request(bad_request)
        
        # Check result is an error response
        self.assertGreaterEqual(len(result.issues), 1)
        self.assertEqual(result.issues[0].severity, "critical")
        self.assertIn("error", result.metadata)
    
    def test_performance_metrics(self):
        """Test performance metrics"""
        # Get initial metrics
        initial_metrics = self.manager.get_performance_report()
        
        # Process a request with a mock
        with patch("app.services.dfm_engine.DFMEngine.analyze") as mock_analyze:
            mock_analyze.return_value = DFMAnalysisResponse(
                cad_data=self.cad_geometry,
                manufacturability_score=85.0,
                issues=[],
                process_suitability=[],
                cost_analysis={},
                metadata={}
            )
            
            self.manager.process_analysis_request(self.request)
        
        # Get updated metrics
        updated_metrics = self.manager.get_performance_report()
        
        # Check metrics were updated
        self.assertEqual(updated_metrics["metrics"]["total_requests"], 
                        initial_metrics["metrics"]["total_requests"] + 1)
        self.assertEqual(updated_metrics["metrics"]["successful_requests"], 
                        initial_metrics["metrics"]["successful_requests"] + 1)


class TestAPIIntegrationFunctions(unittest.TestCase):
    """Test cases for API integration functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Sample CADGeometry
        self.cad_geometry = CADGeometry(
            part_name="test_part",
            volume=125000.0,
            surface_area=15000.0,
            bounding_box=BoundingBox(length=100.0, width=50.0, height=25.0),
            center_of_mass=Point3D(x=50.0, y=25.0, z=12.5),
            holes=[],
            thin_walls=[]
        )
        
        # Sample request
        self.request = DFMAnalysisRequest(
            cad_data=self.cad_geometry,
            material=MaterialType.ALUMINUM,
            production_volume=100,
            processes=[ProcessType.CNC_MILLING]
        )
        
        # Sample legacy data
        self.legacy_data = {
            "part_name": "test_part",
            "dimensions": {
                "length": 100.0,
                "width": 50.0,
                "height": 25.0
            },
            "volume": 125000.0,
            "surface_area": 15000.0,
            "center_of_mass": {
                "x": 50.0,
                "y": 25.0,
                "z": 12.5
            },
            "features": {
                "holes": [],
                "thin_walls": []
            }
        }
    
    @patch("app.services.advanced_integration.integration_manager.process_analysis_request")
    def test_process_dfm_request(self, mock_process):
        """Test process_dfm_request function"""
        # Mock manager.process_analysis_request
        mock_response = DFMAnalysisResponse(
            cad_data=self.cad_geometry,
            manufacturability_score=85.0,
            issues=[],
            process_suitability=[],
            cost_analysis={},
            metadata={}
        )
        mock_process.return_value = mock_response
        
        # Call function
        result = process_dfm_request(self.request)
        
        # Check mock was called
        mock_process.assert_called_once_with(self.request)
        
        # Check result
        self.assertEqual(result.manufacturability_score, 85.0)
    
    @patch("app.services.advanced_integration.integration_manager.process_legacy_request")
    def test_process_legacy_cad_request(self, mock_process):
        """Test process_legacy_cad_request function"""
        # Mock manager.process_legacy_request
        mock_response = {
            "part_name": "test_part",
            "manufacturability_score": 85.0
        }
        mock_process.return_value = mock_response
        
        # Call function
        result = process_legacy_cad_request(
            self.legacy_data,
            "ALUMINUM",
            100
        )
        
        # Check mock was called
        mock_process.assert_called_once_with(
            self.legacy_data,
            "ALUMINUM",
            100
        )
        
        # Check result
        self.assertEqual(result["manufacturability_score"], 85.0)
    
    @patch("app.services.advanced_integration.integration_manager.process_batch_requests")
    def test_process_batch_requests(self, mock_process):
        """Test process_batch_requests function"""
        # Mock manager.process_batch_requests
        mock_response = [
            DFMAnalysisResponse(
                cad_data=self.cad_geometry,
                manufacturability_score=85.0,
                issues=[],
                process_suitability=[],
                cost_analysis={},
                metadata={}
            )
        ]
        mock_process.return_value = mock_response
        
        # Call function
        result = process_batch_requests([self.request])
        
        # Check mock was called
        mock_process.assert_called_once_with([self.request])
        
        # Check result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].manufacturability_score, 85.0)


if __name__ == "__main__":
    unittest.main()
