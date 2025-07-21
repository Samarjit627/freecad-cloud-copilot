"""
Chat router for FreeCAD Manufacturing Co-Pilot API
Handles chat completions and conversation management
"""
import os
import logging
import requests
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import openai
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    cad_analysis: Optional[Dict[str, Any]] = None
    user_context: Optional[Dict[str, Any]] = None
    mode: str = "general"
    conversation_history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    timestamp: str

# In-memory conversation store (replace with database in production)
conversations = {}

@router.post("/completions", response_model=ChatResponse)
async def get_chat_completion(request: ChatRequest):
    """
    Get manufacturing expert advice based on query and CAD analysis
    """
    try:
        # Generate a conversation ID if not present
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Check if this is a DFM analysis request
        query_lower = request.query.lower()
        if ("dfm" in query_lower or 
            "check for manufacturability" in query_lower or
            "design for manufacturing" in query_lower or
            "check this part" in query_lower or
            "manufacturable" in query_lower):
            
            logger.info("DFM analysis request detected")
            
            # Extract CAD analysis data if available
            part_name = "Unknown Part"
            material = "ABS"  # Default material
            min_wall_thickness = 0.8  # Default thickness in mm
            fillet_radius = 0.3  # Default fillet radius in mm
            draft_angle = 0.5  # Default draft angle in degrees
            has_undercuts = False  # Default undercut status
            
            # Use CAD analysis data if available
            if request.cad_analysis:
                # Extract from engineering analysis if available
                if "engineering_analysis" in request.cad_analysis:
                    eng = request.cad_analysis.get("engineering_analysis", {})
                    thickness_data = eng.get("thickness", {})
                    features_data = eng.get("features", {})
                    
                    part_name = request.cad_analysis.get("name", part_name)
                    material = request.cad_analysis.get("material", material)
                    min_wall_thickness = thickness_data.get("min", min_wall_thickness)
                    
                    # Extract fillet radius from engineering analysis
                    if "fillets" in features_data and features_data["fillets"]:
                        fillets = features_data["fillets"]
                        fillet_radii = [f.get("radius", 0) for f in fillets if isinstance(f, dict) and "radius" in f]
                        if fillet_radii:
                            fillet_radius = min(fillet_radii)
                    
                    # Extract draft angle and undercut information
                    draft_angle = min(
                        1.0,  # Default minimum
                        features_data.get("min_draft_angle", draft_angle)
                    )
                    has_undercuts = features_data.get("undercuts_count", 0) > 0
                
                # Fall back to basic dimensions if engineering analysis not available
                else:
                    dims = request.cad_analysis.get("dimensions", {})
                    features = request.cad_analysis.get("manufacturing_features", {})
                    
                    part_name = request.cad_analysis.get("name", part_name)
                    material = request.cad_analysis.get("material", material)
                    min_wall_thickness = dims.get("thickness", min_wall_thickness)
                    fillet_radius = features.get("min_fillet_radius", fillet_radius)
                    draft_angle = features.get("min_draft_angle", draft_angle)
                    has_undercuts = features.get("has_undercuts", has_undercuts)
            
            # Prepare DFM input
            dfm_input = {
                "part_name": part_name,
                "material": material,
                "min_wall_thickness_mm": min_wall_thickness,
                "fillet_radius_mm": fillet_radius,
                "draft_angle_deg": draft_angle,
                "has_undercuts": has_undercuts
            }
            
            try:
                # Call the DFM check endpoint (internal call)
                # For local development, we use direct API call
                from app.agents.dfm_agent import check_dfm
                from app.agents.dfm_agent import DFMInput
                
                # Convert dict to pydantic model
                dfm_request = DFMInput(**dfm_input)
                dfm_result = check_dfm(dfm_request)
                
                # Format the response
                response_text = f"DFM Analysis for {dfm_result.part_name}:\n\n"
                
                if not dfm_result.violations:
                    response_text += "✅ No manufacturability issues detected!\n"
                else:
                    for v in dfm_result.violations:
                        emoji = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(v.severity, "")
                        response_text += f"{emoji} {v.rule}: {v.message}\n"
                
                response_text += "\nWould you like detailed recommendations to improve manufacturability?"
                
                # Store conversation
                if conversation_id not in conversations:
                    conversations[conversation_id] = []
                
                conversations[conversation_id].append({"role": "user", "content": request.query})
                conversations[conversation_id].append({"role": "assistant", "content": response_text})
                
                return ChatResponse(
                    response=response_text,
                    conversation_id=conversation_id,
                    timestamp=datetime.now().isoformat()
                )
                
            except Exception as e:
                logger.error(f"DFM check error: {e}")
                # Fall back to regular chat completion if DFM check fails
                logger.info("Falling back to regular chat completion")
        
        # Regular chat completion flow
        # Build system prompt
        system_prompt = build_system_prompt(request.cad_analysis, request.user_context, request.mode)
        
        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if request.conversation_history:
            for msg in request.conversation_history[-6:]:  # Last 6 messages
                messages.append({"role": msg.role, "content": msg.content})
        
        # Add current query
        messages.append({"role": "user", "content": request.query})
        
        # Call OpenAI API
        if not OPENAI_API_KEY:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        try:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=500,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Store conversation
            if conversation_id not in conversations:
                conversations[conversation_id] = []
            
            conversations[conversation_id].append({"role": "user", "content": request.query})
            conversations[conversation_id].append({"role": "assistant", "content": ai_response})
            
            # Keep history manageable
            if len(conversations[conversation_id]) > 20:
                conversations[conversation_id] = conversations[conversation_id][-20:]
            
            return ChatResponse(
                response=ai_response,
                conversation_id=conversation_id,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"OpenAI API Error: {e}")
            raise HTTPException(status_code=500, detail=f"OpenAI API Error: {str(e)}")
    
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}", response_model=List[ChatMessage])
async def get_conversation(conversation_id: str):
    """
    Get conversation history by ID
    """
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return [ChatMessage(role=msg["role"], content=msg["content"]) 
            for msg in conversations[conversation_id]]

def build_system_prompt(cad_analysis: Optional[Dict[str, Any]], 
                       user_context: Optional[Dict[str, Any]], 
                       mode: str) -> str:
    """
    Build system prompt for AI based on CAD analysis and user context
    """
    base_context = f"""You are a manufacturing engineer consultant specializing in the Indian market.

PART ANALYSIS:
{format_cad_analysis(cad_analysis)}

USER REQUIREMENTS:
{format_user_context(user_context)}

AVAILABLE PROCESSES:
- Injection Molding: Min vol 1000, Tooling ₹200,000, 6w lead
- CNC Machining: Min vol 1, Tooling ₹5,000, 2w lead
- 3D Printing: Min vol 1, Tooling ₹0, 1w lead
- Sheet Metal: Min vol 50, Tooling ₹50,000, 3w lead

COST FACTORS (Indian Market):
- Labor: ₹200-800/hour
- Material markup: 15-25%
- Tooling: 20-40% of global costs
- Quality systems: ISO 9001 standard
"""
    
    if mode == "cost":
        return base_context + """
Focus on detailed cost analysis in Indian Rupees (₹). Include:
- Material costs with Indian pricing
- Tooling and setup costs
- Labor and processing costs
- Volume-based pricing tiers
- Hidden costs and considerations
Keep response professional and under 300 words."""
    
    elif mode == "process":
        return base_context + """
Focus on manufacturing process selection. Provide:
- Best process for the given requirements
- Alternative processes with trade-offs
- Indian manufacturing capabilities
- Quality and timeline considerations
- Supplier recommendations by region
Keep response practical and under 300 words."""
    
    elif mode == "dfm":
        return base_context + """
Focus on Design for Manufacturing analysis. Provide:
- Critical design issues that need addressing
- Specific recommendations to improve manufacturability
- Material selection considerations
- Process-specific design guidelines
- Cost-saving opportunities
Keep response actionable and under 300 words."""
    
    else:
        return base_context + """
Provide comprehensive manufacturing consultation. Include:
- Process recommendation with rationale
- Cost estimates for Indian market
- Timeline and supplier suggestions
- Design optimization opportunities
- Risk factors and mitigation
Keep response balanced and under 350 words."""

def format_cad_analysis(analysis: Optional[Dict[str, Any]]) -> str:
    """Format CAD analysis for AI"""
    if not analysis:
        return "No CAD analysis available"
    
    dims = analysis.get("dimensions", {})
    features = analysis.get("manufacturing_features", {})
    
    return f"""Size: {dims.get('length', 0):.0f}×{dims.get('width', 0):.0f}×{dims.get('height', 0):.0f}mm
Volume: {analysis.get('volume', 0):.0f} cm³
Surface Area: {analysis.get('surface_area', 0):.0f} cm²
Wall Thickness: {dims.get('thickness', 0):.1f}mm
Features: {features.get('holes', 0)} holes, {features.get('ribs', 0)} ribs
Complexity: {features.get('complexity_rating', 'Medium')}
Moldability Score: {features.get('moldability_score', 8.0):.1f}/10"""

def format_user_context(context: Optional[Dict[str, Any]]) -> str:
    """Format user context for AI"""
    if not context:
        return "No user requirements specified"
    
    return "\n".join([f"- {k.replace('_', ' ').title()}: {v}" for k, v in context.items()])
