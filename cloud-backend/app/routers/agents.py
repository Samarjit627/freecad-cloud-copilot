"""
Agents router for FreeCAD Manufacturing Co-Pilot API
Handles specialized manufacturing agents and orchestration
"""
import logging
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Models
class AgentRequest(BaseModel):
    agent_type: str
    query: str
    cad_analysis: Optional[Dict[str, Any]] = None
    user_context: Optional[Dict[str, Any]] = None
    additional_data: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    response: Dict[str, Any]
    agent_type: str
    timestamp: str

# Agent registry
AVAILABLE_AGENTS = [
    "dfm_expert", 
    "cost_estimator", 
    "material_selector", 
    "process_planner", 
    "supplier_finder",
    "tooling_expert"
]

@router.get("/list")
async def list_agents():
    """
    List all available specialized agents
    """
    return {
        "agents": [
            {
                "id": "dfm_expert",
                "name": "DFM Expert",
                "description": "Design for Manufacturing analysis and recommendations"
            },
            {
                "id": "cost_estimator",
                "name": "Cost Estimator",
                "description": "Detailed manufacturing cost breakdown and optimization"
            },
            {
                "id": "material_selector",
                "name": "Material Selector",
                "description": "Material selection and comparison for manufacturing"
            },
            {
                "id": "process_planner",
                "name": "Process Planner",
                "description": "Manufacturing process selection and planning"
            },
            {
                "id": "supplier_finder",
                "name": "Supplier Finder",
                "description": "Supplier recommendations based on requirements"
            },
            {
                "id": "tooling_expert",
                "name": "Tooling Expert",
                "description": "Tooling design and optimization recommendations"
            }
        ]
    }

@router.post("/{agent_type}", response_model=AgentResponse)
async def query_agent(agent_type: str, request: AgentRequest):
    """
    Query a specific manufacturing agent
    """
    if agent_type not in AVAILABLE_AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_type}' not found")
    
    try:
        # Process the request with the specified agent
        response = await process_agent_request(agent_type, request)
        
        return AgentResponse(
            response=response,
            agent_type=agent_type,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orchestrate", response_model=Dict[str, Any])
async def orchestrate_agents(request: AgentRequest):
    """
    Orchestrate multiple agents to solve a complex manufacturing query
    """
    try:
        # Determine which agents to use based on the query
        agents_to_use = determine_relevant_agents(request.query, request.cad_analysis)
        
        # Query each relevant agent
        results = {}
        for agent_type in agents_to_use:
            agent_response = await process_agent_request(agent_type, request)
            results[agent_type] = agent_response
        
        # Synthesize results
        synthesis = await synthesize_agent_results(results, request)
        
        return {
            "orchestration_id": f"orch_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "agents_used": agents_to_use,
            "individual_results": results,
            "synthesis": synthesis,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Orchestration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_agent_request(agent_type: str, request: AgentRequest) -> Dict[str, Any]:
    """
    Process a request with a specific agent
    """
    # Get agent-specific prompt
    system_prompt = get_agent_prompt(agent_type)
    
    # Format the input data
    input_data = {
        "query": request.query,
        "cad_analysis": format_cad_analysis(request.cad_analysis),
        "user_context": format_user_context(request.user_context),
        "additional_data": request.additional_data
    }
    
    # Call OpenAI API for agent response
    if not OPENAI_API_KEY:
        return generate_fallback_response(agent_type, input_data)
    
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(input_data)}
            ],
            max_tokens=800,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        # Parse JSON response
        try:
            result = json.loads(response.choices[0].message.content.strip())
            return result
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from OpenAI")
            return generate_fallback_response(agent_type, input_data)
    
    except Exception as e:
        logger.error(f"OpenAI API Error: {e}")
        return generate_fallback_response(agent_type, input_data)

def determine_relevant_agents(query: str, cad_analysis: Optional[Dict[str, Any]]) -> List[str]:
    """
    Determine which agents are relevant to the query
    """
    relevant_agents = []
    
    # Simple keyword matching for now
    if any(keyword in query.lower() for keyword in ["cost", "price", "expensive", "cheap"]):
        relevant_agents.append("cost_estimator")
    
    if any(keyword in query.lower() for keyword in ["material", "plastic", "metal", "steel"]):
        relevant_agents.append("material_selector")
    
    if any(keyword in query.lower() for keyword in ["process", "manufacturing", "make", "produce"]):
        relevant_agents.append("process_planner")
    
    if any(keyword in query.lower() for keyword in ["supplier", "vendor", "source"]):
        relevant_agents.append("supplier_finder")
    
    if any(keyword in query.lower() for keyword in ["design", "improve", "optimize", "dfm"]):
        relevant_agents.append("dfm_expert")
    
    if any(keyword in query.lower() for keyword in ["tool", "mold", "die", "fixture"]):
        relevant_agents.append("tooling_expert")
    
    # If no specific agents matched, use DFM expert and process planner as defaults
    if not relevant_agents:
        relevant_agents = ["dfm_expert", "process_planner"]
    
    return relevant_agents

async def synthesize_agent_results(results: Dict[str, Dict[str, Any]], request: AgentRequest) -> Dict[str, Any]:
    """
    Synthesize results from multiple agents
    """
    # For now, just combine the results
    # In a more advanced implementation, this would use another LLM call to synthesize
    
    synthesis = {
        "summary": "Combined insights from multiple manufacturing experts",
        "recommendations": [],
        "key_insights": {}
    }
    
    # Extract recommendations from each agent
    for agent_type, result in results.items():
        if "recommendations" in result:
            for rec in result["recommendations"]:
                synthesis["recommendations"].append({
                    "source": agent_type,
                    "recommendation": rec
                })
        
        # Extract key insights
        if agent_type == "dfm_expert" and "design_issues" in result:
            synthesis["key_insights"]["design_issues"] = result["design_issues"]
        
        if agent_type == "cost_estimator" and "cost_breakdown" in result:
            synthesis["key_insights"]["cost_breakdown"] = result["cost_breakdown"]
        
        if agent_type == "material_selector" and "materials" in result:
            synthesis["key_insights"]["material_options"] = result["materials"]
        
        if agent_type == "process_planner" and "processes" in result:
            synthesis["key_insights"]["process_options"] = result["processes"]
    
    return synthesis

def get_agent_prompt(agent_type: str) -> str:
    """
    Get agent-specific system prompt
    """
    base_prompt = """You are an expert manufacturing consultant specializing in the Indian market.
You will receive a JSON input with a query, CAD analysis, and user context.
Respond with detailed, actionable insights in JSON format.
Your response should be well-structured and include specific recommendations.
"""
    
    if agent_type == "dfm_expert":
        return base_prompt + """
You are a Design for Manufacturing (DFM) expert.
Focus on identifying design issues and providing specific recommendations to improve manufacturability.
Your JSON response should include:
{
  "design_issues": [list of specific design issues],
  "recommendations": [list of actionable recommendations],
  "dfm_score": numeric score from 1-10,
  "critical_concerns": [list of critical manufacturing concerns],
  "improvement_potential": text summary of potential improvements
}
"""
    
    elif agent_type == "cost_estimator":
        return base_prompt + """
You are a Manufacturing Cost Estimation expert.
Provide detailed cost breakdowns for different manufacturing processes in Indian Rupees (₹).
Your JSON response should include:
{
  "cost_breakdown": {
    "material_cost": value in ₹,
    "labor_cost": value in ₹,
    "tooling_cost": value in ₹,
    "overhead": value in ₹,
    "total_cost": value in ₹
  },
  "volume_pricing": [pricing at different volumes],
  "cost_drivers": [main factors driving cost],
  "recommendations": [cost-saving recommendations]
}
"""
    
    elif agent_type == "material_selector":
        return base_prompt + """
You are a Materials Selection expert for manufacturing.
Recommend optimal materials based on requirements and provide detailed comparisons.
Your JSON response should include:
{
  "materials": [
    {
      "name": material name,
      "properties": {key properties},
      "cost_per_kg": value in ₹,
      "advantages": [list of advantages],
      "disadvantages": [list of disadvantages],
      "suitability_score": numeric score from 1-10
    }
  ],
  "recommendations": [specific material recommendations],
  "availability_in_india": information about local availability
}
"""
    
    elif agent_type == "process_planner":
        return base_prompt + """
You are a Manufacturing Process Planning expert.
Recommend optimal manufacturing processes and provide detailed production planning insights.
Your JSON response should include:
{
  "processes": [
    {
      "name": process name,
      "suitability_score": numeric score from 1-10,
      "advantages": [list of advantages],
      "disadvantages": [list of disadvantages],
      "lead_time": estimated lead time,
      "minimum_volume": minimum economical volume
    }
  ],
  "recommendations": [specific process recommendations],
  "production_planning": insights on production planning,
  "quality_considerations": quality control recommendations
}
"""
    
    elif agent_type == "supplier_finder":
        return base_prompt + """
You are a Manufacturing Supplier expert for the Indian market.
Recommend suitable suppliers based on manufacturing requirements.
Your JSON response should include:
{
  "suppliers": [
    {
      "name": supplier name,
      "location": city in India,
      "specialties": [list of specialties],
      "advantages": [list of advantages],
      "contact_method": how to contact
    }
  ],
  "recommendations": [specific supplier recommendations],
  "sourcing_strategy": recommended sourcing approach,
  "regional_advantages": benefits of different regions in India
}
"""
    
    elif agent_type == "tooling_expert":
        return base_prompt + """
You are a Manufacturing Tooling expert.
Provide detailed insights on tooling requirements, design, and optimization.
Your JSON response should include:
{
  "tooling_requirements": {
    "tool_type": recommended tool type,
    "complexity": complexity assessment,
    "estimated_cost": value in ₹,
    "lead_time": estimated lead time
  },
  "design_considerations": [tooling design considerations],
  "recommendations": [specific tooling recommendations],
  "maintenance_guidelines": tooling maintenance insights
}
"""
    
    else:
        return base_prompt + """
Provide general manufacturing consultation based on the query and available data.
Your JSON response should include:
{
  "analysis": general analysis of the manufacturing requirements,
  "recommendations": [list of recommendations],
  "next_steps": suggested next steps
}
"""

def format_cad_analysis(analysis: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Format CAD analysis for agent consumption"""
    if not analysis:
        return {"available": False}
    
    return {
        "available": True,
        "dimensions": analysis.get("dimensions", {}),
        "features": analysis.get("manufacturing_features", {}),
        "volume": analysis.get("volume", 0),
        "surface_area": analysis.get("surface_area", 0),
        "issues": analysis.get("design_issues", [])
    }

def format_user_context(context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Format user context for agent consumption"""
    if not context:
        return {"available": False}
    
    return {
        "available": True,
        "requirements": context
    }

def generate_fallback_response(agent_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate fallback response when OpenAI is unavailable"""
    
    if agent_type == "dfm_expert":
        return {
            "design_issues": [
                "Unable to perform detailed DFM analysis without AI service",
                "Consider checking wall thickness and draft angles manually"
            ],
            "recommendations": [
                "Ensure minimum wall thickness of 2mm for injection molding",
                "Add draft angles of at least 1-2° for all vertical surfaces",
                "Review part for undercuts and thin sections"
            ],
            "dfm_score": 5,
            "critical_concerns": ["AI service unavailable for detailed analysis"],
            "improvement_potential": "Connect to AI service for comprehensive DFM analysis"
        }
    
    elif agent_type == "cost_estimator":
        return {
            "cost_breakdown": {
                "material_cost": "Requires AI service",
                "labor_cost": "Requires AI service",
                "tooling_cost": "Requires AI service",
                "overhead": "Requires AI service",
                "total_cost": "Requires AI service"
            },
            "volume_pricing": ["AI service unavailable for detailed pricing"],
            "cost_drivers": ["Material selection", "Production volume", "Part complexity"],
            "recommendations": ["Connect to AI service for accurate cost estimation"]
        }
    
    else:
        return {
            "message": "AI service unavailable for detailed analysis",
            "recommendations": [
                "Check connection to OpenAI API",
                "Ensure API key is properly configured",
                "Try again later"
            ],
            "agent_type": agent_type
        }
