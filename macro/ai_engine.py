"""
Manufacturing Intelligence Engine for the FreeCAD Manufacturing Co-Pilot
Handles AI processing and cloud communication
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List

# Try to import OpenAI for local fallback
try:
    import openai
    HAS_OPENAI_SDK = True
except ImportError:
    HAS_OPENAI_SDK = False

# Import local modules
try:
    import cloud_client
    import config
except ImportError:
    import cloud_client
    import config

class ManufacturingIntelligenceEngine:
    """Advanced AI engine with manufacturing expertise and cloud connectivity"""
    
    def __init__(self):
        self.conversation_history = []
        self.client = None
        self.cloud_client = cloud_client.get_client() if config.USE_CLOUD_BACKEND else None
        
        # Initialize OpenAI client for local fallback
        if HAS_OPENAI_SDK and not config.USE_CLOUD_BACKEND:
            try:
                self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
                print("✅ OpenAI client initialized successfully")
            except Exception as e:
                print(f"❌ OpenAI client initialization failed: {e}")
                self.client = None
        else:
            if not config.USE_CLOUD_BACKEND:
                print("⚠️ OpenAI SDK not available - using fallback responses")
        
    def get_expert_advice(self, query: str, cad_analysis: Dict[str, Any], 
                          user_context: Dict[str, Any], mode: str = "general") -> str:
        """Get expert manufacturing advice with full context"""
        
        # Use cloud backend if available
        if config.USE_CLOUD_BACKEND and self.cloud_client and self.cloud_client.connected:
            try:
                # Get conversation ID from history if available
                conversation_id = None
                if self.conversation_history:
                    conversation_id = self.conversation_history[-1].get("conversation_id")
                
                # Call cloud API
                response = self.cloud_client.get_chat_response(
                    query=query,
                    cad_analysis=cad_analysis,
                    user_context=user_context,
                    mode=mode,
                    conversation_id=conversation_id
                )
                
                result = response.get("response", "")
                conversation_id = response.get("conversation_id", "")
                
                # Store in conversation history
                self.conversation_history.append({
                    "query": query,
                    "response": result,
                    "timestamp": datetime.now().isoformat(),
                    "mode": mode,
                    "conversation_id": conversation_id,
                    "source": "cloud"
                })
                
                return result
                
            except Exception as e:
                print(f"❌ Cloud API Error: {e}")
                # Fall back to local processing
        
        # Fallback to local OpenAI if available
        if HAS_OPENAI_SDK and self.client:
            try:
                system_prompt = self.build_expert_system_prompt(cad_analysis, user_context, mode)
                
                response = self.client.chat.completions.create(
                    model=config.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                
                result = response.choices[0].message.content.strip()
                
                # Store in conversation history
                self.conversation_history.append({
                    "query": query,
                    "response": result,
                    "timestamp": datetime.now().isoformat(),
                    "mode": mode,
                    "source": "local_openai"
                })
                
                return result
                
            except Exception as e:
                print(f"❌ OpenAI API Error: {e}")
        
        # Final fallback to hardcoded responses
        return self.get_fallback_response(query, cad_analysis, user_context, mode)
    
    def get_fallback_response(self, query: str, cad_analysis: Dict[str, Any], 
                              user_context: Dict[str, Any], mode: str) -> str:
        """Fallback response when cloud and OpenAI are not available"""
        
        if not cad_analysis:
            return "I'd be happy to help with manufacturing advice, but I need CAD analysis data first. Please click 'Analyze CAD' to get started."
        
        dims = cad_analysis.get("dimensions", {})
        features = cad_analysis.get("manufacturing_features", {})
        
        # Store in conversation history
        self.conversation_history.append({
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "source": "fallback"
        })
        
        # Generate intelligent fallback based on analysis
        if "cost" in query.lower() or mode == "cost":
            response = f"""💰 **Cost Analysis for your {dims.get('length', 0):.0f}×{dims.get('width', 0):.0f}×{dims.get('height', 0):.0f}mm part:**

**Material Cost:** ₹{max(50, dims.get('length', 0) * dims.get('width', 0) * dims.get('thickness', 2) * 0.001):.0f} per part (ABS plastic)

**Tooling Cost:** ₹{200000 + features.get('holes', 0) * 25000:.0f} (Injection molding)

**Recommended Volume:** 1,000-10,000 pieces for optimal cost/part

**Indian Suppliers:** Mumbai, Bangalore, Chennai, Pune

*For real-time AI analysis, connect to the cloud backend*"""
        
        elif "process" in query.lower() or mode == "process":
            response = f"""🔧 **Manufacturing Process Recommendations:**

**Primary Process:** {'Injection Molding' if dims.get('thickness', 0) > 1 else 'CNC Machining'}

**Secondary Options:**
• 3D Printing (Prototyping): 1-5 days
• CNC Machining (Low volume): 1-2 weeks  
• Sheet Metal (If applicable): 2-3 weeks

**Complexity Rating:** {features.get('complexity_rating', 'Medium')}

**Indian Manufacturing Hubs:** Tamil Nadu, Maharashtra, Karnataka

*For detailed AI analysis, connect to the cloud backend*"""
        
        elif "material" in query.lower():
            response = f"""🧪 **Material Recommendations:**

**Primary Options:**
• ABS Plastic - ₹120/kg (Good balance)
• PP Plastic - ₹95/kg (Cost effective)
• PC-ABS - ₹180/kg (High strength)

**For your {dims.get('thickness', 0):.1f}mm wall thickness:**
{'Excellent choice' if dims.get('thickness', 0) > 1.5 else 'Consider increasing to 2-3mm'}

**Estimated Weight:** {max(50, dims.get('length', 0) * dims.get('width', 0) * dims.get('thickness', 2) * 0.001):.0f}g

*For AI-powered material selection, connect to the cloud backend*"""
        
        else:
            response = f"""🚀 **Manufacturing Analysis for your part:**

**Dimensions:** {dims.get('length', 0):.0f} × {dims.get('width', 0):.0f} × {dims.get('height', 0):.0f}mm

**Key Features:** {features.get('holes', 0)} holes, {features.get('ribs', 0)} ribs

**Recommended Process:** {'Injection Molding' if dims.get('thickness', 0) > 1 else 'CNC Machining'}

**Estimated Cost:** ₹{50 + features.get('holes', 0) * 25:.0f} per part

**Timeline:** 4-8 weeks including tooling

**Ask me about:** costs, processes, materials, optimization

*For full AI capabilities, connect to the cloud backend*"""
        
        # Update conversation history with response
        if self.conversation_history and self.conversation_history[-1].get("query") == query:
            self.conversation_history[-1]["response"] = response
        
        return response
    
    def build_expert_system_prompt(self, cad_analysis: Dict[str, Any], 
                                  user_context: Dict[str, Any], mode: str) -> str:
        """Build expert system prompt based on mode"""
        
        base_context = f"""You are a senior manufacturing engineer consultant specializing in the Indian market. 
        
PART ANALYSIS:
{self.format_cad_analysis(cad_analysis)}

USER REQUIREMENTS:
{self.format_user_context(user_context)}
"""
        
        if mode == "dfm":
            return base_context + """
FOCUS: Design for Manufacturing (DFM) Analysis
Provide specific DFM recommendations including:
1. Design optimization for manufacturability
2. Material flow considerations
3. Tooling complexity reduction
4. Quality improvement suggestions
5. Cost reduction opportunities
Keep response under 250 words but actionable."""
            
        elif mode == "cost":
            return base_context + """
FOCUS: Cost Analysis & Estimation
Provide detailed cost breakdown in Indian Rupees (₹):
1. Material costs per part
2. Tooling costs estimation
3. Processing costs
4. Volume-based pricing
5. Cost optimization strategies
Include specific ₹ amounts and percentages."""
            
        elif mode == "process":
            return base_context + """
FOCUS: Manufacturing Process Selection
Analyze and recommend:
1. Optimal manufacturing processes
2. Indian supplier capabilities
3. Process comparison with pros/cons
4. Lead time analysis
5. Quality considerations
Include specific Indian cities/regions."""
            
        else:  # general mode
            return base_context + """
FOCUS: General Manufacturing Consultation
Provide expert advice including:
1. Best manufacturing process for this part
2. Cost estimates in Indian Rupees (₹)
3. Quality considerations
4. Timeline estimates
5. One key optimization tip
Keep response comprehensive but under 200 words."""
    
    def format_cad_analysis(self, analysis: Optional[Dict[str, Any]]) -> str:
        """Format CAD analysis for AI prompt"""
        if not analysis or "error" in analysis:
            return "No CAD analysis available"
        
        dims = analysis.get("dimensions", {})
        features = analysis.get("manufacturing_features", {})
        
        return f"""Dimensions: {dims.get('length', 0):.1f} × {dims.get('width', 0):.1f} × {dims.get('height', 0):.1f} mm
Wall thickness: {dims.get('thickness', 0):.2f} mm
Surface area: {analysis.get('surface_area', 0):.1f} cm²
Volume: {analysis.get('volume', 0):.1f} cm³
Holes: {features.get('holes', 0)}, Ribs: {features.get('ribs', 0)}
Complexity: {features.get('complexity_rating', 'Medium')}
Moldability: {features.get('moldability_score', 8.0):.1f}/10"""
    
    def format_user_context(self, context: Optional[Dict[str, Any]]) -> str:
        """Format user context for AI prompt"""
        if not context:
            return "No user requirements specified"
        
        formatted = []
        for key, value in context.items():
            if isinstance(value, list):
                formatted.append(f"{key.title()}: {', '.join(value)}")
            else:
                formatted.append(f"{key.title()}: {value}")
        
        return "\n".join(formatted)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_conversation_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of available manufacturing agents from the cloud backend"""
        if not config.USE_CLOUD_BACKEND or not self.cloud_client or not self.cloud_client.connected:
            return self._get_fallback_agents()
        
        try:
            response = self.cloud_client.get_available_agents()
            return response.get("agents", [])
        except Exception as e:
            print(f"❌ Error getting agents: {e}")
            return self._get_fallback_agents()
    
    def _get_fallback_agents(self) -> List[Dict[str, Any]]:
        """Return fallback agent list when cloud is not available"""
        return [
            {"id": "dfm_expert", "name": "DFM Expert", "description": "Design for Manufacturing specialist"},
            {"id": "cost_estimator", "name": "Cost Estimator", "description": "Provides detailed cost analysis"},
            {"id": "process_planner", "name": "Process Planner", "description": "Recommends optimal manufacturing processes"},
            {"id": "material_selector", "name": "Material Selector", "description": "Suggests appropriate materials"}
        ]
    
    def query_agent(self, agent_id: str, query: str, cad_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Query a specific manufacturing agent"""
        if not config.USE_CLOUD_BACKEND or not self.cloud_client or not self.cloud_client.connected:
            return self._get_fallback_agent_response(agent_id, query, cad_analysis)
        
        try:
            response = self.cloud_client.query_agent(agent_id, query, cad_analysis)
            
            # Store in conversation history
            self.conversation_history.append({
                "query": query,
                "response": response.get("response", ""),
                "timestamp": datetime.now().isoformat(),
                "agent_id": agent_id,
                "source": "cloud_agent"
            })
            
            return response
        except Exception as e:
            print(f"❌ Error querying agent {agent_id}: {e}")
            return self._get_fallback_agent_response(agent_id, query, cad_analysis)
    
    def _get_fallback_agent_response(self, agent_id: str, query: str, cad_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback response for a specific agent"""
        dims = cad_analysis.get("dimensions", {}) if cad_analysis else {}
        features = cad_analysis.get("manufacturing_features", {}) if cad_analysis else {}
        
        if agent_id == "dfm_expert":
            response = f"""🛠️ **DFM Analysis:**

Based on your {dims.get('length', 0):.0f}×{dims.get('width', 0):.0f}×{dims.get('height', 0):.0f}mm part:

1. **Wall Thickness**: {'Adequate' if dims.get('thickness', 0) > 1.5 else 'Too thin - increase to 2mm minimum'}
2. **Draft Angles**: Add 1-2° draft for molding
3. **Corner Radii**: Add 0.5-1mm radius to sharp corners
4. **Ribs**: {'Well designed' if features.get('ribs', 0) < 5 else 'Too many ribs - simplify design'}

*For detailed AI-powered DFM analysis, connect to cloud backend*"""
        
        elif agent_id == "cost_estimator":
            response = f"""💰 **Cost Breakdown:**

• **Material**: ₹{max(30, dims.get('volume', 0) * 0.1):.0f}/part
• **Tooling**: ₹{150000 + (50000 if features.get('complexity_rating', 'Medium') == 'High' else 0):.0f}
• **Labor**: ₹{20 + features.get('holes', 0) * 5:.0f}/part
• **Overhead**: ₹{15 + features.get('holes', 0) * 2:.0f}/part

**Volume Price Breaks:**
• 1,000 pcs: ₹{120 + features.get('holes', 0) * 10:.0f}/part
• 10,000 pcs: ₹{80 + features.get('holes', 0) * 5:.0f}/part

*For real-time cost estimation, connect to cloud backend*"""
        
        elif agent_id == "process_planner":
            response = f"""🔧 **Process Recommendations:**

**Primary Process**: {'Injection Molding' if dims.get('thickness', 0) > 1 else 'CNC Machining'}

**Process Flow:**
1. Material preparation
2. {'Molding' if dims.get('thickness', 0) > 1 else 'Machining'}
3. {'Deflashing' if dims.get('thickness', 0) > 1 else 'Deburring'}
4. Secondary operations
5. QC inspection

**Lead Time**: {4 if dims.get('thickness', 0) > 1 else 2} weeks

*For optimized process planning, connect to cloud backend*"""
        
        elif agent_id == "material_selector":
            response = f"""🧪 **Material Recommendations:**

**Top Choices:**
1. {'ABS' if dims.get('thickness', 0) > 1 else 'Aluminum 6061'} - Best overall
2. {'Polypropylene' if dims.get('thickness', 0) > 1 else 'Delrin/POM'} - Cost effective
3. {'PC-ABS' if dims.get('thickness', 0) > 1 else 'Stainless Steel'} - Premium option

**Properties Needed:**
• Tensile Strength: {25 if dims.get('thickness', 0) > 1 else 200} MPa
• Heat Resistance: {85 if dims.get('thickness', 0) > 1 else 150}°C

*For AI-powered material selection, connect to cloud backend*"""
        
        else:
            response = "Agent not available in offline mode. Please connect to cloud backend for full capabilities."
        
        # Store in conversation history
        self.conversation_history.append({
            "query": query,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "source": "fallback_agent"
        })
        
        return {
            "agent_id": agent_id,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    
    def orchestrate_agents(self, query: str, cad_analysis: Dict[str, Any], agent_ids: List[str] = None) -> Dict[str, Any]:
        """Orchestrate multiple manufacturing agents to answer a complex query"""
        if not agent_ids:
            agent_ids = ["dfm_expert", "cost_estimator", "process_planner", "material_selector"]
        
        if not config.USE_CLOUD_BACKEND or not self.cloud_client or not self.cloud_client.connected:
            return self._get_fallback_orchestration(query, cad_analysis, agent_ids)
        
        try:
            response = self.cloud_client.orchestrate_agents(query, cad_analysis, agent_ids)
            
            # Store in conversation history
            self.conversation_history.append({
                "query": query,
                "response": response.get("summary", ""),
                "timestamp": datetime.now().isoformat(),
                "agent_ids": agent_ids,
                "source": "cloud_orchestration"
            })
            
            return response
        except Exception as e:
            print(f"❌ Error orchestrating agents: {e}")
            return self._get_fallback_orchestration(query, cad_analysis, agent_ids)
    
    def _get_fallback_orchestration(self, query: str, cad_analysis: Dict[str, Any], agent_ids: List[str]) -> Dict[str, Any]:
        """Generate fallback orchestration response"""
        responses = []
        
        for agent_id in agent_ids:
            agent_response = self._get_fallback_agent_response(agent_id, query, cad_analysis)
            responses.append(agent_response)
        
        # Generate a summary
        summary = f"""📊 **Manufacturing Analysis Summary:**

Based on analysis from multiple manufacturing experts:

1. **Design**: {'Good manufacturability' if cad_analysis.get('manufacturing_features', {}).get('moldability_score', 8) > 7 else 'Needs optimization'}
2. **Process**: {'Injection molding recommended' if cad_analysis.get('dimensions', {}).get('thickness', 0) > 1 else 'CNC machining recommended'}
3. **Material**: {'ABS or PP plastic' if cad_analysis.get('dimensions', {}).get('thickness', 0) > 1 else 'Aluminum or Delrin'}
4. **Cost**: Estimated ₹{80 + cad_analysis.get('manufacturing_features', {}).get('holes', 0) * 10:.0f}/part at 5,000 units

*For comprehensive AI-powered analysis, connect to cloud backend*"""
        
        # Store in conversation history
        self.conversation_history.append({
            "query": query,
            "response": summary,
            "timestamp": datetime.now().isoformat(),
            "agent_ids": agent_ids,
            "source": "fallback_orchestration"
        })
        
        return {
            "responses": responses,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
