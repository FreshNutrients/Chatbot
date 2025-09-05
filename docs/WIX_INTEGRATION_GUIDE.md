# 🌱 FreshNutrients Chatbot - Wix Integration Guide

*Created: July 29, 2025*  
*Version: 1.0*  
*API Base URL: `https://your-domain.com/api/v1`*

---

## 📋 Overview

This guide provides complete instructions for integrating the FreshNutrients AI Chatbot with your Wix website. The chatbot API is designed to work seamlessly with Wix's custom elements and JavaScript capabilities.

---

## 🚀 Quick Start Integration

### Step 1: Add Custom HTML Element

1. In your Wix Editor, go to **Add (+)** → **Embed** → **Custom Element**
2. Choose **HTML iframe** or **Custom Code**
3. Add the following HTML structure:

```html
<!-- FreshNutrients Chatbot Container -->
<div id="freshnutrients-chat">
    <div id="chat-header">
        <h3>🌱 FreshNutrients Assistant</h3>
        <p>Ask me about fertilizers and crop recommendations!</p>
    </div>
    
    <div id="chat-messages"></div>
    
    <div id="chat-input-container">
        <input type="text" id="chat-input" placeholder="Ask about fertilizers, crops, or farming advice...">
        <button id="send-button">Send</button>
    </div>
    
    <div id="typing-indicator" style="display: none;">
        <span>AI is typing...</span>
    </div>
</div>
```

### Step 2: Add CSS Styling

```css
#freshnutrients-chat {
    width: 100%;
    max-width: 500px;
    height: 600px;
    border: 2px solid #4CAF50;
    border-radius: 10px;
    background: #f9f9f9;
    display: flex;
    flex-direction: column;
    font-family: Arial, sans-serif;
}

#chat-header {
    background: linear-gradient(135deg, #4CAF50, #45a049);
    color: white;
    padding: 15px;
    border-radius: 8px 8px 0 0;
}

#chat-header h3 {
    margin: 0 0 5px 0;
    font-size: 18px;
}

#chat-header p {
    margin: 0;
    font-size: 12px;
    opacity: 0.9;
}

#chat-messages {
    flex: 1;
    padding: 15px;
    overflow-y: auto;
    background: white;
}

.message {
    margin-bottom: 15px;
    padding: 10px 15px;
    border-radius: 15px;
    max-width: 80%;
    word-wrap: break-word;
}

.user-message {
    background: #e3f2fd;
    margin-left: auto;
    text-align: right;
}

.ai-message {
    background: #f1f8e9;
    margin-right: auto;
    border-left: 4px solid #4CAF50;
}

.product-recommendation {
    background: #fff3e0;
    border: 1px solid #ff9800;
    border-radius: 8px;
    padding: 10px;
    margin: 10px 0;
}

.product-title {
    font-weight: bold;
    color: #e65100;
    margin-bottom: 5px;
}

.product-details {
    font-size: 14px;
    color: #666;
}

#chat-input-container {
    display: flex;
    padding: 15px;
    background: #f5f5f5;
    border-radius: 0 0 8px 8px;
}

#chat-input {
    flex: 1;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    margin-right: 10px;
}

#send-button {
    padding: 10px 20px;
    background: #4CAF50;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
}

#send-button:hover {
    background: #45a049;
}

#typing-indicator {
    padding: 10px 15px;
    font-style: italic;
    color: #666;
    background: #f0f0f0;
}
```

### Step 3: Add JavaScript Functionality

```javascript
// FreshNutrients Chatbot Integration
class FreshNutrientsChat {
    constructor() {
        this.apiBaseUrl = 'https://your-api-domain.com/api/v1';
        this.conversationId = null;
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.addWelcomeMessage();
    }
    
    setupEventListeners() {
        const sendButton = document.getElementById('send-button');
        const chatInput = document.getElementById('chat-input');
        
        sendButton.addEventListener('click', () => this.sendMessage());
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }
    
    addWelcomeMessage() {
        this.addMessage('ai', 
            "👋 Hello! I'm your FreshNutrients farming assistant. " +
            "I can help you find the right fertilizers and products for your crops. " +
            "Try asking about specific crops, application methods, or farming challenges!"
        );
    }
    
    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        input.value = '';
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Send to API
            const response = await this.callChatAPI(message);
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add AI response
            this.addMessage('ai', response.response);
            
            // Show product recommendations if available
            if (response.context_used && response.context_used.length > 0) {
                this.addProductRecommendations(response.context_used);
            }
            
            // Store conversation ID
            this.conversationId = response.conversation_id;
            
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('ai', 
                "I apologize, but I'm having trouble connecting right now. " +
                "Please try again in a moment."
            );
            console.error('Chat API error:', error);
        }
    }
    
    async callChatAPI(message) {
        const requestBody = {
            message: message,
            conversation_id: this.conversationId
        };
        
        const response = await fetch(`${this.apiBaseUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    addMessage(sender, content) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.innerHTML = this.formatMessage(content);
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    formatMessage(content) {
        // Convert URLs to clickable links
        return content.replace(
            /(https?:\/\/[^\s]+)/g, 
            '<a href="$1" target="_blank">View Document</a>'
        );
    }
    
    addProductRecommendations(products) {
        const messagesContainer = document.getElementById('chat-messages');
        
        products.slice(0, 3).forEach(product => {
            const productDiv = document.createElement('div');
            productDiv.className = 'product-recommendation';
            productDiv.innerHTML = `
                <div class="product-title">${product.product_name}</div>
                <div class="product-details">
                    <strong>Crop:</strong> ${product.crop}<br>
                    <strong>Application:</strong> ${product.application_type}<br>
                    <strong>Problem:</strong> ${product.problem}
                </div>
            `;
            messagesContainer.appendChild(productDiv);
        });
        
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    showTypingIndicator() {
        document.getElementById('typing-indicator').style.display = 'block';
    }
    
    hideTypingIndicator() {
        document.getElementById('typing-indicator').style.display = 'none';
    }
}

// Initialize the chatbot when the page loads
document.addEventListener('DOMContentLoaded', function() {
    new FreshNutrientsChat();
});
```

---

## 🔧 Advanced Configuration Options

### API Endpoints Available

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/v1/chat` | POST | Main chat interface |
| `/api/v1/session/{id}` | GET | Get session information |
| `/api/v1/conversations/{id}` | GET | Get conversation history |
| `/api/v1/products/search` | GET | Search products directly |
| `/api/v1/crops` | GET | List available crops |

### Environment Configuration

Replace `https://your-api-domain.com` with your actual API domain:

- **Development**: `http://localhost:8000`
- **Staging**: `https://staging-api.freshnutrients.com`
- **Production**: `https://api.freshnutrients.com`

### CORS Configuration

Ensure your API is configured to accept requests from your Wix domain:

```python
# In your FastAPI configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-wix-site.com", "https://www.your-wix-site.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📱 Mobile Responsive Design

Add these CSS media queries for mobile optimization:

```css
@media (max-width: 768px) {
    #freshnutrients-chat {
        height: 500px;
        max-width: 100%;
    }
    
    .message {
        max-width: 90%;
    }
    
    #chat-input-container {
        flex-direction: column;
    }
    
    #chat-input {
        margin-right: 0;
        margin-bottom: 10px;
    }
}
```

---

## 🎨 Customization Options

### Theme Colors

You can customize the chatbot colors to match your brand:

```css
:root {
    --primary-color: #4CAF50;
    --primary-dark: #45a049;
    --secondary-color: #ff9800;
    --background-color: #f9f9f9;
    --message-bg: #f1f8e9;
}
```

### Custom Welcome Message

Modify the welcome message to match your brand voice:

```javascript
addWelcomeMessage() {
    this.addMessage('ai', 
        "🌱 Welcome to FreshNutrients! I'm here to help you find the perfect " +
        "fertilizers and agricultural solutions for your specific crops and needs. " +
        "What are you growing today?"
    );
}
```

---

## 🔍 Testing Your Integration

### Test Messages to Try:

1. **Crop-specific**: "What fertilizer is best for tomatoes?"
2. **Application method**: "I need foliar spray products for avocados"
3. **Problem-based**: "My maize needs better nutrition"
4. **General**: "What products do you have for vegetables?"

### Expected Response Format:

```json
{
    "response": "Based on what you've told me, here are the FreshNutrients products suitable for...",
    "conversation_id": "uuid-string",
    "context_used": [
        {
            "product_name": "AfriKelp Plus",
            "crop": "Tomatoes & Vegetables",
            "application_type": "Foliar",
            "problem": "Plant Nutrition"
        }
    ],
    "metadata": {
        "response_time": 2.34,
        "model_used": "gpt-35-turbo",
        "products_count": 7,
        "timestamp": "2025-07-29T12:00:00"
    },
    "status": "success"
}
```

---

## 🚨 Error Handling

### Common Issues and Solutions:

1. **CORS Errors**: Ensure your domain is whitelisted in the API configuration
2. **Network Timeouts**: Implement retry logic with exponential backoff
3. **API Rate Limits**: Implement request queuing for high-traffic scenarios

### Error Handling Example:

```javascript
async callChatAPI(message, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: message,
                    conversation_id: this.conversationId
                })
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
            
        } catch (error) {
            if (i === retries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        }
    }
}
```

---

## 📊 Analytics Integration

### Track User Interactions:

```javascript
// Add to your existing chatbot class
trackEvent(eventName, properties = {}) {
    // Google Analytics 4
    if (typeof gtag !== 'undefined') {
        gtag('event', eventName, {
            custom_parameter_1: properties.conversation_id,
            custom_parameter_2: properties.message_length
        });
    }
    
    // Facebook Pixel
    if (typeof fbq !== 'undefined') {
        fbq('track', 'ChatbotInteraction', properties);
    }
}

// Use in your sendMessage method
async sendMessage() {
    // ... existing code ...
    
    this.trackEvent('chatbot_message_sent', {
        conversation_id: this.conversationId,
        message_length: message.length
    });
}
```

---

## 🔒 Security Best Practices

1. **API Key Management**: Never expose API keys in frontend code
2. **Input Validation**: Sanitize user inputs before sending to API
3. **Rate Limiting**: Implement client-side rate limiting
4. **HTTPS Only**: Always use HTTPS in production

---

## 📞 Support & Troubleshooting

### Need Help?

- **API Documentation**: Available at `https://your-domain.com/docs`
- **Test Endpoint**: Use `https://your-domain.com/api/health` to verify API status
- **Support Email**: support@freshnutrients.com

### Development Mode

For testing, you can enable debug mode:

```javascript
const DEBUG_MODE = true;

if (DEBUG_MODE) {
    console.log('Chat API Response:', response);
    console.log('Extracted Context:', response.metadata.context_extracted);
}
```

---

*Last Updated: July 29, 2025*  
*Integration Version: 1.0*  
*API Version: v1*
