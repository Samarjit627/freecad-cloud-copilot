"""
Text-to-CAD Cloud Agent - Google Cloud Run Service
Processes natural language descriptions and returns both engineering analysis and FreeCAD Python code

This service:
- Receives natural language requests via HTTP API
- Performs engineering analysis (materials, structural, manufacturing)
- Generates professional engineering reports
- Creates FreeCAD Python code for 3D model generation
- Returns both analysis and executable CAD code
"""

from flask import Flask, request, jsonify
import json
import math
import os
import logging
import time
import random
import traceback
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load API keys from environment variables
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Import AI libraries conditionally to avoid startup errors if not available
try:
    import anthropic
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    logger.warning("Anthropic library not available. Some features will be disabled.")
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI library not available. Some features will be disabled.")
    OPENAI_AVAILABLE = False

class TextToCADEngine:
    """Engine for converting text descriptions to CAD models"""
    
    def __init__(self):
        """Initialize the Text-to-CAD engine"""
        self.anthropic_client = None
        self.openai_client = None
        
        # Initialize AI clients if available
        if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
            self.anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
        
        if OPENAI_AVAILABLE and OPENAI_API_KEY:
            openai.api_key = OPENAI_API_KEY
            
        logger.info(f"Text-to-CAD Engine initialized. Anthropic: {ANTHROPIC_AVAILABLE}, OpenAI: {OPENAI_AVAILABLE}")
    
    def generate_engineering_analysis(self, prompt: str, detail_level: str = "medium") -> str:
        """Generate engineering analysis from a text prompt"""
        if not self.anthropic_client:
            return "Engineering analysis unavailable - Anthropic API not configured"
        
        try:
            system_prompt = f"""You are an expert mechanical engineer specializing in CAD design.
            Analyze the following design request and provide a detailed engineering analysis.
            Include material recommendations, structural considerations, manufacturing constraints,
            and design optimization suggestions. Use a {detail_level} level of detail.
            """
            
            response = self.anthropic_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating engineering analysis: {e}")
            return f"Error generating engineering analysis: {str(e)}"
    
    def generate_freecad_code(self, prompt: str, engineering_analysis: str) -> str:
        """Generate FreeCAD Python code from a text prompt and engineering analysis"""
        if not self.anthropic_client:
            return "# FreeCAD code generation unavailable - Anthropic API not configured"
        
        try:
            system_prompt = """You are an expert FreeCAD programmer. 
            Generate Python code for FreeCAD that implements the requested design.
            The code should be complete, well-commented, and ready to run in FreeCAD's Python console.
            Use best practices for parametric modeling and include appropriate error handling.
            """
            
            combined_prompt = f"""Design Request: {prompt}
            
            Engineering Analysis: {engineering_analysis}
            
            Based on this information, generate complete FreeCAD Python code that implements this design.
            The code should be well-structured, commented, and follow FreeCAD best practices.
            """
            
            response = self.anthropic_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": combined_prompt}]
            )
            
            # Extract code blocks from the response
            code = response.content[0].text
            
            # If the response contains markdown code blocks, extract just the code
            if "```python" in code and "```" in code:
                code_blocks = []
                lines = code.split("\n")
                in_code_block = False
                
                for line in lines:
                    if line.strip().startswith("```python"):
                        in_code_block = True
                        continue
                    elif line.strip() == "```" and in_code_block:
                        in_code_block = False
                        continue
                    
                    if in_code_block:
                        code_blocks.append(line)
                
                return "\n".join(code_blocks)
            
            return code
        except Exception as e:
            logger.error(f"Error generating FreeCAD code: {e}")
            return f"# Error generating FreeCAD code: {str(e)}"

# Initialize the Text-to-CAD engine
engine = TextToCADEngine()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "anthropic_available": ANTHROPIC_AVAILABLE and bool(ANTHROPIC_API_KEY),
        "openai_available": OPENAI_AVAILABLE and bool(OPENAI_API_KEY)
    })

@app.route('/text-to-cad', methods=['POST'])
def text_to_cad():
    """Convert text description to CAD model"""
    try:
        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({"error": "Missing required parameter: prompt"}), 400
        
        prompt = data['prompt']
        parameters = data.get('parameters', {})
        detail_level = parameters.get('detail_level', 'medium')
        
        logger.info(f"Processing text-to-CAD request: {prompt[:50]}...")
        
        # Generate engineering analysis
        start_time = time.time()
        engineering_analysis = engine.generate_engineering_analysis(prompt, detail_level)
        analysis_time = time.time() - start_time
        logger.info(f"Engineering analysis generated in {analysis_time:.2f}s")
        
        # Generate FreeCAD code
        start_time = time.time()
        freecad_code = engine.generate_freecad_code(prompt, engineering_analysis)
        code_time = time.time() - start_time
        logger.info(f"FreeCAD code generated in {code_time:.2f}s")
        
        return jsonify({
            "prompt": prompt,
            "engineering_analysis": engineering_analysis,
            "freecad_code": freecad_code,
            "metadata": {
                "analysis_time_seconds": analysis_time,
                "code_generation_time_seconds": code_time,
                "total_time_seconds": analysis_time + code_time,
                "detail_level": detail_level
            }
        })
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Error processing request: {str(e)}",
            "traceback": traceback.format_exc()
        }), 500

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 8070))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
