"""
Import Diagnostic Script for Cloud Backend
This script attempts to import all critical modules to identify import errors
"""
import os
import sys
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("import_diagnostics")

def test_import(module_path, description):
    """Test importing a module and log the result"""
    try:
        logger.info(f"Attempting to import {module_path} ({description})")
        __import__(module_path)
        logger.info(f"✅ Successfully imported {module_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to import {module_path}: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Run import diagnostics"""
    logger.info("Starting import diagnostics")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    
    # Add current directory to path if not already there
    if os.getcwd() not in sys.path:
        sys.path.append(os.getcwd())
        logger.info(f"Added current directory to Python path")
    
    # Test basic imports
    test_import("fastapi", "FastAPI framework")
    test_import("pydantic", "Pydantic data validation")
    test_import("starlette", "Starlette ASGI framework")
    
    # Test app module imports
    test_import("app", "Main app package")
    test_import("app.main", "Main FastAPI application")
    
    # Test router imports
    test_import("app.routers", "Router package")
    test_import("app.routers.enhanced_analysis", "Enhanced analysis router")
    
    # Test model imports
    test_import("app.models", "Models package")
    test_import("app.models.dfm_models", "DFM models")
    
    # Test service imports
    test_import("app.services", "Services package")
    test_import("app.services.dfm_engine", "DFM engine")
    test_import("app.services.dfm_analysis_methods", "DFM analysis methods")
    test_import("app.services.dfm_process_methods", "DFM process methods")
    test_import("app.services.dfm_cost_methods", "DFM cost methods")
    test_import("app.services.enhanced_api_converter", "Enhanced API converter")
    test_import("app.services.advanced_integration", "Advanced integration")
    
    # Test auth imports
    test_import("app.auth", "Auth package")
    test_import("app.auth.api_key", "API key authentication")
    
    logger.info("Import diagnostics complete")

if __name__ == "__main__":
    main()
