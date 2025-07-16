"""
Integrated Questionnaire System for the FreeCAD Manufacturing Co-Pilot
Handles gathering manufacturing requirements from the user
"""

from typing import Dict, Any, List, Optional, Callable

# Import local modules
try:
    import config
except ImportError:
    import config

class IntegratedQuestionnaire:
    """Integrated questionnaire system that works within chat flow"""
    
    def __init__(self, chat_message_callback: Callable[[str, str], None]):
        """
        Initialize the questionnaire system
        
        Args:
            chat_message_callback: Function to call to add chat messages (role, content)
        """
        self.chat_message_callback = chat_message_callback
        self.questions = self.build_questions()
        self.current_question = 0
        self.responses = {}
        self.active = False
        
    def build_questions(self) -> List[Dict[str, Any]]:
        """Build the 8 essential questions for manufacturing context"""
        return [
            {
                "id": "application",
                "question": "🎯 **What is the specific application for this component?**",
                "options": [
                    "🚗 Automotive (vehicle parts, engine components)",
                    "🏭 Industrial Equipment (machinery, manufacturing tools)",
                    "💻 Electronics/Tech (enclosures, mounts, connectors)",
                    "🏥 Medical/Healthcare (devices, instruments)",
                    "🏠 Consumer Products (appliances, furniture)",
                    "🔧 Custom/Specialized application"
                ]
            },
            {
                "id": "production_volume",
                "question": "📊 **What is your target production volume?**",
                "options": [
                    "🖨️ Prototype/Concept (1-10 pieces)",
                    "🔬 Pilot Production (10-100 pieces)",
                    "📈 Small Batch (100-1,000 pieces)",
                    "🏭 Production (1,000-10,000 pieces)",
                    "📊 High Volume (10,000+ pieces)"
                ]
            },
            {
                "id": "business_priority",
                "question": "💼 **What is your primary business priority?**",
                "options": [
                    "💰 Cost Optimization (minimize manufacturing cost)",
                    "⏱️ Fast Time-to-Market (rapid prototyping and production)",
                    "🎯 Premium Quality (high-end finish and precision)",
                    "🌍 Local Supply Chain (Indian suppliers preferred)",
                    "🔄 Production Flexibility (easy design changes)"
                ]
            },
            {
                "id": "timeline",
                "question": "⏰ **What are your project timeline constraints?**",
                "options": [
                    "🚀 Rush Project (<4 weeks - premium costs acceptable)",
                    "⏱️ Standard Timeline (4-8 weeks - normal project)",
                    "📅 Flexible Timeline (8-12 weeks - cost optimization)",
                    "🎯 Optimal Timeline (12+ weeks - best value planning)"
                ]
            },
            {
                "id": "budget_range",
                "question": "💰 **What is your tooling budget range?**",
                "options": [
                    "💸 Minimal Budget (<₹50,000 - 3D printing/CNC)",
                    "💵 Moderate Budget (₹50K-₹2L - rapid tooling)",
                    "💴 Standard Budget (₹2L-₹5L - conventional tooling)",
                    "💶 Premium Budget (₹5L-₹10L - high-quality tooling)",
                    "💷 Unlimited Budget (>₹10L - optimal tooling)"
                ]
            },
            {
                "id": "quality_requirements",
                "question": "🔧 **What are your quality and tolerance requirements?**",
                "options": [
                    "🤷 Functional Fit Only (form and function priority)",
                    "📐 Standard Tolerances (±0.1mm - standard manufacturing)",
                    "🎯 Tight Tolerances (±0.05mm - precision manufacturing)",
                    "🔬 High Precision (±0.02mm - specialized equipment)",
                    "💎 Ultra Precision (<±0.01mm - measurement equipment)"
                ]
            },
            {
                "id": "surface_finish",
                "question": "🎨 **What are your surface finish requirements?**",
                "options": [
                    "🏭 Functional Only (no special finish requirements)",
                    "📱 Consumer Grade (smooth, professional appearance)",
                    "💎 Premium Finish (high-end appearance, polished)",
                    "🔲 Textured/Patterned (specific texture required)",
                    "🌈 Colored/Painted (specific color requirements)"
                ]
            },
            {
                "id": "manufacturing_location",
                "question": "🌍 **What is your preferred manufacturing location?**",
                "options": [
                    "🇮🇳 India - Local manufacturing (Mumbai, Bangalore, Chennai)",
                    "🌏 Asia - Cost-effective options (China, Vietnam, Thailand)",
                    "🌍 Global - Best quality regardless of location",
                    "🏠 Regional - Within 500km of my location",
                    "🤝 Hybrid - Mix of local and international suppliers"
                ]
            }
        ]
    
    def start_questionnaire(self) -> None:
        """Start the integrated questionnaire"""
        if self.active:
            return
            
        self.active = True
        self.current_question = 0
        self.responses = {}
        
        # Start with welcome message
        self.chat_message_callback("Assistant", """🎯 **Welcome to Manufacturing Requirements Gathering!**

I'll ask you 8 essential questions to understand your manufacturing needs and provide personalized recommendations.

Let's start with the first question:""")
        
        # Ask first question
        self.ask_current_question()
    
    def ask_current_question(self) -> None:
        """Ask the current question"""
        if self.current_question >= len(self.questions):
            self.complete_questionnaire()
            return
            
        question = self.questions[self.current_question]
        
        # Format question with options
        message = f"{question['question']}\n\n"
        
        for i, option in enumerate(question['options'], 1):
            message += f"**{i}.** {option}\n"
        
        message += f"\n*Please type the number (1-{len(question['options'])}) of your choice:*"
        
        self.chat_message_callback("Assistant", message)
    
    def process_response(self, response: str) -> bool:
        """
        Process user response to current question
        
        Returns:
            bool: True if the response was handled by the questionnaire, False otherwise
        """
        if not self.active:
            return False
            
        question = self.questions[self.current_question]
        
        try:
            # Try to parse as number
            choice_num = int(response.strip())
            if 1 <= choice_num <= len(question['options']):
                selected_option = question['options'][choice_num - 1]
                self.responses[question['id']] = {
                    'choice': choice_num,
                    'text': selected_option,
                    'value': self.extract_value_from_option(selected_option)
                }
                
                # Acknowledge the response
                self.chat_message_callback("Assistant", f"✅ **Selected:** {selected_option}")
                
                # Move to next question
                self.current_question += 1
                
                if self.current_question < len(self.questions):
                    self.chat_message_callback("Assistant", f"**Question {self.current_question + 1} of {len(self.questions)}:**")
                    self.ask_current_question()
                else:
                    self.complete_questionnaire()
                
                return True
            else:
                self.chat_message_callback("Assistant", f"❌ Please choose a number between 1 and {len(question['options'])}")
                return True
                
        except ValueError:
            self.chat_message_callback("Assistant", f"❌ Please enter a valid number (1-{len(question['options'])})")
            return True
    
    def extract_value_from_option(self, option: str) -> str:
        """Extract value from option text"""
        if "automotive" in option.lower():
            return "automotive"
        elif "industrial" in option.lower():
            return "industrial"
        elif "electronics" in option.lower():
            return "electronics"
        elif "medical" in option.lower():
            return "medical"
        elif "consumer" in option.lower():
            return "consumer"
        elif "prototype" in option.lower():
            return "prototype"
        elif "pilot" in option.lower():
            return "pilot"
        elif "small batch" in option.lower():
            return "small_batch"
        elif "production" in option.lower():
            return "production"
        elif "high volume" in option.lower():
            return "high_volume"
        elif "cost" in option.lower():
            return "cost"
        elif "time" in option.lower():
            return "speed"
        elif "quality" in option.lower():
            return "quality"
        elif "local" in option.lower():
            return "local"
        elif "rush" in option.lower():
            return "rush"
        elif "standard" in option.lower():
            return "standard"
        elif "flexible" in option.lower():
            return "flexible"
        elif "optimal" in option.lower():
            return "optimal"
        else:
            return option.lower().replace(" ", "_")
    
    def complete_questionnaire(self) -> None:
        """Complete the questionnaire and return user context"""
        self.active = False
        
        # Generate user context
        user_context = {
            key: value['value'] for key, value in self.responses.items()
        }
        
        # Generate summary
        summary = self.generate_summary()
        self.chat_message_callback("Assistant", f"""✅ **Manufacturing Requirements Complete!**

{summary}

🚀 **I'm now ready to provide personalized manufacturing recommendations based on your requirements!**

**Try asking me:**
• "What's the best manufacturing process for this part?"
• "Estimate the cost for my production volume"
• "Optimize my design for manufacturing"
• "Recommend Indian suppliers for my application"
""")
        
        return user_context
    
    def generate_summary(self) -> str:
        """Generate a summary of responses"""
        summary_parts = []
        
        for question_id, response in self.responses.items():
            if question_id == "application":
                summary_parts.append(f"📱 **Application:** {response['text'].split('(')[0].strip()}")
            elif question_id == "production_volume":
                summary_parts.append(f"📊 **Volume:** {response['text'].split('(')[0].strip()}")
            elif question_id == "business_priority":
                summary_parts.append(f"💼 **Priority:** {response['text'].split('(')[0].strip()}")
            elif question_id == "timeline":
                summary_parts.append(f"⏰ **Timeline:** {response['text'].split('(')[0].strip()}")
            elif question_id == "budget_range":
                summary_parts.append(f"💰 **Budget:** {response['text'].split('(')[0].strip()}")
        
        return "\n".join(summary_parts)
    
    def is_active(self) -> bool:
        """Check if the questionnaire is active"""
        return self.active
    
    def get_responses(self) -> Dict[str, Dict[str, Any]]:
        """Get all responses"""
        return self.responses
