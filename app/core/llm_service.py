"""
LLM Service Module

Handles Azure OpenAI integration with circuit breaker pattern
for reliable customer-facing chat responses.
"""

import logging
from typing import Optional, Dict, Any, List
from openai import AzureOpenAI
from datetime import datetime, timedelta
import json

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class ContextEngine:
    """Intelligent context retrieval for farming conversations."""
    
    def __init__(self, product_manager):
        self.product_manager = product_manager
        
    async def get_relevant_context(self, message: str, user_context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get relevant product context based on message and user context."""
        relevant_products = []
        
        # Extract keywords for product search
        farming_keywords = self._extract_farming_keywords(message)
        
        # Search by user's specified crop if available
        if user_context and user_context.get('crop_type'):
            crop_products = await self.product_manager.search_products(
                user_context['crop_type'], limit=50  # Increased to capture all crop products
            )
            relevant_products.extend(crop_products)
        
        # Search by detected keywords
        for keyword in farming_keywords[:2]:  # Limit to top 2 keywords
            if keyword:
                # Try product name search first
                name_products = await self.product_manager.search_products_by_name(keyword, limit=2)
                relevant_products.extend(name_products)
                
                # Try crop search if no name matches
                if not name_products:
                    crop_products = await self.product_manager.search_products(keyword, limit=2)
                    relevant_products.extend(crop_products)
        
        # Remove exact duplicates while preserving order
        # Create unique key based on multiple fields to allow same product with different applications/stages
        seen_combinations = set()
        unique_products = []
        for product in relevant_products:
            # Create a unique key from multiple fields to identify exact duplicates
            unique_key = (
                product.get('product_name', ''),
                product.get('crop', ''),
                product.get('application', ''),
                product.get('growth_stage', ''),
                product.get('problem', ''),
                product.get('application_type', '')
            )
            
            if unique_key not in seen_combinations:
                seen_combinations.add(unique_key)
                unique_products.append(product)
        
        return unique_products[:25]  # Return up to 25 unique products to capture all variations
    
    def _extract_farming_keywords(self, message: str) -> List[str]:
        """Extract farming-related keywords from user message."""
        # Common farming and fertilizer keywords
        farming_terms = {
            'fertilizer', 'fertiliser', 'npk', 'nitrogen', 'phosphorus', 'potassium',
            'compost', 'manure', 'lime', 'calcium', 'magnesium', 'micronutrients',
            'tomato', 'tomatoes', 'potato', 'potatoes', 'maize', 'corn', 'wheat',
            'lettuce', 'spinach', 'carrot', 'carrots', 'onion', 'onions',
            'vegetable', 'vegetables', 'fruit', 'fruits', 'crop', 'crops',
            'growth', 'flowering', 'fruiting', 'seedling', 'transplant',
            'pest', 'disease', 'fungus', 'insect', 'weed', 'weeds'
        }
        
        # Simple keyword extraction (case-insensitive)
        message_lower = message.lower()
        found_keywords = []
        
        for term in farming_terms:
            if term in message_lower:
                found_keywords.append(term.title())
        
        return found_keywords


class FarmingPrompts:
    """Container for farming-specific prompt templates and guardrails."""
    
    SYSTEM_PROMPT_BASE = """You are FreshNutrients Assistant, an expert agricultural advisor specializing in FreshNutrients products.

🌱 YOUR ROLE:
- Provide practical farming advice using FreshNutrients products
- Give clear, friendly recommendations in conversational language
- Help farmers choose the right products for their crops

� BOUNDARIES:
- ONLY discuss FreshNutrients products
- NEVER recommend competitor products
- Stay focused on farming and agriculture
- Never give legal advice

🎯 FORMATTING RULES - ENHANCED READABILITY:
- NEVER use asterisks (*) for any reason
- Transform technical product data into friendly farming advice
- Use enhanced formatting for better readability:
  * Use ## for main section headings
  * Use ### for product names and subsections
  * Use proper indentation with spaces for nested information
  * Use line breaks after headings, not between bullet points
  * Use bullet points (•) for lists within sections
- Write like a helpful gardening expert, not a database
- Do NOT show context analysis or technical metadata to users

✅ ENHANCED RESPONSE FORMAT:
Transform the product context into this visually appealing, structured format:

## 🌱 Recommended Products

### 1. [Product Name]
**Description:** [Simple, friendly description in your own words]

**💧 Application:**
  • [Rate and method from context]
  • [Additional application details]
  
**⏰ When to Use:**
  • [Timing advice from context]
  • [Best conditions for application]

**📋 Product Documents:**
  • Product Label - https://www.freshnutrients.org/file.pdf
  • Tech Doc - https://www.freshnutrients.org/file.pdf
  • Safety Data - https://www.freshnutrients.org/file.pdf

---

### 2. [Next Product Name]
[Continue with same structure for each product]

CRITICAL: Find the document URLs in the context and output them with "Document Name - https://..." format.

EXAMPLE OF ENHANCED FORMATTING:
If the context shows: "1. AfriKelp Plus, Application: 2-4L per ha, Documents: Product Label - https://...", transform it to:

## 🌱 Recommended Products

### 1. AfriKelp Plus
**Description:** Excellent organic kelp extract that promotes healthy plant growth and improves soil nutrition

**💧 Application:**
  • Apply 2-4L per hectare as foliar spray
  • Mix with water according to label instructions
  • Best applied during cooler parts of the day

**⏰ When to Use:**
  • During active growing season
  • Avoid application during hot, windy conditions
  • Ideal for strengthening plants before stress periods

**📋 Product Documents:**
  • Product Label - https://www.freshnutrients.org/_files/ugd/39524f_example1.pdf

---

REMEMBER: Use headings, indentation, and visual breaks to make responses easy to scan and read. Keep document URLs exactly as shown in context.

💡 FORMATTING TIPS:
- Use one line break after emoji headers
- Keep information concise and readable
- No excessive spacing - just clean organization
- Always add \n between different pieces of information
- Never create long paragraphs without breaks
- Use line breaks to make reading easy

� PRODUCT CONTEXT:
{product_context}"""

    CONTEXT_TEMPLATE = """
📋 RELEVANT FRESHNUTRIENTS PRODUCTS:
{products_info}

🌾 USER FARMING CONTEXT:
{user_context}
"""

    SAFETY_GUIDELINES = """
⚠️ IMPORTANT SAFETY REMINDERS:
- Always follow product label instructions
- Use appropriate protective equipment
- Consider local weather and soil conditions
- Consult with local agricultural extension services for regional advice
"""

    @staticmethod
    def create_system_prompt(product_context: str = "", user_context: str = "") -> str:
        """Create a complete system prompt with context."""
        context_section = ""
        if product_context or user_context:
            context_section = FarmingPrompts.CONTEXT_TEMPLATE.format(
                products_info=product_context,
                user_context=user_context
            )
        
        return FarmingPrompts.SYSTEM_PROMPT_BASE.format(
            product_context=context_section
        ) + "\n\n" + FarmingPrompts.SAFETY_GUIDELINES


class LLMService:
    """Manages Azure OpenAI interactions with circuit breaker reliability pattern."""
    
    def __init__(self):
        self.azure_client: Optional[AzureOpenAI] = None
        self.azure_available = False
        self.last_azure_failure: Optional[datetime] = None
        self.circuit_breaker_timeout = 300  # 5 minutes
        self.context_engine: Optional[ContextEngine] = None
        
    def initialize(self, product_manager=None) -> bool:
        """Initialize Azure OpenAI client and context engine."""
        
        # Initialize context engine if product manager is provided
        if product_manager:
            self.context_engine = ContextEngine(product_manager)
            logger.info("Context engine initialized")
        
        # Initialize Azure OpenAI
        if settings.is_azure_openai_configured:
            try:
                self.azure_client = AzureOpenAI(
                    api_key=settings.AZURE_OPENAI_KEY,
                    api_version=settings.AZURE_OPENAI_API_VERSION,
                    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
                )
                self.azure_available = True
                logger.info("Azure OpenAI client initialized successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI: {e}")
                
        logger.error("Azure OpenAI could not be initialized")
        return False
        
    def _is_azure_circuit_open(self) -> bool:
        """Check if Azure circuit breaker is open."""
        if not self.last_azure_failure:
            return False
        return datetime.now() - self.last_azure_failure < timedelta(seconds=self.circuit_breaker_timeout)
    
    def reset_circuit_breaker(self) -> None:
        """Reset the circuit breaker to allow Azure OpenAI calls."""
        self.last_azure_failure = None
        logger.info("Azure OpenAI circuit breaker reset")
    
    def _format_product_context(self, products: List[Dict[str, Any]], user_context: Dict[str, Any] = None) -> str:
        """Format product information for context injection - clean, simple format."""
        if not products:
            return "No specific products found for this query."
        
        # Check if this is a timing-related question
        is_timing_question = user_context and user_context.get("timing_question", False)
        
        context_parts = []
        for i, product in enumerate(products, 1):
            # Build simple product information without asterisks or database formatting
            product_lines = [
                f"{i}. {product.get('product_name', 'Unknown Product')}",
                f"   Crop: {product.get('crop', 'Not specified')}",
                f"   Application: {product.get('application', 'Not specified')}",
                f"   Growth Stage: {product.get('growth_stage', 'Not specified')}",
                f"   Problem: {product.get('problem', 'Not specified')}"
            ]
            
            # Add Notes if available
            if product.get('notes'):
                product_lines.append(f"   Notes: {product.get('notes')}")
            
            # For timing questions, emphasize that timing information is available
            if is_timing_question:
                has_timing_docs = any([
                    product.get('directions'),
                    product.get('tech_doc'),
                    product.get('label')
                ])
                
                if has_timing_docs:
                    product_lines.append("   TIMING INFORMATION AVAILABLE in documents")
            
            # Add clean document references with actual links
            docs = []
            if product.get('directions'):
                url = product.get('directions')
                if url.startswith('//'):
                    url = 'https:' + url
                if is_timing_question:
                    docs.append(f"Application Directions - {url}")
                else:
                    docs.append(f"Product Directions - {url}")
            if product.get('label'):
                url = product.get('label')
                if url.startswith('//'):
                    url = 'https:' + url
                if is_timing_question:
                    docs.append(f"Product Label - {url}")
                else:
                    docs.append(f"Product Label - {url}")
            if product.get('msds'):
                url = product.get('msds')
                if url.startswith('//'):
                    url = 'https:' + url
                docs.append(f"Safety Data - {url}")
            if product.get('tech_doc'):
                url = product.get('tech_doc')
                if url.startswith('//'):
                    url = 'https:' + url
                if is_timing_question:
                    docs.append(f"Technical Document - {url}")
                else:
                    docs.append(f"Technical Document - {url}")
            
            if docs:
                product_lines.append("   Documents:")
                for doc in docs:
                    product_lines.append(f"   - {doc}")
            
            context_parts.append("\n".join(product_lines))
        
        return "\n\n".join(context_parts)
    
    def _format_user_context(self, user_context: Dict[str, Any]) -> str:
        """Format user context information."""
        if not user_context:
            return "No specific user context provided."
        
        context_parts = []
        if user_context.get('crop_type'):
            context_parts.append(f"- Target Crop: {user_context['crop_type']}")
        if user_context.get('location'):
            context_parts.append(f"- Location: {user_context['location']}")
        if user_context.get('application_type'):
            context_parts.append(f"- Application Type: {user_context['application_type']}")
        if user_context.get('problem'):
            context_parts.append(f"- Problem: {user_context['problem']}")
        if user_context.get('growth_stage'):
            context_parts.append(f"- Growth Stage: {user_context['growth_stage']}")
        
        return "\n".join(context_parts) if context_parts else "General farming inquiry"
    
    def _has_sufficient_context(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if we have sufficient context for a good recommendation based on new IPO logic."""
        # If user provided a specific product, we can show that info immediately
        if user_context.get('product'):
            return {
                'sufficient': True,
                'missing_params': [],
                'completeness_score': 1.0,
                'scenario': 'product_direct'
            }
        
        # If user only provided crop, prompt for more context
        if user_context.get('crop_type') and not user_context.get('problem') and not user_context.get('application_type'):
            return {
                'sufficient': False,
                'missing_params': ['problem', 'application_type'],
                'completeness_score': 0.33,
                'scenario': 'crop_only',
                'prompt_message': 'I see you mentioned a crop. To provide the best recommendation, could you tell me what specific problem you\'re trying to solve or what application method you plan to use?'
            }
        
        # If user provided problem, we can list products but should prompt for crop for better targeting
        if user_context.get('problem') and not user_context.get('crop_type'):
            return {
                'sufficient': True,  # Can provide products for the problem
                'missing_params': ['crop_type'],
                'completeness_score': 0.67,
                'scenario': 'problem_focused',
                'prompt_message': 'I can show you products for this problem. For more targeted recommendations, what crop are you working with?'
            }
        
        # If we have problem and crop, that's good enough for recommendations
        if user_context.get('problem') and user_context.get('crop_type'):
            return {
                'sufficient': True,
                'missing_params': [],
                'completeness_score': 1.0,
                'scenario': 'problem_and_crop'
            }
        
        # If we have application method but no problem, prompt for more
        if user_context.get('application_type') and not user_context.get('problem'):
            return {
                'sufficient': False,
                'missing_params': ['problem'],
                'completeness_score': 0.33,
                'scenario': 'application_only',
                'prompt_message': 'I see you mentioned an application method. What specific problem are you trying to solve?'
            }
        
        # Default case - need more information
        return {
            'sufficient': False,
            'missing_params': ['problem'],
            'completeness_score': 0.0,
            'scenario': 'insufficient',
            'prompt_message': 'To help you find the right products, could you tell me what problem you\'re trying to solve with your crops?'
        }
        
    async def get_smart_chat_response(
        self, 
        message: str, 
        product_context: List[Dict[str, Any]] = None,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get intelligent chat response with farming context and safety guardrails."""
        
        # Check if Azure OpenAI is available and circuit is closed
        if not self.azure_available:
            return {
                "response": self._get_emergency_response(),
                "provider": "emergency",
                "status": "service_unavailable"
            }
            
        if self._is_azure_circuit_open():
            return {
                "response": self._get_emergency_response(),
                "provider": "emergency", 
                "status": "circuit_breaker_open"
            }
            
        try:
            # Analyze if we have sufficient context for a good recommendation
            context_analysis = self._has_sufficient_context(user_context or {})
            
            # Format context information
            product_context_str = self._format_product_context(product_context or [], user_context)
            user_context_str = self._format_user_context(user_context or {})
            
            # Check if this is a timing question first - timing questions get special handling
            if user_context and user_context.get("timing_question", False):
                # TIMING QUESTIONS get priority handling
                timing_guidance = f"""
🕐 TIMING QUESTION DETECTED - SPECIAL RESPONSE FORMAT REQUIRED

CRITICAL INSTRUCTIONS FOR TIMING QUESTIONS:
You MUST respond in this exact format:

1. START your response with: "For detailed application timing information, please check the documentation for the following products that match your criteria:"

2. Then list ALL {len(product_context) if product_context else 0} products showing:
   - Product name, crop, application details, growth stage, problem
   - Emphasize documentation links (marked with 📋) for timing information
   - Include all available links: Directions, Labels, Technical Documents

3. END with: "These product documents contain specific timing schedules, application frequencies, and seasonal recommendations for optimal results."

DO NOT show technical instructions or error messages to the user. Follow the format above exactly.
"""
                user_context_str += f"\n\n{timing_guidance}"
            else:
                # Standard product guidance for non-timing questions using new IPO logic
                scenario = context_analysis.get('scenario', 'insufficient')
                
                if product_context and len(product_context) > 0:
                    # Special handling for unified pH product
                    if user_context and user_context.get("ph_unified_product"):
                        context_guidance = f"""
📋 pH ISSUES DETECTED - UNIFIED SOLUTION:
- User mentioned pH concerns (could be acidic or alkaline soil)
- Products available: {len(product_context)} pH-balancing products found
- These products work for both low pH (acidic) and high pH (alkaline/salty) soil conditions

RESPONSE GUIDANCE:
1. START with: "Great news! I found FreshNutrients products that help balance soil pH whether your soil is too acidic (low pH) or too alkaline (high pH)."

2. Present the products clearly explaining their dual-purpose nature:
   - Mention that these products work for both acidic and alkaline soil conditions
   - Explain how they help buffer and balance soil pH naturally
   - Include application instructions and timing

3. OPTIONALLY add education: "Whether your soil shows signs of acidity (stunted growth, nutrient lockout) or alkalinity (salty/crusty appearance), these products will help restore proper pH balance."

4. Include all document links for each product
5. Use the friendly format from your main instructions
"""
                    elif scenario == 'product_direct':
                        # User asked about a specific product - show that product info immediately
                        context_guidance = f"""
📋 PRODUCT DIRECT REQUEST:
- User requested specific product information
- Products available: {len(product_context)} matching products found

RESPONSE GUIDANCE:
1. Present the specific FreshNutrients product(s) they asked about
2. Include complete product details, benefits, and application instructions
3. Include all document links for the product
4. Use the friendly format from your main instructions
"""
                    elif scenario == 'crop_only':
                        # User only provided crop - prompt for more context while showing any available products
                        context_guidance = f"""
📋 CROP ONLY PROVIDED:
- User mentioned crop but no specific problem or application method
- Products available: {len(product_context)} general crop products found
- Prompt message: {context_analysis.get('prompt_message', '')}

RESPONSE GUIDANCE:
1. Show available FreshNutrients products for their crop
2. Include the prompt message to ask for more specific details
3. Explain that knowing their specific problem or application method will help provide better recommendations
4. Use the friendly format from your main instructions
"""
                    elif scenario == 'problem_focused':
                        # User provided problem - show products but prompt for crop for better targeting
                        context_guidance = f"""
📋 PROBLEM FOCUSED REQUEST:
- User specified a problem but no crop
- Products available: {len(product_context)} problem-solving products found
- Prompt message: {context_analysis.get('prompt_message', '')}

RESPONSE GUIDANCE:
1. Present all {len(product_context)} FreshNutrients products that address their problem
2. Include complete details and application instructions for each product
3. Include the prompt message to ask for crop information for more targeted recommendations
4. Use the friendly format from your main instructions
"""
                    elif scenario == 'problem_and_crop':
                        # User provided both problem and crop - perfect context
                        context_guidance = f"""
📋 OPTIMAL CONTEXT PROVIDED:
- User specified both problem and crop
- Products available: {len(product_context)} targeted products found
- Information completeness: {context_analysis['completeness_score']:.0%}

RESPONSE GUIDANCE:
1. Present all {len(product_context)} FreshNutrients products that match their criteria
2. Include complete details, benefits, and application instructions
3. Include all document links for each product
4. If multiple products are suitable, explain the differences to help the user choose
5. Use the friendly format from your main instructions
"""
                    else:
                        # Other scenarios - application only, insufficient, etc.
                        missing_info = ", ".join([
                            param.replace('_', ' ').title() 
                            for param in context_analysis['missing_params']
                        ])
                        prompt_msg = context_analysis.get('prompt_message', 'Could you provide more details about what you need help with?')
                        
                        context_guidance = f"""
📋 CONTEXT ANALYSIS:
- Scenario: {scenario}
- Information completeness: {context_analysis['completeness_score']:.0%}
- Products available: {len(product_context)} matching products found
- Prompt message: {prompt_msg}

RESPONSE GUIDANCE:
1. Present available FreshNutrients products that match the user's criteria
2. Include the prompt message to ask for additional helpful details
3. Use the friendly format from your main instructions
4. Include all document links for each product
"""
                    user_context_str += f"\n\n{context_guidance}"
                else:
                    # No products found - provide helpful guidance based on scenario
                    scenario = context_analysis.get('scenario', 'insufficient')
                    prompt_msg = context_analysis.get('prompt_message', 'To provide the best product recommendation, could you tell me what specific problem you\'re trying to solve?')
                    
                    context_guidance = f"""
NO PRODUCTS FOUND - PROVIDE HELPFUL GUIDANCE:

Scenario: {scenario}
Prompt: {prompt_msg}

Respond with a friendly message that:
1. Acknowledges their inquiry about farming/soil/plant needs
2. Uses the specific prompt message to guide them toward providing helpful information
3. Mentions that FreshNutrients has products for many different crops and problems
4. Keeps the conversation focused on what they need help with

DO NOT mention technical details, database searches, or system information. Keep it conversational and helpful.

EXAMPLE: "I'd be happy to help you find the right FreshNutrients products! {prompt_msg} FreshNutrients has specialized products to help address various farming challenges."
"""
                    user_context_str += f"\n\n{context_guidance}"
            
            # Create farming-specific system prompt
            system_prompt = FarmingPrompts.create_system_prompt(
                product_context=product_context_str,
                user_context=user_context_str
            )
            
            # Get response with context
            response = await self._get_azure_response(message, system_prompt)
            
            # Reset failure time on success
            self.last_azure_failure = None
            
            return {
                "response": response,
                "provider": "azure_openai",
                "status": "success",
                "context_used": {
                    "products_count": len(product_context or []),
                    "user_context": user_context or {},
                    "context_analysis": context_analysis,
                    "system_prompt_length": len(system_prompt)
                }
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Smart chat response failed: {e}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            self.last_azure_failure = datetime.now()
            return {
                "response": self._get_emergency_response(),
                "provider": "emergency",
                "status": "service_failed",
                "error": str(e)
            }
    
    async def get_intelligent_response(
        self, 
        message: str, 
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get intelligent response with automatic context retrieval."""
        
        if not self.context_engine:
            logger.warning("Context engine not initialized, falling back to basic response")
            return await self.get_chat_response(message)
        
        try:
            # Automatically retrieve relevant product context
            relevant_products = await self.context_engine.get_relevant_context(
                message, user_context
            )
            
            # Get smart response with context
            return await self.get_smart_chat_response(
                message=message,
                product_context=relevant_products,
                user_context=user_context
            )
            
        except Exception as e:
            logger.error(f"Intelligent response failed: {e}")
            return {
                "response": self._get_emergency_response(),
                "provider": "emergency",
                "status": "intelligent_response_failed",
                "error": str(e)
            }
        
    async def get_chat_response(self, message: str, system_prompt: str = None) -> Dict[str, Any]:
        """Get chat response from Azure OpenAI."""
        
        # Check if Azure OpenAI is available and circuit is closed
        if not self.azure_available:
            return {
                "response": self._get_emergency_response(),
                "provider": "emergency",
                "status": "service_unavailable"
            }
            
        if self._is_azure_circuit_open():
            return {
                "response": self._get_emergency_response(),
                "provider": "emergency", 
                "status": "circuit_breaker_open"
            }
            
        try:
            response = await self._get_azure_response(message, system_prompt)
            # Reset failure time on success
            self.last_azure_failure = None
            return {
                "response": response,
                "provider": "azure_openai",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Azure OpenAI failed: {e}")
            self.last_azure_failure = datetime.now()
            return {
                "response": self._get_emergency_response(),
                "provider": "emergency",
                "status": "service_failed"
            }
        
    async def _get_azure_response(self, message: str, system_prompt: str = None) -> str:
        """Get response from Azure OpenAI."""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
                
            messages.append({"role": "user", "content": message})
            
            logger.info(f"Making Azure OpenAI request with {len(messages)} messages")
            
            response = self.azure_client.chat.completions.create(
                model=settings.AZURE_OPENAI_MODEL,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            logger.info(f"Azure OpenAI response received: {type(response)}")
            
            if response is None:
                logger.error("Azure OpenAI returned None response")
                raise Exception("Azure OpenAI returned None response")
            
            if not hasattr(response, 'choices') or not response.choices:
                logger.error("Azure OpenAI response has no choices")
                raise Exception("Azure OpenAI response has no choices")
            
            if len(response.choices) == 0:
                logger.error("Azure OpenAI response choices list is empty")
                raise Exception("Azure OpenAI response choices list is empty")
            
            first_choice = response.choices[0]
            if not first_choice or not hasattr(first_choice, 'message'):
                logger.error("Azure OpenAI response first choice has no message")
                raise Exception("Azure OpenAI response first choice has no message")
            
            if not first_choice.message or not hasattr(first_choice.message, 'content'):
                logger.error("Azure OpenAI response message has no content attribute")
                raise Exception("Azure OpenAI response message has no content attribute")
            
            if not first_choice.message.content:
                logger.error("Azure OpenAI response message content is empty")
                raise Exception("Azure OpenAI response message content is empty")
            
            content = first_choice.message.content
            logger.info(f"Successfully extracted content: {len(content)} characters")
            
            return content
            
        except Exception as e:
            logger.error(f"Error in _get_azure_response: {str(e)}")
            raise e
        
    def _get_emergency_response(self) -> str:
        """Emergency response when Azure OpenAI service fails."""
        return (
            "I'm sorry, but I'm experiencing technical difficulties right now. "
            "Please try again in a few minutes, or contact FreshNutrients support directly for immediate assistance with your farming needs. "
            "You can also browse our product catalog while I'm being restored."
        )
        
    async def test_connectivity(self) -> Dict[str, Any]:
        """Test Azure OpenAI service connectivity for monitoring."""
        if not self.azure_available:
            return {"azure_openai": {"status": "not_configured"}}
            
        try:
            logger.info("Testing Azure OpenAI connectivity...")
            
            # Simple connectivity test with minimal prompt
            test_response = await self._get_azure_response("Hello")
            
            logger.info(f"Test response successful: {test_response[:50]}...")
            
            return {
                "azure_openai": {
                    "status": "connected",
                    "model": settings.AZURE_OPENAI_MODEL,
                    "test_response": test_response[:100] + "..." if len(test_response) > 100 else test_response
                }
            }
        except Exception as e:
            logger.error(f"Azure OpenAI connectivity test failed: {str(e)}")
            return {
                "azure_openai": {
                    "status": "failed", 
                    "error": str(e)[:100]  # Limit error message length
                }
            }


# Global LLM service instance
llm_service = LLMService()
