"""
Claude API DFM Analyzer for Real Manufacturing Issue Detection
Integrates with Anthropic Claude API to identify specific DFM issues like sharp corners, thin walls, undercuts
"""

import os
import json
import time
from typing import Dict, List, Any, Optional

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: anthropic library not available for Claude DFM analysis")

class ClaudeDFMAnalyzer:
    """Advanced DFM analyzer using Claude API for real manufacturing issue detection"""
    
    def __init__(self, api_key=None):
        """Initialize Claude DFM analyzer"""
        self.client = None
        self.api_key = api_key
        self.available = False
        
        # Initialize Claude client if available
        self._initialize_claude()
    
    def _initialize_claude(self):
        """Initialize Claude API client"""
        try:
            if not ANTHROPIC_AVAILABLE:
                print("Claude DFM: anthropic library not available")
                return
            
            # Use provided API key first, then try environment
            if not self.api_key:
                self.api_key = os.getenv('ANTHROPIC_API_KEY')
            
            if not self.api_key:
                # Try to load from .env file
                try:
                    from dotenv import load_dotenv
                    load_dotenv()
                    self.api_key = os.getenv('ANTHROPIC_API_KEY')
                except ImportError:
                    pass
            
            if self.api_key:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.available = True
                print("✅ Claude DFM analyzer initialized successfully")
            else:
                print("⚠️ ANTHROPIC_API_KEY not found - Claude DFM analysis disabled")
                
        except Exception as e:
            print(f"Error initializing Claude DFM analyzer: {str(e)}")
            self.available = False
    
    def analyze_dfm_issues(self, cad_data: Dict[str, Any], manufacturing_process: str = "injection_molding", 
                          material: str = "abs") -> Dict[str, Any]:
        """
        Analyze CAD data for real DFM issues using Claude API
        
        Args:
            cad_data: CAD geometry data from FreeCAD
            manufacturing_process: Target manufacturing process
            material: Material type
            
        Returns:
            Dict containing specific DFM issues with locations and recommendations
        """
        if not self.available:
            return {
                "success": False,
                "error": "Claude API not available",
                "issues": []
            }
        
        try:
            # Build comprehensive prompt for Claude
            prompt = self._build_dfm_prompt(cad_data, manufacturing_process, material)
            
            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.1,  # Low temperature for consistent technical analysis
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse Claude's response
            analysis_result = self._parse_claude_response(response.content[0].text)
            
            return {
                "success": True,
                "issues": analysis_result.get("issues", []),
                "recommendations": analysis_result.get("recommendations", []),
                "severity_summary": analysis_result.get("severity_summary", {}),
                "claude_analysis": True,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
            
        except Exception as e:
            print(f"Error in Claude DFM analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "issues": []
            }
    
    def _build_dfm_prompt(self, cad_data: Dict[str, Any], manufacturing_process: str, material: str) -> str:
        """Build comprehensive DFM analysis prompt for Claude"""
        
        # Extract key geometry information
        objects_info = []
        total_volume = 0
        total_faces = 0
        
        for obj in cad_data.get("objects", []):
            obj_summary = {
                "name": obj.get("label", "Unknown"),
                "type": obj.get("type", "Unknown"),
                "volume": obj.get("volume", 0),
                "surface_area": obj.get("surface_area", 0),
                "dimensions": obj.get("dimensions", {}),
                "faces": obj.get("faces", 0),
                "edges": obj.get("edges", 0)
            }
            objects_info.append(obj_summary)
            total_volume += obj.get("volume", 0)
            total_faces += obj.get("faces", 0)
        
        # Build the prompt
        prompt = f"""You are an expert manufacturing engineer specializing in Design for Manufacturing (DFM) analysis, particularly for {manufacturing_process} with {material} material.

I need you to analyze this CAD geometry data and identify specific manufacturing issues that would cause problems in {manufacturing_process}:

**CAD GEOMETRY DATA:**
- Total Volume: {total_volume:.2f} mm³
- Total Faces: {total_faces}
- Number of Objects: {len(objects_info)}

**OBJECT DETAILS:**
"""
        
        for i, obj in enumerate(objects_info, 1):
            prompt += f"""
Object {i}: {obj['name']}
- Type: {obj['type']}
- Volume: {obj['volume']:.2f} mm³
- Surface Area: {obj['surface_area']:.2f} mm²
- Faces: {obj['faces']}
- Edges: {obj['edges']}
- Dimensions: {obj['dimensions']}
"""
        
        prompt += f"""

**MANUFACTURING CONTEXT:**
- Process: {manufacturing_process.replace('_', ' ').title()}
- Material: {material.upper()}
- Target: Production-ready parts

**ANALYSIS REQUIREMENTS:**
Please identify specific DFM issues for {manufacturing_process} and provide your response in this exact JSON format:

{{
    "issues": [
        {{
            "type": "thin_walls|sharp_corners|undercuts|draft_angles|gate_location|cooling|ejection|other",
            "severity": "critical|high|medium|low",
            "title": "Brief issue title",
            "description": "Detailed description of the manufacturing problem",
            "location": "Where this issue occurs (e.g., 'bottom face', 'corner edges', 'internal features')",
            "recommendation": "Specific fix or design change needed",
            "impact": "How this affects manufacturing (cost, quality, feasibility)"
        }}
    ],
    "recommendations": [
        "Overall design recommendations for better manufacturability"
    ],
    "severity_summary": {{
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }}
}}

**FOCUS ON THESE COMMON {manufacturing_process.replace('_', ' ').title()} ISSUES:**
1. **Thin Walls**: Walls thinner than 0.8mm for ABS injection molding
2. **Sharp Corners**: Internal corners without adequate radius (min 0.5mm)
3. **Undercuts**: Features that prevent part ejection from mold
4. **Draft Angles**: Vertical walls without 1-3° draft for ejection
5. **Gate Location**: Poor gate placement causing flow issues
6. **Cooling**: Thick sections causing uneven cooling and warpage
7. **Ejection**: Features that complicate part removal from mold

Analyze the geometry data carefully and identify real, specific issues that would cause manufacturing problems. Be precise about locations and provide actionable recommendations.
"""
        
        return prompt
    
    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's JSON response into structured data"""
        try:
            # Try to extract JSON from Claude's response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                analysis_result = json.loads(json_str)
                
                # Validate and enhance the response
                if "issues" not in analysis_result:
                    analysis_result["issues"] = []
                
                if "recommendations" not in analysis_result:
                    analysis_result["recommendations"] = []
                
                if "severity_summary" not in analysis_result:
                    analysis_result["severity_summary"] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
                
                # Add position coordinates for highlighting (estimated based on geometry)
                for issue in analysis_result["issues"]:
                    if "position" not in issue:
                        issue["position"] = self._estimate_issue_position(issue)
                
                return analysis_result
            else:
                # Fallback: create structured response from text
                return self._parse_text_response(response_text)
                
        except json.JSONDecodeError as e:
            print(f"Error parsing Claude JSON response: {e}")
            return self._parse_text_response(response_text)
        except Exception as e:
            print(f"Error processing Claude response: {e}")
            return {"issues": [], "recommendations": [], "severity_summary": {}}
    
    def _parse_text_response(self, response_text: str) -> Dict[str, Any]:
        """Fallback parser for non-JSON responses"""
        issues = []
        recommendations = []
        
        # Simple text parsing for common DFM issues
        lines = response_text.split('\n')
        current_issue = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for issue indicators
            if any(keyword in line.lower() for keyword in ['thin wall', 'sharp corner', 'undercut', 'draft']):
                if current_issue:
                    issues.append(current_issue)
                
                # Determine severity
                severity = "medium"
                if any(word in line.lower() for word in ['critical', 'severe', 'major']):
                    severity = "critical"
                elif any(word in line.lower() for word in ['high', 'important']):
                    severity = "high"
                elif any(word in line.lower() for word in ['minor', 'low']):
                    severity = "low"
                
                current_issue = {
                    "type": "manufacturing_issue",
                    "severity": severity,
                    "title": line[:50] + "..." if len(line) > 50 else line,
                    "description": line,
                    "location": "geometry",
                    "recommendation": "Review design for manufacturability",
                    "position": {"x": 0, "y": 0, "z": 0}
                }
            elif line.lower().startswith('recommend'):
                recommendations.append(line)
        
        if current_issue:
            issues.append(current_issue)
        
        # Count severities
        severity_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for issue in issues:
            severity = issue.get("severity", "medium")
            if severity in severity_summary:
                severity_summary[severity] += 1
        
        return {
            "issues": issues,
            "recommendations": recommendations,
            "severity_summary": severity_summary
        }
    
    def _estimate_issue_position(self, issue: Dict[str, Any]) -> Dict[str, float]:
        """Estimate 3D position for issue highlighting based on issue type and location"""
        # Default position (will be refined based on actual geometry analysis)
        position = {"x": 0.0, "y": 0.0, "z": 0.0}
        
        issue_type = issue.get("type", "")
        location = issue.get("location", "").lower()
        
        # Rough position estimation based on issue type
        if "bottom" in location:
            position["z"] = -5.0
        elif "top" in location:
            position["z"] = 5.0
        elif "corner" in location:
            position.update({"x": 2.0, "y": 2.0, "z": 1.0})
        elif "edge" in location:
            position.update({"x": 1.0, "y": 0.0, "z": 0.0})
        
        return position
    
    def is_available(self) -> bool:
        """Check if Claude DFM analyzer is available"""
        return self.available
