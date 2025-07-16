#!/usr/bin/env python3
"""
Test script to verify that the cloud analyzer fallback mechanism works correctly
"""

import os
import sys
import io
import contextlib
from unittest.mock import patch, MagicMock

# Add the macro directory to the path
macro_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "macro")
sys.path.append(macro_dir)

# Create mock modules for dependencies that might be missing
class MockModule:
    def __init__(self, name):
        self.__name__ = name
        
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

# Mock FreeCAD and related modules if not available
for module_name in ['FreeCAD', 'Part', 'Mesh', 'MeshPart']:
    if module_name not in sys.modules:
        sys.modules[module_name] = MockModule(module_name)

# Create a proper mock for requests with exceptions
class RequestException(Exception):
    pass

class MockResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text
        self.headers = {}
        
    def json(self):
        return self._json_data
        
    def raise_for_status(self):
        if self.status_code >= 400:
            raise RequestException(f"{self.status_code} Client Error: Not Found")

# Create a mock requests module
mock_requests = type('MockRequests', (), {
    'get': lambda url, **kwargs: MockResponse(200, {"status": "ok"}, "OK") if "/health" in url else MockResponse(404, {"error": "Not Found"}, "Not Found"),
    'post': lambda url, **kwargs: MockResponse(404, {"error": "Not Found"}, "Not Found"),
    'exceptions': type('Exceptions', (), {'RequestException': RequestException})
})

# Replace the requests module with our mock
sys.modules['requests'] = mock_requests

# Now import our modules
from cloud_client import CloudApiClient
from cloud_cad_analyzer import CloudCADAnalyzer, get_analyzer
from local_cad_analyzer import LocalCADAnalyzer

def capture_output(func, *args, **kwargs):
    """Capture stdout during function execution"""
    captured_output = io.StringIO()
    with contextlib.redirect_stdout(captured_output):
        try:
            result = func(*args, **kwargs)
            return result, captured_output.getvalue()
        except Exception as e:
            return {"error": str(e)}, captured_output.getvalue()

def test_cloud_fallback():
    """Test that the cloud analyzer falls back to local analysis when cloud endpoints fail"""
    print("\n===== Testing Cloud Analyzer Fallback =====")
    
    # Create a mock for the local analyzer that returns a known result
    local_result = {
        "analysis_type": "local",
        "features": {"holes": 2, "fillets": 4},
        "wall_thickness": {"min": 2.0, "max": 5.0},
        "manufacturing_insights": {"difficulty": "medium"}
    }
    
    # Create a mock document
    class MockDocument:
        def __init__(self, name):
            self.Name = name
            self.Objects = []
            
        def getBoundBox(self):
            class BoundBox:
                def __init__(self):
                    self.XLength = 100.0
                    self.YLength = 50.0
                    self.ZLength = 25.0
            return BoundBox()
    
    mock_doc = MockDocument("TestPart")
    
    # Patch the local analyzer to return our known result
    with patch.object(LocalCADAnalyzer, 'analyze_document', return_value=local_result):
        # Create a cloud analyzer
        analyzer = get_analyzer()
        
        # Force the cloud client to fail
        def mock_analyze_cad(*args, **kwargs):
            raise Exception("All cloud endpoints failed")
        
        # Apply the patch to the cloud client
        with patch.object(CloudApiClient, 'analyze_cad', side_effect=mock_analyze_cad):
            # Capture the output during analysis
            result, output = capture_output(analyzer.analyze_document, mock_doc)
    
    # Check the result
    print("\nAnalysis Result:")
    print(f"Analysis type: {result.get('analysis_type', 'unknown')}")
    print(f"Contains cloud_error: {'cloud_error' in result}")
    print(f"Result keys: {list(result.keys())}")
    
    # Check the output for expected messages
    print("\nOutput Messages:")
    success_message = "✅ Cloud analysis successful!"
    failure_message = "Error in cloud CAD analysis:"
    fallback_message = "⚠️ Falling back to local CAD analysis..."
    
    contains_success = success_message in output
    contains_failure = failure_message in output
    contains_fallback = fallback_message in output
    
    print(f"Contains success message: {contains_success}")
    print(f"Contains failure message: {contains_failure}")
    print(f"Contains fallback message: {contains_fallback}")
    
    # Verify the behavior is correct
    print("\nVerification:")
    if result.get("analysis_type") == "local" and "cloud_error" in result and contains_failure and contains_fallback and not contains_success:
        print("✅ CORRECT: Cloud analysis failed, fell back to local analysis with appropriate messaging")
    else:
        print("❌ INCORRECT: Expected fallback to local analysis with appropriate messaging")
    
    return result, output

if __name__ == "__main__":
    test_cloud_fallback()
