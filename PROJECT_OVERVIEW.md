# 🌱 FreshNutrients AI Chatbot - Project Overview & Implementation Plan

*Created: July 7, 2025*  
*Project Type: AI-Powered Chat API for Wix Website*  
*Target: Azure-hosted backend serving FreshNutrients product knowledge*

---

## 📋 Project Summary

**Objective**: Build an AI-powered chat assistant API that integrates with your Wix website to provide intelligent, context-aware responses about FreshNutrients products and farming applications using data from your existing Azure database.

**Key Goals**:
- ✅ Answer product-specific questions using Azure database context
- ✅ Provide practical, farming-focused suggestions  
- ✅ Maintain strict product knowledge boundaries
- ✅ Log conversations for analysis and improvement
- ✅ Integrate seamlessly with Wix frontend

**Current Status**: 🚧 **In Development** - Core functionality implemented with Railway test deployment active

---

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Wix Website   │───▶│  Chat API       │───▶│  Azure SQL DB   │
│  (Frontend UI)  │    │  (FastAPI)      │    │  (Product Data) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Azure OpenAI  │
                       │   (LLM Service) │
                       └─────────────────┘
```

### Technology Stack Decision
- **Backend Framework**: FastAPI (Python) - High performance, async, excellent OpenAPI docs
- **Database**: Azure SQL Database (your existing setup)
- **LLM Service**: Azure OpenAI (preferred) or OpenAI API
- **Hosting**: Azure Container Apps or Azure Functions
- **Frontend Integration**: RESTful API with CORS support for Wix

---

## 📊 Implementation Phases

### Phase 1: Foundation Setup ✅ **COMPLETED**
**Status**: ✅ **COMPLETED** - July 7, 2025

#### 1.1 Environment & Project Structure
- [x] Set up Python virtual environment
- [x] Create FastAPI project structure
- [x] Configure development environment
- [x] Set up version control (Git)

#### 1.2 Core Dependencies
- [x] Install FastAPI, Uvicorn, Pydantic
- [x] Add Azure SQL Database connectors (pymssql)
- [x] Install Azure OpenAI SDK
- [x] Configure environment variables management

#### 1.3 Basic API Framework
- [x] Create main FastAPI application
- [x] Implement health check endpoints
- [x] Set up CORS for Wix integration
- [x] Configure logging system

**Deliverables**:
- ✅ Working FastAPI server
- ✅ Health check endpoint
- ✅ Environment configuration

---

### Phase 2: Database Integration ✅ **COMPLETED**
**Status**: ✅ **COMPLETED** - July 9, 2025

#### Key Achievements
- ✅ Successfully connected to Azure SQL Database `FNProducts`
- ✅ Created comprehensive database manager with connection pooling
- ✅ Implemented product search and retrieval functions
- ✅ Created and deployed ChatLogs table automatically
- ✅ Added debug endpoints for database inspection

**Current API Endpoints Available**:
- `GET /` - Root health check
- `GET /health` - Detailed system health
- `GET /debug/status` - Development monitoring
- `GET /api/products/search?q={query}` - Search products by name
- `GET /api/products/search-by-crop?q={query}` - Search by crop type
- `GET /api/products/{product_name}` - Get specific product
- `GET /api/crops` - List all available crops

---

### Phase 3: LLM Integration ✅ **COMPLETED**
**Status**: ✅ **COMPLETED** - July 16, 2025

#### Key Achievements
- ✅ Successfully integrated Azure OpenAI with gpt-35-turbo model
- ✅ Created robust LLMService class with circuit breaker pattern
- ✅ Implemented error handling and emergency responses
- ✅ **NEW**: Implemented FarmingPrompts class with agricultural guardrails
- ✅ **NEW**: Created ContextEngine for intelligent product recommendation
- ✅ **NEW**: Added automatic keyword extraction and context retrieval
- ✅ **ENHANCED**: Fixed AI response logic to show ALL available products first
- ✅ **OPTIMIZED**: Removed unnecessary database query limits 
- ✅ **IMPROVED**: Added product deduplication to prevent duplicate recommendations

---

### Phase 4: Chat API Development ✅ **COMPLETED**
**Status**: ✅ **COMPLETED** - July 29, 2025

#### 4.1 Core Chat Endpoints ✅ COMPLETED
- ✅ `/api/v1/chat` - Main chat interface with context extraction
- ✅ `/api/v1/conversations/{id}` - Conversation management
- ✅ `/api/v1/session/{id}` - Enhanced session management
- ✅ Request/response model validation

#### Key Achievements
- ✅ **MAJOR MILESTONE**: Production chat endpoints fully implemented
- ✅ Automatic context extraction from user messages (crops, application types, problems)
- ✅ Enhanced conversation management with unique session IDs
- ✅ **CRITICAL FIX**: Resolved context mapping to match actual database crop names
- ✅ **CRITICAL FIX**: Resolved AI hallucination of non-existent products  
- ✅ Integration with existing database and LLM services

---

### Phase 5: Security & Production Readiness ✅ **COMPLETED**
**Status**: ✅ **COMPLETED** - August 7, 2025

#### Key Achievements
- ✅ **API AUTHENTICATION**: Bearer token authentication with configurable API keys
- ✅ **RATE LIMITING**: 100 requests/hour per client with IP-based identification
- ✅ **INPUT VALIDATION**: Comprehensive sanitization against XSS and injection attacks
- ✅ **SECURITY MIDDLEWARE**: HTTPS enforcement, security headers, trusted host validation
- ✅ **PERFORMANCE MONITORING**: Real-time CPU, memory, response time tracking
- ✅ **ADMIN ENDPOINTS**: `/admin/health`, `/admin/metrics`, `/admin/analytics`, `/admin/config`
- ✅ **DOCKER CONTAINERIZATION**: Production-ready container with health checks
- ✅ **AZURE DEPLOYMENT**: Container Apps deployment scripts with secrets management

---

### Phase 6: IPO Framework Intelligence & User Experience ✅ **COMPLETED**
**Status**: ✅ **COMPLETED** - September 1, 2025

#### Key Achievements
- ✅ **INTELLIGENT BEHAVIOR**: Fixed crop-only queries to prompt for more information
- ✅ **pH EXPERTISE**: Advanced pH problem detection with classification for soil acidity, salinity, and general pH issues
- ✅ **UNIFIED APPROACH**: Single product handling for items that address multiple pH-related problems
- ✅ **CONTEXT AWARENESS**: Enhanced message parsing with better pattern matching
- ✅ **DUPLICATE ELIMINATION**: Sophisticated deduplication preventing the same product appearing multiple times

---

### Phase 7: Railway Test Deployment 🎯 **CURRENT FOCUS**
**Status**: 🎯 **IN PROGRESS** - September 5, 2025

#### 7.1 Test Deployment Setup ✅ COMPLETED
- ✅ **Railway Platform**: Successfully deployed to Railway cloud platform
- ✅ **Database Connection**: Azure SQL Database connectivity verified from Railway
- ✅ **Azure OpenAI**: LLM service fully functional in cloud environment
- ✅ **API Endpoints**: All chat and debug endpoints accessible
- ✅ **HTML Interfaces**: Test interfaces updated for Railway URLs

#### 7.2 Test Environment Validation
- ✅ **Live URL**: `https://chatbot-production-7bf1.up.railway.app`
- ✅ **Health Checks**: Database and LLM services operational
- ✅ **Chat Interface**: `/chat_test_interface.html` - functional test interface
- ✅ **API Endpoints**: `/api/v1/chat` - main chat functionality working
- ✅ **Debug Tools**: `/debug/status`, `/debug/db-test` - system monitoring active

**Purpose**: This Railway deployment serves as a **test environment only** for validating functionality before Azure production deployment.

---

### Phase 8: Response Formatting & Advanced Features 🔄 **NEXT PRIORITY**
**Status**: 🔄 **PENDING** - Target: September 2025

#### 8.1 LLM-Based Response Formatting 
- 🎯 **STRATEGY**: Format responses at the LLM level (system prompt) rather than post-processing
- ✅ **PROBLEM IDENTIFIED**: Current responses show all technical data but lack user-friendly structure
- 🔄 **SOLUTION**: Enhance system prompt to include formatting instructions for conversational, organized responses

#### 8.2 User-Friendly Response Structure
- [ ] Add conversational tone instructions to system prompt
- [ ] Create response templates with sections (🌱 Recommended Products, 📋 Application Guide, ⏰ Timing)
- [ ] Implement visual hierarchy with emojis and clear headings
- [ ] Make responses read like helpful gardening advice, not technical specifications

---

### Phase 9: Comprehensive Testing & Validation 🔄 **PLANNED**
**Status**: 🔄 **PLANNED** - Target: September 2025

#### 9.1 Stress Testing
- [ ] API load testing (concurrent requests)
- [ ] Database connection pool testing
- [ ] Memory leak detection
- [ ] Rate limiting validation

#### 9.2 Security Testing
- [ ] Authentication bypass attempts
- [ ] Input injection testing (SQL, XSS, LDAP)
- [ ] API key brute force protection
- [ ] CORS policy validation

#### 9.3 Edge Case Testing
- [ ] Malformed request handling
- [ ] Database connection failures
- [ ] LLM service outages
- [ ] Invalid conversation IDs
- [ ] Extremely long messages

---

### Phase 10: Production Deployment & Integration 🔄 **PLANNED**
**Status**: 🔄 **PLANNED** - Target: October 2025

#### 10.1 Azure Production Deployment
- [ ] Deploy to Azure Container Apps
- [ ] Configure Azure Application Gateway
- [ ] Set up custom domain
- [ ] SSL certificate configuration

#### 10.2 Wix Integration
- [ ] Create Wix Custom Element
- [ ] Implement chat UI components
- [ ] Test cross-origin requests
- [ ] Mobile responsiveness

#### 10.3 Go-Live
- [ ] Production deployment
- [ ] Monitoring setup
- [ ] Documentation handover

---

## 📁 Project Structure

```
freshnutrients-chatbot/
├── 📁 app/
│   ├── 📄 __init__.py
│   ├── 📄 main.py              # FastAPI application
│   ├── 📄 config.py            # Configuration management
│   ├── 📄 models.py            # Pydantic models
│   ├── 📁 api/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 chat.py          # Chat endpoints
│   │   └── 📄 health.py        # Health check endpoints
│   ├── 📁 core/
│   │   ├── 📄 database.py      # Database connection & queries
│   │   ├── 📄 llm_service.py   # LLM integration
│   │   └── 📄 security.py      # Authentication & security
│   └── 📁 utils/
│       ├── 📄 logging.py       # Logging configuration
│       └── 📄 helpers.py       # Utility functions
├── 📁 tests/
│   ├── 📄 test_api.py          # API endpoint tests
│   ├── 📄 test_database.py     # Database tests
│   └── 📄 test_llm.py          # LLM service tests
├── 📁 deployment/
│   ├── 📄 Dockerfile           # Container configuration
│   ├── 📄 docker-compose.yml   # Local development
│   └── 📄 azure-deploy.yml     # Azure deployment
├── 📁 docs/
│   ├── 📄 api-specification.md # API documentation
│   ├── 📄 wix-integration.md   # Wix integration guide
│   └── 📄 deployment-guide.md  # Deployment instructions
├── 📄 requirements.txt         # Python dependencies
├── 📄 .env.example            # Environment variables template
├── 📄 .gitignore              # Git ignore rules
└── 📄 README.md               # Project documentation
```

---

## 🔧 Technical Specifications

### API Endpoints Design

#### Main Chat Endpoint
```http
POST /api/v1/chat
Content-Type: application/json

{
  "message": "What fertilizer is best for tomatoes?",
  "conversation_id": "uuid-optional",
  "user_context": {
    "location": "South Africa",
    "crop_type": "vegetables"
  }
}
```

**Response**:
```json
{
  "response": "For tomatoes, I recommend FreshNutrients' NPK 2:3:2 fertilizer...",
  "conversation_id": "uuid",
  "context_used": [
    {
      "product_id": "BIO001",
      "product_name": "NPK 2:3:2 Fertilizer",
      "relevance_score": 0.95
    }
  ],
  "metadata": {
    "response_time": 1.2,
    "model_used": "gpt-4",
    "category": "fertilizer_recommendation"
  }
}
```

### Database Schema Extensions

#### ChatLogs Table
```sql
CREATE TABLE ChatLogs (
    id INT IDENTITY(1,1) PRIMARY KEY,
    conversation_id UNIQUEIDENTIFIER,
    user_message NVARCHAR(MAX),
    ai_response NVARCHAR(MAX),
    context_products NVARCHAR(MAX), -- JSON array of product IDs
    category NVARCHAR(100),
    timestamp DATETIME2 DEFAULT GETDATE(),
    response_time_ms INT,
    user_context NVARCHAR(MAX) -- JSON object
);
```

### LLM Prompt Template
```python
SYSTEM_PROMPT = """
You are a FreshNutrients agricultural assistant. You ONLY provide advice about FreshNutrients products and their farming applications.

STRICT GUIDELINES:
- Only discuss FreshNutrients products and their uses
- Focus on practical farming applications
- Do NOT provide general farming, medical, or legal advice
- If asked about non-FreshNutrients products, redirect to FreshNutrients alternatives
- Always be helpful and professional

AVAILABLE CONTEXT:
{product_context}

USER LOCATION: {user_location}
CROP TYPE: {crop_type}
"""
```

---

## 🧪 Testing Strategy

### Development Testing
- **Unit Tests**: Each component tested independently
- **Integration Tests**: Database + LLM integration
- **API Tests**: All endpoints with various scenarios
- **Security Tests**: Authentication and validation

### User Testing
- **Accuracy Tests**: Verify AI responses match product data
- **Boundary Tests**: Ensure AI stays within FreshNutrients scope
- **Performance Tests**: Response times under load
- **Wix Integration Tests**: Frontend integration works smoothly

---

## 🚀 Deployment Strategy

### Development Environment
- Local FastAPI server with hot reload
- Local Azure SQL Database connection
- Environment variables for configuration
- Docker for consistent development

### Staging Environment
- Azure Container Apps deployment
- Staging database with test data
- Full integration testing
- Performance monitoring

### Production Environment
- Azure Container Apps with auto-scaling
- Production Azure SQL Database
- Custom domain with SSL
- Comprehensive monitoring and logging

---

## 📋 Success Criteria

### Technical Metrics
- ✅ API response time < 2 seconds (95th percentile)
- ✅ 99.9% uptime availability
- ✅ Zero data leakage between conversations
- ✅ All responses stay within FreshNutrients product scope

### Business Metrics
- ✅ Accurate product recommendations (>90% relevance)
- ✅ User satisfaction with chat responses
- ✅ Reduced support ticket volume
- ✅ Increased product page engagement

---

## 📞 Next Steps

### **IMMEDIATE PRIORITY** (Phase 7 - Response Formatting & Advanced Features)
1. **LLM-Based Formatting**: Enhance system prompts for user-friendly response structure
2. **Response Templates**: Create conversational response patterns with visual hierarchy
3. **Quality Enhancement**: Test formatting while maintaining technical accuracy

### **SHORT TERM** (Phase 8 - Comprehensive Testing)
4. **Stress Testing**: Load testing, concurrent requests, database connection limits
5. **Security Testing**: Authentication, input validation, injection attempts
6. **Edge Case Testing**: Malformed requests, service failures, Unicode handling
7. **End-to-End Testing**: Full conversation flows, context accuracy, admin functions

### **MEDIUM TERM** (Phase 9 - Deployment)
8. **Azure Deployment**: Container Apps, custom domain, SSL configuration
9. **Wix Integration**: Chat widget, frontend testing, mobile responsiveness

### **LONG TERM** (Production Optimization)
10. **Monitoring & Analytics**: Usage tracking, performance monitoring, cost management
11. **CI/CD Pipeline**: Automated testing, deployment automation
12. **User Feedback**: Load testing, user acceptance testing, feedback collection

**Current Status**: ✅ Phase 6 complete with IPO framework intelligence and pH detection. Ready for response formatting enhancement.

---

## 📝 Progress Tracking

### Development Log
- **July 7, 2025**: Project overview created, Phase 1 completed - FastAPI server running
- **July 9, 2025**: Phase 2 completed - Azure SQL integration, product search, chat logging
- **July 16, 2025**: Phase 3 completed - Azure OpenAI integration with smart prompts and context injection
- **July 29, 2025**: Phase 4 completed - Production chat endpoints with context extraction and conversation management
- **August 7, 2025**: Phase 5 completed - Security, monitoring, containerization, and Azure deployment scripts
- **September 1, 2025**: Phase 6 completed - IPO framework intelligence and advanced pH detection system
- **September 5, 2025**: **Railway Test Deployment** - Successfully deployed working chatbot to Railway for testing
  - ✅ Live test environment: `https://chatbot-production-7bf1.up.railway.app`
  - ✅ Database connectivity verified from cloud environment
  - ✅ Azure OpenAI integration functional in production
  - ✅ Chat interface accessible and operational
  - ✅ All debug and monitoring endpoints active

### Issue Tracking
- **July 16, 2025**: AI only showing 5 products instead of all available - **RESOLVED**
- **July 16, 2025**: Duplicate products in AI responses - **RESOLVED**
- **July 24, 2025**: Context mapping to match database crop names - **RESOLVED**
- **July 24, 2025**: AI hallucination of non-existent products - **RESOLVED**
- **September 5, 2025**: Railway deployment URL mismatch in HTML interfaces - **RESOLVED**

---

*This document will be updated throughout the project to reflect progress, decisions, and any changes to the implementation plan.*
