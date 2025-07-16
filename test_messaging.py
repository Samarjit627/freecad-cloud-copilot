#!/usr/bin/env python3
"""
Test script to verify that the cloud analyzer messaging is consistent
"""

import os
import sys
import io
import contextlib
from unittest.mock import patch

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

# Create a proper mock for requests
class MockResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text
        
    def json(self):
        return self._json_data
        
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"{self.status_code} Client Error: Not Found")

class RequestException(Exception):
    pass

class MockRequests:
    def __init__(self):
        self.exceptions = type('Exceptions', (), {'RequestException': RequestException})
        
    def get(self, url, **kwargs):
        if "/health" in url:
            return MockResponse(200, {"status": "ok"}, "OK")
        else:
            return MockResponse(404, {"error": "Not Found"}, "Not Found")
        
    def post(self, url, **kwargs):
        # Simulate 404 error for all cloud analysis endpoints
        response = MockResponse(404, {"error": "Not Found"}, "Not Found")
        response.raise_for_status()
        return response  # This won't be reached due to the exception

# Create the mock module
mock_requests = MockRequests()
sys.modules['requests'] = type('MockRequests', (), {
    'get': mock_requests.get,
    'post': mock_requests.post,
    'exceptions': mock_requests.exceptions
})

# Now import our modules
from cloud_client import CloudApiClient
from cloud_cad_analyzer import CloudCADAnalyzer, get_analyzer
from local_cad_analyzer import LocalCADAnalyzer

def capture_output(func, *args, **kwargs):
    """Capture stdout during function execution"""
    captured_output = io.StringIO()
    with contextlib.redirect_stdout(captured_output):
        result = func(*args, **kwargs)
    return result, captured_output.getvalue()

def test_messaging_consistency():
    """Test that the messaging is consistent when cloud analysis fails"""
    print("\n===== Testing Cloud Analyzer Messaging Consistency =====")
    
    # Patch the local_cad_analyzer to return a known result
    def mock_analyze_document(self, document):
        return {
            "analysis_type": "local",
            "features": {"holes": 2, "fillets": 4},
            "wall_thickness": {"min": 2.0, "max": 5.0},
            "manufacturing_insights": {"difficulty": "medium"}
        }
    
    # Apply the patch
    original_analyze = LocalCADAnalyzer.analyze_document
    LocalCADAnalyzer.analyze_document = mock_analyze_document
    
    try:
        # Create a cloud analyzer
        analyzer = get_analyzer()
        
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
        
        # Capture the output during analysis
        result, output = capture_output(analyzer.analyze_document, mock_doc)
    finally:
        # Restore the original method
        LocalCADAnalyzer.analyze_document = original_analyze
    
    # Check for contradictory messages
    success_message = "✅ Cloud analysis successful!"
    failure_message = "Error in cloud CAD analysis:"
    fallback_message = "⚠️ Falling back to local CAD analysis..."
    
    print("\nAnalysis Output:")
    print(output)
    
    # Check if both success and failure messages appear
    contains_success = success_message in output
    contains_failure = failure_message in output
    contains_fallback = fallback_message in output
    
    print("\nMessage Consistency Check:")
    print(f"Contains success message: {contains_success}")
    print(f"Contains failure message: {contains_failure}")
    print(f"Contains fallback message: {contains_fallback}")
    
    if contains_success and contains_failure:
        print("❌ INCONSISTENT: Both success and failure messages found!")
    elif contains_failure and not contains_success:
        print("✅ CONSISTENT: Only failure message found, no contradictory success message.")
    elif contains_success and not contains_failure:
        print("✅ CONSISTENT: Only success message found, no failure message.")
    else:
        print("⚠️ UNCLEAR: Messaging pattern doesn't match expected patterns.")
    
    # Check the analysis result type
    analysis_type = result.get("analysis_type", "unknown")
    print(f"\nAnalysis type: {analysis_type}")
    print(f"Result keys: {list(result.keys())}")
    
    # Check for cloud_error key which indicates fallback to local
    has_cloud_error = "cloud_error" in result
    
    if analysis_type == "local" and contains_success:
        print("❌ INCONSISTENT: Analysis type is local but success message for cloud was shown!")
    elif analysis_type == "cloud" and contains_failure and has_cloud_error:
        print("❌ INCONSISTENT: Analysis type is cloud but contains cloud_error indicating fallback!")
    elif analysis_type == "local" and contains_failure:
        print(f"✅ CONSISTENT: Analysis type ({analysis_type}) matches the failure messaging.")
    elif analysis_type == "cloud" and contains_success:
        print(f"✅ CONSISTENT: Analysis type ({analysis_type}) matches the success messaging.")
    else:
        print(f"⚠️ UNCLEAR: Analysis type ({analysis_type}) relationship to messaging is unclear.")
    
    return result, output

if __name__ == "__main__":
    test_messaging_consistency()
