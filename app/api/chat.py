"""
Chat API Endpoints

This module implements the production chat API endpoints for FreshNutrients.
Provides the main chat interface that will be integrated with the Wix website.
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import uuid
import time
import logging
from datetime import datetime

from ..core.database import product_manager, chat_log_manager
from ..core.llm_service import llm_service
from ..core.security import verify_api_key, sanitize_input, RequestValidator
from ..config import settings
from ..utils.logging import get_logger
from ..utils.wix_formatter import WixResponseFormatter

logger = get_logger(__name__)

# Create the chat router
router = APIRouter(prefix="/api/v1", tags=["chat"])


# Request/Response Models
class ChatMessage(BaseModel):
    """Chat message request model."""
    message: str = Field(..., min_length=1, max_length=1000, description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for session continuity")
    user_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional user context")
    
    @validator('message')
    def validate_message(cls, v):
        """Validate and sanitize message content."""
        return sanitize_input(v, max_length=1000)
    
    @validator('conversation_id')
    def validate_conversation_id(cls, v):
        """Validate conversation ID format."""
        if v is not None and not RequestValidator.validate_conversation_id(v):
            raise ValueError("Invalid conversation ID format")
        return v


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="AI response")
    conversation_id: str = Field(..., description="Conversation ID")
    context_used: List[Dict[str, Any]] = Field(default_factory=list, description="Products used in response")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")
    status: str = Field(default="success", description="Response status")


class ConversationSummary(BaseModel):
    """Conversation summary model."""
    conversation_id: str
    message_count: int
    created_at: datetime
    last_message_at: datetime
    category: Optional[str] = None


class SessionInfo(BaseModel):
    """Session information model."""
    conversation_id: str
    session_active: bool
    message_count: int
    last_activity: datetime
    extracted_context: Dict[str, Any]
    recommendations_given: int


# Utility Functions
def extract_context_from_message(message: str) -> Dict[str, Any]:
    """
    Extract farming context from user message using keyword detection.
    Enhanced to detect products, problems, application methods, and crops.
    """
    import re
    context = {}
    message_lower = message.lower()
    
    # Common FreshNutrients products - check for direct product mentions
    products = [
        "afrikelp plus", "afrikelp", "kelp plus", "afrikelp+",
        "blac-mag", "blacmag", "blac mag", 
        "aquamate", "aqua mate", "aqua-mate",
        "calsap",    
    ]
    
    # Check for direct product mentions
    for product in products:
        if product in message_lower:
            if product in ["afrikelp plus", "afrikelp", "kelp plus", "afrikelp+"]:
                context["product_name"] = "AfriKelp Plus"
            elif product in ["blac-mag", "blacmag", "blac mag"]:
                context["product_name"] = "BlaC-Mag"
            elif product in ["aquamate", "aqua mate", "aqua-mate"]:
                context["product_name"] = "AquaMate"
            elif product in ["calsap"]:
                context["product_name"] = "Calsap"
            else:
                context["product_name"] = product.title()
            break
    
    # Common crops - ordered with more specific terms first to avoid false matches  
    crops = [
        # Specific multi-word crops first
        "soybeans", "soybean", "macadamias", "macadamia", "avocados", "avocado", 
        "seedlings", "seedling", "pecans", "pecan", "subtropicals", "subtropical",
        # Specific single crops
        "tomatoes", "tomato", "potatoes", "potato", "tobacco", "maize", "corn", "wheat", 
        "lettuce", "cabbage", "onions", "onion", "carrots", "carrot", "spinach",
        "apples", "apple", "pears", "pear", "peaches", "peach", "plums", "plum",
        "cherries", "cherry", "grapes", "grape", "oranges", "orange", "lemons", "lemon",
        "grass", "pasture", "barley", "citrus", "deciduous", "nursery", "transplants", "transplant",
        # Generic terms last - but use word boundaries to avoid false matches
        "vegetables", "veggie", "fruits", "fruit", "avos", 
        "soyas", "soya", "legumes", "legume", "beans", "bean", "peas", "pea"
    ]
    
    # Special handling for "nuts" to avoid false matches with "nutrition"
    # Only match "nuts" or "nut" when they appear as whole words
    if re.search(r'\b(nuts|nut)\b', message_lower):
        context["crop_type"] = "Pecan Nuts"
    else:
        # Extract crop type using word boundaries for better accuracy
        for crop in crops:
            if re.search(r'\b' + re.escape(crop) + r'\b', message_lower):
                if crop in ["vegetables", "veggie"]:
                    context["crop_type"] = "Tomatoes & Vegetables"
                elif crop in ["tomato", "tomatoes"]:
                    context["crop_type"] = "Tomatoes & Vegetables"
                elif crop in ["potato", "potatoes"]:
                    context["crop_type"] = "Potatoes"
                elif crop in ["grass", "pasture"]:
                    context["crop_type"] = "Grass pastures"
                elif crop in ["tobacco"]:
                    context["crop_type"] = "Field Tobacco"
                elif crop in ["maize", "corn"]:
                    context["crop_type"] = "Maize & Wheat"
                elif crop in ["wheat"]:
                    context["crop_type"] = "Maize & Wheat"
                elif crop in ["apple", "apples", "pear", "pears", "peach", "peaches", "plum", "plums", 
                             "cherry", "cherries", "grape", "grapes", "citrus", "orange", "oranges", 
                             "lemon", "lemons", "deciduous", "fruit", "fruits"]:
                    context["crop_type"] = "Deciduous Fruit"
                elif crop in ["macadamia", "macadamias", "avocado", "avocados", "avos", "subtropical", "subtropicals"]:
                    context["crop_type"] = "Macadamias & Avos (Other Subtropicals)"
                elif crop in ["pecan", "pecans"]:
                    context["crop_type"] = "Pecan Nuts"
                elif crop in ["seedling", "seedlings", "nursery", "transplant", "transplants"]:
                    context["crop_type"] = "Seedlings (Tobacco included)"
                elif crop in ["soya", "soyas", "soybean", "soybeans", "legume", "legumes", "bean", "beans", "pea", "peas"]:
                    context["crop_type"] = "Soyas and other legumes"
                else:
                    context["crop_type"] = crop.capitalize()
                break
    
    # Application types
    applications = {
        "foliar": ["foliar", "spray", "spraying", "leaf", "leaves"],
        "soil": ["soil", "ground", "root", "roots", "planting"],
        "water": ["water", "irrigation", "irrigate", "hydroponic"]
    }
    
    # Problems/needs - mapping to actual database problem names
    # Enhanced pH detection and classification
    def classify_ph_issue(message_lower):
        """Classify pH-related queries into specific problem categories."""
        import re
        
        # Indicators for high pH/alkaline issues (Soil Salinity)
        high_ph_indicators = [
            "alkaline", "alkalinity", "high ph", "ph too high", "ph is high",
            "salty soil", "salt problems", "high salinity", "lime needs",
            "ph above", "ph over", "basic soil"
        ]
        
        # Indicators for low pH/acidic issues (Soil Acidity)  
        low_ph_indicators = [
            "acidic", "acidity", "acid soil", "low ph", "ph too low", "ph is low",
            "sour soil", "ph below", "ph under", "acidic soil"
        ]
        
        # Generic pH terms that need clarification - using word boundaries
        generic_ph_patterns = [
            r'\bph\b',           # Match "ph" as whole word only
            r'\bph level\b', 
            r'\bph levels\b', 
            r'\bph balance\b', 
            r'\bph imbalance\b', 
            r'\bph testing\b', 
            r'\bph meter\b', 
            r'\bsoil ph\b', 
            r'\bph adjustment\b'
        ]
        
        # Check for specific pH issues first
        if any(indicator in message_lower for indicator in high_ph_indicators):
            return "Soil Salinity"  # High pH/alkaline
        elif any(indicator in message_lower for indicator in low_ph_indicators):
            return "Soil Acidity"   # Low pH/acidic
        elif any(re.search(pattern, message_lower) for pattern in generic_ph_patterns):
            return "pH Issues"      # Generic pH concern - needs both problems
        
        return None
    
    # Enhanced problems mapping with pH detection
    # Made more specific to avoid false positives like "nutrition" triggering on general terms
    problems = {
        "Plant Nutrition": ["plant nutrition", "nutrient deficiency", "nutrients needed", "feeding program", "npk requirements", "nutritional needs", "nutrition of"],
        "Fertilizer Efficiency": ["fertilizer efficiency", "efficient fertilizer", "effectiveness of fertilizer", "improve efficiency"],
        "Soil Health": ["disease control", "disease prevention", "fungus control", "pest control", "pest management", "health problems", "soil health"],
        "Soil Salinity": ["soil salinity", "salt problems", "salty soil", "high salinity", "alkaline soil", "alkaline", "high ph", "ph too high"],
        "Soil Acidity": ["soil acidity", "acid soil", "acidic soil", "low ph", "ph too low", "sour soil"],
        "Irrigation efficiency": ["irrigation efficiency", "water efficiency", "watering efficiency", "irrigation problems"],
        "Shelf life management": ["shelf life", "storage life", "preservation", "post harvest"]
    }
    
    # Timing-related questions - detect when user is asking about application timing
    timing_keywords = [
        "timing", "when should", "what time", "schedule", "frequency", "interval", "how often",
        "application timing", "spray timing", "fertilizer timing", "season", "seasonal",
        "before planting", "after planting", "during growing", "monthly", "weekly", "daily", 
        "days apart", "weeks apart", "months apart", "how many times"
    ]
    
    # Extract application type
    for app_type, keywords in applications.items():
        if any(keyword in message_lower for keyword in keywords):
            context["application_type"] = app_type.title()
            break
    
    # Enhanced problem/need extraction with pH classification
    # First check for pH-related queries using smart classification
    ph_problem = classify_ph_issue(message_lower)
    if ph_problem:
        if ph_problem == "pH Issues":
            # Generic pH issue - mark for dual-problem search
            context["ph_issues"] = True
            context["problem"] = "pH Issues"  # Special marker for dual search
        else:
            # Specific pH issue (Soil Acidity or Soil Salinity)
            context["problem"] = ph_problem
    else:
        # Regular problem detection for non-pH issues
        for problem, keywords in problems.items():
            if any(keyword in message_lower for keyword in keywords):
                context["problem"] = problem  # Use exact database problem name
                break
    
    # Detect timing-related questions
    timing_question = any(keyword in message_lower for keyword in timing_keywords)
    if timing_question:
        context["timing_question"] = True
        context["question_type"] = "timing"
    
    return context


async def get_relevant_products(context: Dict[str, Any], conversation_id: str = None) -> List[Dict[str, Any]]:
    """Get relevant products based on extracted context and conversation history."""
    products = []
    
    # 1. If specific product mentioned, search for that product first
    if context.get("product_name"):
        products = await product_manager.search_products_by_name(context["product_name"])
        if products:
            return products  # Return immediately for direct product queries
    
    # 2. Problem-based search (can work without crop)
    if context.get("problem"):
        if context.get("problem") == "pH Issues":
            # Special case: Generic pH issue - search for both Soil Acidity and Soil Salinity
            acidity_products = await product_manager.search_products_by_criteria(
                crop=context.get("crop_type"),
                application_type=context.get("application_type"),
                problem="Soil Acidity"
            )
            salinity_products = await product_manager.search_products_by_criteria(
                crop=context.get("crop_type"),
                application_type=context.get("application_type"),
                problem="Soil Salinity"
            )
            
            # Combine and remove duplicates (same product listed under both problems)
            all_ph_products = acidity_products + salinity_products
            
            # Remove duplicates based on product name and key details
            seen_products = set()
            unique_products = []
            for product in all_ph_products:
                # Create unique key based on product name and application details
                unique_key = (
                    product.get('product_name', ''),
                    product.get('crop', ''),
                    product.get('application', ''),
                    product.get('growth_stage', ''),
                    product.get('application_type', '')
                )
                
                if unique_key not in seen_products:
                    seen_products.add(unique_key)
                    unique_products.append(product)
            
            products = unique_products
            # Mark context for special pH handling in LLM response  
            context["ph_unified_product"] = True
        else:
            # Regular single-problem search
            products = await product_manager.search_products_by_criteria(
                crop=context.get("crop_type"),  # Can be None
                application_type=context.get("application_type"),
                problem=context.get("problem")
            )
        
        # If we have products from problem search, return them
        if products:
            return products
    
    # 3. Crop-based search (when crop is provided with other context)
    if context.get("crop_type"):
        # Only search for products if we have more than just the crop
        # If we only have crop_type, return empty list to trigger prompting logic
        has_only_crop = (
            context.get("crop_type") and 
            not context.get("problem") and 
            not context.get("application_type") and
            not context.get("product_name")
        )
        
        if not has_only_crop:
            # We have crop + additional context, so search for products
            products = await product_manager.search_products_by_criteria(
                crop=context.get("crop_type"),
                application_type=context.get("application_type"),
                problem=context.get("problem")
            )
            
            # If no specific matches, fall back to general crop search
            if not products:
                products = await product_manager.search_products(context["crop_type"])
        # If has_only_crop is True, products remains empty list to trigger prompting
    
    # 4. Application method search (when only application method provided)
    elif context.get("application_type"):
        products = await product_manager.search_products_by_criteria(
            application_type=context.get("application_type")
        )
    
    # Enhance products with conversation context if available
    if conversation_id and products:
        try:
            # Get recent conversation history to understand user preferences
            recent_history = await chat_log_manager.get_chat_history(conversation_id, limit=3)
            
            # Analyze previous interactions to refine product selection
            if recent_history:
                logger.debug(f"Found {len(recent_history)} previous messages in conversation")
                # Could implement preference learning here in the future
                
        except Exception as e:
            logger.warning(f"Could not retrieve conversation history: {e}")
    
    # Remove exact duplicates while preserving variations
    # Create unique key based on multiple fields to allow same product with different applications/stages
    seen_combinations = set()
    unique_products = []
    for product in products:
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

    return unique_products


# API Endpoints
@router.post("/chat", response_model=ChatResponse)
async def chat(
    message: ChatMessage, 
    request: Request,
    api_key: str = Depends(verify_api_key) if settings.ENABLE_API_AUTH else None
) -> ChatResponse:
    """
    Main chat endpoint for FreshNutrients AI assistant.
    
    This endpoint processes user messages and returns intelligent responses
    about FreshNutrients products and farming applications.
    """
    start_time = time.time()
    
    try:
        # Generate conversation ID if not provided
        conversation_id = message.conversation_id or str(uuid.uuid4())
        
        # Extract context from message
        extracted_context = extract_context_from_message(message.message)
        
        # Try to get previous conversation context for continuity
        conversation_context = {}
        try:
            if conversation_id:
                # Get recent conversation history to maintain context
                recent_history = await chat_log_manager.get_chat_history(conversation_id, limit=5)
                if recent_history:
                    # Accumulate context from all previous messages (oldest to newest)
                    for entry in reversed(recent_history):  # Process in chronological order
                        if entry and entry.get("user_message"):
                            entry_context = extract_context_from_message(entry["user_message"])
                            if entry_context:
                                # Update with each message's context (newer messages override older ones)
                                conversation_context.update(entry_context)
                    
                    logger.debug(f"Retrieved accumulated conversation context: {conversation_context}")
                        
        except Exception as e:
            logger.warning(f"Could not retrieve conversation context: {e}")
        
        # Merge contexts: new message context overrides conversation context
        combined_context = {**conversation_context, **extracted_context, **message.user_context}
        
        logger.info(f"Processing chat message for conversation {conversation_id}")
        logger.debug(f"Message context: {extracted_context}")
        logger.debug(f"Conversation context: {conversation_context}")
        logger.debug(f"Combined context: {combined_context}")
        
        # Get relevant products
        products = await get_relevant_products(combined_context, conversation_id)
        
        logger.info(f"Found {len(products)} relevant products")
        
        # Get AI response
        ai_result = await llm_service.get_smart_chat_response(
            message=message.message,
            product_context=products,
            user_context=combined_context
        )
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Prepare context_used for response
        context_used = []
        for product in products[:10]:  # Limit to first 10 for metadata
            product_info = {
                "product_name": product.get("product_name"),
                "crop": product.get("crop"),
                "application_type": product.get("application_type"),
                "problem": product.get("problem")
            }
            
            # Add document URLs if they exist
            documents = {}
            if product.get("directions"):
                documents["Product Directions"] = product.get("directions")
                logger.info(f"Found directions URL: {product.get('directions')}")
            if product.get("label"):
                documents["Product Label"] = product.get("label")
                logger.info(f"Found label URL: {product.get('label')}")
            if product.get("msds"):
                documents["Safety Data"] = product.get("msds")
                logger.info(f"Found MSDS URL: {product.get('msds')}")
            if product.get("tech_doc"):
                documents["Technical Document"] = product.get("tech_doc")
                logger.info(f"Found tech doc URL: {product.get('tech_doc')}")
            
            if documents:
                product_info["documents"] = documents
                logger.info(f"Product {product.get('product_name')} has {len(documents)} documents")
            else:
                logger.info(f"Product {product.get('product_name')} has NO documents")
            
            context_used.append(product_info)
        
        # Get conversation history for metadata
        try:
            current_history = await chat_log_manager.get_chat_history(conversation_id, limit=10)
            history_count = len(current_history)
        except Exception as e:
            logger.warning(f"Could not get history count: {e}")
            history_count = 0
        
        # Prepare metadata
        metadata = {
            "response_time": round(response_time, 2),
            "model_used": "gpt-35-turbo",
            "products_count": len(products),
            "context_extracted": extracted_context,
            "conversation_context": conversation_context,
            "combined_context": combined_context,
            "conversation_id": conversation_id,
            "history_count": history_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log the conversation
        try:
            await chat_log_manager.log_chat_interaction(
                session_id=conversation_id,
                user_message=message.message,
                bot_response=ai_result.get("response", ""),
                category="product_recommendation",
                product_context=str(context_used),
                response_time=int(response_time * 1000),  # Convert to milliseconds
                user_ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
        except Exception as e:
            logger.error(f"Failed to log chat interaction: {e}")
            # Don't fail the request if logging fails
        
        # Return raw response temporarily for debugging
        raw_response = ai_result.get("response", "I apologize, but I'm unable to provide a response at the moment.")
        # formatted_response = WixResponseFormatter.format_for_wix(raw_response, metadata)
        
        # Create response
        response = ChatResponse(
            response=raw_response,
            conversation_id=conversation_id,
            context_used=context_used,
            metadata=metadata,
            status="success" if ai_result.get("status") == "success" else "partial"
        )
        
        logger.info(f"Chat response generated successfully in {response_time:.2f}s")
        return response
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        
        # Return error response
        # error_response = WixResponseFormatter.format_error_response(str(e))
        return ChatResponse(
            response="I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
            conversation_id=message.conversation_id or str(uuid.uuid4()),
            context_used=[],
            metadata={
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error"
            },
            status="error"
        )


@router.get("/session/{conversation_id}", response_model=SessionInfo)
async def get_session_info(conversation_id: str) -> SessionInfo:
    """
    Get comprehensive session information for a conversation.
    Useful for maintaining context across interactions.
    """
    try:
        # Get conversation history
        history = await chat_log_manager.get_chat_history(conversation_id, limit=50)
        
        # Analyze conversation for context
        extracted_context = {}
        recommendations_given = 0
        
        if history:
            # Get the most recent message to extract current context
            latest_message = history[0] if history else None
            if latest_message and latest_message.get("user_message"):
                extracted_context = extract_context_from_message(latest_message["user_message"])
            
            # Count recommendations (messages with product context)
            recommendations_given = sum(1 for entry in history 
                                     if entry.get("product_context") and entry["product_context"] != "[]")
        
        return SessionInfo(
            conversation_id=conversation_id,
            session_active=len(history) > 0,
            message_count=len(history),
            last_activity=history[0]["timestamp"] if history else datetime.utcnow(),
            extracted_context=extracted_context,
            recommendations_given=recommendations_given
        )
        
    except Exception as e:
        logger.error(f"Error retrieving session info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session information")


@router.post("/session/context", response_model=Dict[str, Any])
async def update_session_context(
    conversation_id: str, 
    context_update: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update session context manually (for advanced integrations).
    Allows Wix frontend to provide additional context.
    """
    try:
        # In a full implementation, we'd store this context
        # For now, we'll return the merged context
        
        logger.info(f"Context update for session {conversation_id}: {context_update}")
        
        return {
            "conversation_id": conversation_id,
            "updated_context": context_update,
            "status": "success",
            "message": "Session context updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating session context: {e}")
        raise HTTPException(status_code=500, detail="Failed to update session context")


@router.get("/conversations/{conversation_id}", response_model=List[Dict[str, Any]])
async def get_conversation_history(conversation_id: str) -> List[Dict[str, Any]]:
    """
    Get conversation history for a specific conversation ID.
    """
    try:
        history = await chat_log_manager.get_chat_history(conversation_id, limit=50)
        
        # Format history for response
        formatted_history = []
        for entry in history:
            formatted_history.append({
                "message_id": entry["log_id"],
                "user_message": entry["user_message"],
                "ai_response": entry["bot_response"],
                "timestamp": entry["timestamp"].isoformat() if entry["timestamp"] else None,
                "category": entry["category"]
            })
        
        return formatted_history
        
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation history")


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(limit: int = 20) -> List[ConversationSummary]:
    """
    List recent conversations (for development/debugging purposes).
    """
    try:
        # This would need to be implemented in chat_log_manager
        # For now, return empty list
        return []
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list conversations")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str) -> Dict[str, str]:
    """
    Delete a conversation (for privacy/GDPR compliance).
    """
    try:
        # This would need to be implemented in chat_log_manager
        # For now, just return success
        return {"message": f"Conversation {conversation_id} deletion requested"}
        
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")
