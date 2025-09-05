"""
Response Formatter for Wix Integration

This module cleans up and formats AI responses to be more user-friendly 
for the Wix website integration, removing technical jargon and system prompts.
"""

import re
from typing import Dict, Any, List

class WixResponseFormatter:
    """Formats AI responses for better user experience on Wix."""
    
    @staticmethod
    def format_for_wix(response: str, metadata: Dict[str, Any] = None) -> str:
        """
        Clean and format AI response for Wix users.
        
        Args:
            response: Raw AI response text
            metadata: Response metadata for additional context
            
        Returns:
            Formatted response suitable for Wix display
        """
        if not response:
            return "I apologize, but I couldn't generate a response. Please try again."
        
        # Clean up technical system prompts and markers
        cleaned_response = WixResponseFormatter._remove_system_content(response)
        
        # Format based on content type
        if WixResponseFormatter._is_product_response(cleaned_response):
            return WixResponseFormatter._format_product_response(cleaned_response, metadata)
        elif WixResponseFormatter._is_advice_response(cleaned_response):
            return WixResponseFormatter._format_advice_response(cleaned_response)
        else:
            return WixResponseFormatter._format_general_response(cleaned_response)
    
    @staticmethod
    def _remove_system_content(text: str) -> str:
        """Remove technical system prompts and internal markers."""
        # Simple string replacements instead of complex regex
        text = text.replace('🕐 TIMING QUESTION DETECTED', '')
        text = text.replace('REQUIRED RESPONSE FORMAT:', '')
        text = text.replace('📊 CONTEXT ANALYSIS:', '')
        text = text.replace('DEBUG:', '')
        
        # Remove common system emojis
        emojis_to_remove = ['🕐', '📊', '🌾', '⚠️', '✅', '❌', '🎯', '💡']
        for emoji in emojis_to_remove:
            text = text.replace(emoji + ' ', '')
            text = text.replace(emoji, '')
        
        return text.strip()
    
    @staticmethod
    def _is_product_response(text: str) -> bool:
        """Check if response contains product recommendations."""
        product_indicators = [
            'freshnutrients',
            'product:',
            'products that match',
            'recommended products',
            'following products',
            'application rate',
            'npk'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in product_indicators)
    
    @staticmethod
    def _is_advice_response(text: str) -> bool:
        """Check if response contains farming advice."""
        advice_indicators = [
            'application',
            'timing',
            'recommend',
            'apply',
            'growing stage',
            'soil condition',
            'best practice'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in advice_indicators)
    
    @staticmethod
    def _format_product_response(text: str, metadata: Dict[str, Any] = None) -> str:
        """Format product recommendation responses."""
        # Start with a friendly header
        formatted = "🌱 **FreshNutrients Product Recommendations**\n\n"
        
        # Extract and clean product information
        cleaned_text = WixResponseFormatter._clean_markdown_formatting(text)
        
        # Add the main response content
        formatted += cleaned_text
        
        # Add helpful next steps if products were found
        if metadata and metadata.get('products_count', 0) > 0:
            formatted += "\n\n💡 **Need More Specific Guidance?**\n"
            formatted += "For detailed application instructions and timing, please let me know:\n"
            formatted += "• Your preferred application method (foliar spray or soil application)\n"
            formatted += "• Current growth stage of your crops\n"
            formatted += "• Any specific challenges you're facing\n"
        
        return formatted
    
    @staticmethod
    def _format_advice_response(text: str) -> str:
        """Format farming advice responses."""
        formatted = "🎯 **Agricultural Guidance**\n\n"
        
        # Clean and add the advice content
        cleaned_text = WixResponseFormatter._clean_markdown_formatting(text)
        formatted += cleaned_text
        
        # Add safety reminder for application advice
        if any(word in text.lower() for word in ['apply', 'application', 'spray', 'fertilize']):
            formatted += "\n\n⚠️ **Safety Reminder**: Always follow product label instructions and use appropriate protective equipment."
        
        return formatted
    
    @staticmethod
    def _format_general_response(text: str) -> str:
        """Format general conversational responses."""
        # For general responses, just clean up formatting
        return WixResponseFormatter._clean_markdown_formatting(text)
    
    @staticmethod
    def _clean_markdown_formatting(text: str) -> str:
        """Clean up markdown and improve readability."""
        # Simple replacements instead of complex regex
        text = text.replace('\n-', '\n• ')
        text = text.replace('\n*', '\n• ')
        
        # Clean up excessive newlines
        text = text.replace('\n\n\n', '\n\n')
        text = text.replace('\n\n\n\n', '\n\n')
        
        # Remove any remaining system markers
        emojis_to_remove = ['📊', '🌾', '⚠️', '✅', '❌', '🎯', '💡', '🕐']
        for emoji in emojis_to_remove:
            text = text.replace(emoji + ' ', '')
            text = text.replace(emoji, '')
        
        return text.strip()
    
    @staticmethod
    def format_error_response(error_message: str = None) -> str:
        """Format error responses for user-friendly display."""
        if error_message:
            return f"I apologize, but I'm experiencing technical difficulties. Please try again in a moment.\n\nIf the problem persists, please contact our support team."
        return "I'm having trouble processing your request right now. Please try rephrasing your question or try again shortly."
    
    @staticmethod
    def add_conversation_context(response: str, has_previous_context: bool = False) -> str:
        """Add conversation context hints if helpful."""
        if has_previous_context and not any(word in response.lower() for word in ['previous', 'earlier', 'continue']):
            return response + "\n\n💬 *I'm keeping track of our conversation context to provide better recommendations.*"
        return response
