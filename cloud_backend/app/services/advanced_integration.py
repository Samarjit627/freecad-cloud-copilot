"""
Advanced Integration Functions for CAD Geometry Extraction System

This module provides advanced integration functions that connect the enhanced API converter
with the existing DFM engine and API router. It includes functions for:
1. Parallel processing of CAD analysis requests
2. Caching of analysis results
3. Batch processing capabilities
4. Advanced error handling and recovery
5. Performance monitoring and optimization
"""

import logging
import time
import json
import hashlib
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from functools import lru_cache
from pathlib import Path
import traceback

from ..models.dfm_models import (
    CADGeometry, 
    DFMAnalysisRequest, 
    DFMAnalysisResponse,
    ProcessType,
    MaterialType,
    ManufacturingIssue,
    ProcessSuitability
)
from .dfm_engine import DFMEngine
from .enhanced_api_converter import EnhancedAPIFormatConverter

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MAX_WORKERS = 4
CACHE_EXPIRY_HOURS = 24
CACHE_DIR = Path("/tmp/cad_analysis_cache")
PERFORMANCE_LOG_PATH = Path("/tmp/cad_analysis_performance.log")

# Ensure cache directory exists
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class AdvancedIntegrationManager:
    """
    Advanced Integration Manager for CAD Geometry Extraction System
    
    Provides advanced integration capabilities including:
    - Parallel processing of analysis requests
    - Result caching
    - Batch processing
    - Error handling and recovery
    - Performance monitoring
    """
    
    def __init__(self):
        """Initialize the Advanced Integration Manager"""
        self.dfm_engine = DFMEngine()
        self.api_converter = EnhancedAPIFormatConverter()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
            "average_processing_time": 0.0,
            "peak_processing_time": 0.0
        }
        logger.info("Advanced Integration Manager initialized")
    
    def process_analysis_request(self, request: DFMAnalysisRequest) -> DFMAnalysisResponse:
        """
        Process a single DFM analysis request with advanced error handling
        
        Args:
            request: DFM analysis request
            
        Returns:
            DFM analysis response
        """
        start_time = time.time()
        self.performance_metrics["total_requests"] += 1
        
        try:
            # Check cache first
            cached_result = self._check_cache(request)
            if cached_result:
                logger.info(f"Cache hit for {request.cad_data.part_name}")
                self.performance_metrics["cache_hits"] += 1
                return cached_result
            
            # Process request
            logger.info(f"Processing analysis request for {request.cad_data.part_name}")
            
            # Use enhanced API converter for additional analysis
            enhanced_data = self.api_converter.extract_production_cad_data(
                request.cad_data,
                request.material,
                request.production_volume
            )
            
            # Process with DFM engine
            response = self.dfm_engine.analyze(request)
            
            # Enhance response with additional data
            self._enhance_response(response, enhanced_data)
            
            # Cache result
            self._cache_result(request, response)
            
            # Update performance metrics
            processing_time = time.time() - start_time
            self._update_performance_metrics(processing_time, success=True)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing analysis request: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Update performance metrics
            processing_time = time.time() - start_time
            self._update_performance_metrics(processing_time, success=False)
            
            # Generate error response
            return self._generate_error_response(request, str(e))
    
    def process_batch_requests(self, requests: List[DFMAnalysisRequest]) -> List[DFMAnalysisResponse]:
        """
        Process multiple DFM analysis requests in parallel
        
        Args:
            requests: List of DFM analysis requests
            
        Returns:
            List of DFM analysis responses
        """
        logger.info(f"Processing batch of {len(requests)} requests")
        
        try:
            # Submit all requests to thread pool
            futures = [
                self.executor.submit(self.process_analysis_request, request)
                for request in requests
            ]
            
            # Gather results
            responses = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    responses.append(future.result())
                except Exception as e:
                    logger.error(f"Error in batch processing: {str(e)}")
                    # Add error response for failed request
                    responses.append(self._generate_error_response(None, str(e)))
            
            logger.info(f"Completed batch processing of {len(requests)} requests")
            return responses
            
        except Exception as e:
            logger.error(f"Fatal error in batch processing: {str(e)}")
            # Return error responses for all requests
            return [self._generate_error_response(req, "Batch processing error") for req in requests]
    
    def process_legacy_request(self, legacy_data: Dict[str, Any], 
                              material: str = "ABS", 
                              volume: int = 100) -> Dict[str, Any]:
        """
        Process a legacy format request and return enhanced results
        
        Args:
            legacy_data: Legacy CAD data dictionary
            material: Material type string
            volume: Production volume
            
        Returns:
            Enhanced analysis results in legacy format
        """
        try:
            logger.info("Processing legacy format request")
            
            # Convert legacy format to enhanced format
            cad_geometry = self.api_converter.legacy_to_enhanced_format(legacy_data)
            
            # Create DFM analysis request
            material_type = MaterialType(material)
            request = DFMAnalysisRequest(
                cad_data=cad_geometry,
                material=material_type,
                production_volume=volume,
                processes=[ProcessType.CNC_MILLING, ProcessType.INJECTION_MOLDING, ProcessType.FDM_PRINTING]
            )
            
            # Process request
            response = self.process_analysis_request(request)
            
            # Convert back to legacy format with enhancements
            enhanced_legacy_response = self.api_converter.enhanced_to_legacy_format(response.cad_data)
            
            # Add enhanced data
            enhanced_legacy_response.update({
                "manufacturability_score": response.manufacturability_score,
                "manufacturing_issues": [issue.dict() for issue in response.issues],
                "recommended_processes": [
                    {
                        "process": ps.process.value,
                        "suitability": ps.suitability_score,
                        "cost_estimate": ps.estimated_unit_cost
                    }
                    for ps in response.process_suitability[:3]
                ],
                "complexity_rating": response.metadata.get("complexity_rating", "Medium"),
                "analysis_timestamp": datetime.now().isoformat()
            })
            
            return enhanced_legacy_response
            
        except Exception as e:
            logger.error(f"Error processing legacy request: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _check_cache(self, request: DFMAnalysisRequest) -> Optional[DFMAnalysisResponse]:
        """
        Check if analysis result is in cache
        
        Args:
            request: DFM analysis request
            
        Returns:
            Cached response or None
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(request)
            cache_file = CACHE_DIR / f"{cache_key}.json"
            
            # Check if cache file exists and is not expired
            if cache_file.exists():
                # Check file modification time
                mod_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if datetime.now() - mod_time < timedelta(hours=CACHE_EXPIRY_HOURS):
                    # Load cached response
                    with open(cache_file, "r") as f:
                        cached_data = json.load(f)
                    
                    # Convert to DFMAnalysisResponse
                    return DFMAnalysisResponse(**cached_data)
            
            return None
            
        except Exception as e:
            logger.warning(f"Cache check error: {str(e)}")
            return None
    
    def _cache_result(self, request: DFMAnalysisRequest, response: DFMAnalysisResponse) -> None:
        """
        Cache analysis result
        
        Args:
            request: DFM analysis request
            response: DFM analysis response
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(request)
            cache_file = CACHE_DIR / f"{cache_key}.json"
            
            # Save response to cache
            with open(cache_file, "w") as f:
                json.dump(response.dict(), f)
                
            logger.debug(f"Cached result for {request.cad_data.part_name}")
            
        except Exception as e:
            logger.warning(f"Cache save error: {str(e)}")
    
    def _generate_cache_key(self, request: DFMAnalysisRequest) -> str:
        """
        Generate cache key for request
        
        Args:
            request: DFM analysis request
            
        Returns:
            Cache key string
        """
        # Create a unique hash based on key request properties
        key_data = {
            "part_name": request.cad_data.part_name,
            "volume": request.cad_data.volume,
            "surface_area": request.cad_data.surface_area,
            "material": request.material.value,
            "production_volume": request.production_volume
        }
        
        # Convert to string and hash
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _enhance_response(self, response: DFMAnalysisResponse, enhanced_data: Dict[str, Any]) -> None:
        """
        Enhance DFM response with additional data
        
        Args:
            response: DFM analysis response to enhance
            enhanced_data: Enhanced data from API converter
        """
        # Add complexity analysis to metadata
        if "complexity_analysis" in enhanced_data:
            response.metadata["complexity_score"] = enhanced_data["complexity_analysis"]["complexity_score"]
            response.metadata["complexity_rating"] = enhanced_data["complexity_analysis"]["complexity_rating"]
            response.metadata["complexity_factors"] = enhanced_data["complexity_analysis"]["complexity_factors"]
        
        # Add machining estimates to metadata
        if "machining_estimates" in enhanced_data:
            response.metadata["machining_time"] = enhanced_data["machining_estimates"]
        
        # Add recommended approach if available
        if "recommended_approach" in enhanced_data:
            response.metadata["recommended_approach"] = enhanced_data["recommended_approach"]
    
    def _generate_error_response(self, request: Optional[DFMAnalysisRequest], error_message: str) -> DFMAnalysisResponse:
        """
        Generate error response
        
        Args:
            request: Original request or None
            error_message: Error message
            
        Returns:
            Error response
        """
        # Create basic error response
        error_response = DFMAnalysisResponse(
            cad_data=request.cad_data if request else CADGeometry(
                part_name="error",
                volume=0.0,
                surface_area=0.0,
                bounding_box={"length": 0.0, "width": 0.0, "height": 0.0},
                center_of_mass={"x": 0.0, "y": 0.0, "z": 0.0},
                holes=[],
                thin_walls=[]
            ),
            manufacturability_score=0.0,
            issues=[ManufacturingIssue(
                severity="critical",
                message=f"Analysis error: {error_message}",
                location={"x": 0.0, "y": 0.0, "z": 0.0},
                recommendation="Contact support for assistance"
            )],
            process_suitability=[],
            cost_analysis={},
            metadata={
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        self.performance_metrics["failed_requests"] += 1
        return error_response
    
    def _update_performance_metrics(self, processing_time: float, success: bool) -> None:
        """
        Update performance metrics
        
        Args:
            processing_time: Request processing time in seconds
            success: Whether request was successful
        """
        # Update success/failure counts
        if success:
            self.performance_metrics["successful_requests"] += 1
        else:
            self.performance_metrics["failed_requests"] += 1
        
        # Update processing time metrics
        current_avg = self.performance_metrics["average_processing_time"]
        total_requests = self.performance_metrics["successful_requests"] + self.performance_metrics["failed_requests"]
        
        # Calculate new average
        self.performance_metrics["average_processing_time"] = (
            (current_avg * (total_requests - 1) + processing_time) / total_requests
        )
        
        # Update peak processing time
        if processing_time > self.performance_metrics["peak_processing_time"]:
            self.performance_metrics["peak_processing_time"] = processing_time
        
        # Log performance metrics periodically
        if total_requests % 100 == 0:
            self._log_performance_metrics()
    
    def _log_performance_metrics(self) -> None:
        """Log current performance metrics"""
        try:
            with open(PERFORMANCE_LOG_PATH, "a") as f:
                metrics = {
                    "timestamp": datetime.now().isoformat(),
                    **self.performance_metrics
                }
                f.write(json.dumps(metrics) + "\n")
                
            logger.info(f"Performance metrics: "
                       f"Requests: {self.performance_metrics['total_requests']}, "
                       f"Success rate: {self.performance_metrics['successful_requests'] / max(1, self.performance_metrics['total_requests']):.2%}, "
                       f"Avg time: {self.performance_metrics['average_processing_time']:.2f}s")
                
        except Exception as e:
            logger.warning(f"Error logging performance metrics: {str(e)}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get performance report
        
        Returns:
            Performance metrics dictionary
        """
        return {
            "metrics": self.performance_metrics,
            "timestamp": datetime.now().isoformat(),
            "uptime_hours": 0.0  # Would be calculated from initialization time in a real implementation
        }


# Singleton instance
integration_manager = AdvancedIntegrationManager()


# Convenience functions for API integration

def process_dfm_request(request: DFMAnalysisRequest) -> DFMAnalysisResponse:
    """
    Process a DFM analysis request
    
    Args:
        request: DFM analysis request
        
    Returns:
        DFM analysis response
    """
    return integration_manager.process_analysis_request(request)


def process_legacy_cad_request(legacy_data: Dict[str, Any], 
                              material: str = "ABS", 
                              volume: int = 100) -> Dict[str, Any]:
    """
    Process a legacy CAD request
    
    Args:
        legacy_data: Legacy CAD data dictionary
        material: Material type string
        volume: Production volume
        
    Returns:
        Enhanced analysis results in legacy format
    """
    return integration_manager.process_legacy_request(legacy_data, material, volume)


def process_batch_requests(requests: List[DFMAnalysisRequest]) -> List[DFMAnalysisResponse]:
    """
    Process multiple DFM analysis requests in parallel
    
    Args:
        requests: List of DFM analysis requests
        
    Returns:
        List of DFM analysis responses
    """
    return integration_manager.process_batch_requests(requests)


def get_system_performance() -> Dict[str, Any]:
    """
    Get system performance metrics
    
    Returns:
        Performance metrics dictionary
    """
    return integration_manager.get_performance_report()
