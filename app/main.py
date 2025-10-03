"""
FastAPI Main Application

This module initializes the FastAPI application with all necessary
middleware, routes, and configuration for the FreshNutrients AI chat API.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os
from contextlib import asynccontextmanager

from .config import settings
from .models import HealthResponse
from .core.database import db_manager, chat_log_manager, product_manager
from .core.llm_service import llm_service
from .core.security import SecurityMiddleware, RateLimitMiddleware
from .utils.monitoring import performance_monitor
from .api import chat
from .api import admin

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting FreshNutrients AI Chat API...")
    
    # Initialize database connection
    db_initialized = await db_manager.initialize()
    if db_initialized:
        logger.info("Database initialized successfully")
        # Create chat logs table
        await chat_log_manager.create_chat_logs_table()
    else:
        logger.error("Failed to initialize database")
    
    # Initialize LLM service
    llm_initialized = llm_service.initialize(product_manager)
    if llm_initialized:
        logger.info("LLM service initialized successfully")
    else:
        logger.warning("LLM service initialization failed - check configuration")
    
    logger.info("FreshNutrients AI Chat API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FreshNutrients AI Chat API...")
    
    # Close database connections
    await db_manager.close()
    
    logger.info("FreshNutrients AI Chat API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="AI-powered chat API for FreshNutrients speciality fertilizers and farming advice",
    lifespan=lifespan
)

# Mount static files - serve HTML interface files from root directory
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)))
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Route for chat test interface
@app.get("/chat_test_interface.html")
async def chat_test_interface():
    """Serve the chat test interface HTML file."""
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat_test_interface.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="Chat test interface not found")

# Add security middleware (order matters!)
# Add monitoring middleware first
from starlette.middleware.base import BaseHTTPMiddleware
import time

class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        response_time = time.time() - start_time
        
        # Record the request
        performance_monitor.record_request(
            endpoint=request.url.path,
            method=request.method,
            response_time=response_time,
            status_code=response.status_code
        )
        
        return response

app.add_middleware(MonitoringMiddleware)

if settings.ENABLE_HTTPS_REDIRECT:
    app.add_middleware(SecurityMiddleware)

if settings.ENABLE_RATE_LIMITING:
    app.add_middleware(RateLimitMiddleware)

# Add trusted host middleware for production
# Temporarily disabled for Railway debugging
# if settings.ENVIRONMENT == "production":
#     app.add_middleware(
#         TrustedHostMiddleware, 
#         allowed_hosts=["freshnutrients.com", "*.freshnutrients.com", "*.railway.app", "*.up.railway.app", "localhost"]
#     )

# Configure CORS for Wix integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "FreshNutrients AI Chat API is running",
        "version": settings.API_VERSION,
        "status": "healthy"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Check database connection
        db_info = await db_manager.get_database_info()
        db_connected = db_info.get("status", "unknown") == "connected"
        
        # Check LLM service status
        llm_configured = llm_service.azure_available
        
        # Check circuit breaker status
        circuit_breaker_open = llm_service._is_azure_circuit_open()
        last_failure = llm_service.last_azure_failure
        
        # Determine overall status
        overall_status = "healthy"
        if not db_connected:
            overall_status = "degraded"
        elif circuit_breaker_open:
            overall_status = "degraded"
        
        return HealthResponse(
            status=overall_status,
            database_connected=db_connected,
            llm_configured=llm_configured,
            circuit_breaker_open=circuit_breaker_open,
            last_azure_failure=last_failure,
            version=settings.API_VERSION
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/debug/env")
async def debug_environment():
    """Check environment configuration for debugging."""
    return {
        "environment": settings.ENVIRONMENT,
        "azure_sql_configured": settings.is_azure_sql_configured,
        "azure_openai_configured": settings.is_azure_openai_configured,
        "azure_sql_server": settings.AZURE_SQL_SERVER,
        "cors_origins": settings.ALLOWED_ORIGINS,
        "port": settings.API_PORT
    }


@app.get("/debug/db-test")
async def debug_database_connection():
    """Test database connection with detailed error info."""
    try:
        db_info = await db_manager.get_database_info()
        return {
            "status": "success",
            "database_info": db_info,
            "connection_string_format": f"mssql+pymssql://{settings.AZURE_SQL_USERNAME}:***@{settings.AZURE_SQL_SERVER}/{settings.AZURE_SQL_DATABASE}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "connection_string_format": f"mssql+pymssql://{settings.AZURE_SQL_USERNAME}:***@{settings.AZURE_SQL_SERVER}/{settings.AZURE_SQL_DATABASE}"
        }


# Development monitoring endpoints (minimal set)
@app.get("/debug/status")
async def debug_status():
    """Essential system status for development monitoring."""
    try:
        # Get basic system health
        db_info = await db_manager.get_database_info()
        llm_results = await llm_service.test_connectivity()
        
        return {
            "timestamp": "2025-07-11",
            "database": {
                "status": db_info.get("status"),
                "server": settings.AZURE_SQL_SERVER
            },
            "llm_service": llm_results,
            "environment": settings.ENVIRONMENT,
            "circuit_breaker_open": llm_service._is_azure_circuit_open(),
            "last_failure": llm_service.last_azure_failure.isoformat() if llm_service.last_azure_failure else None
        }
    except Exception as e:
        logger.error(f"Debug status failed: {e}")
        return {"error": str(e)}


@app.post("/debug/reset-circuit-breaker")
async def reset_circuit_breaker():
    """Reset the Azure OpenAI circuit breaker."""
    try:
        llm_service.reset_circuit_breaker()
        return {
            "status": "success",
            "message": "Circuit breaker reset successfully",
            "circuit_breaker_open": llm_service._is_azure_circuit_open()
        }
    except Exception as e:
        logger.error(f"Circuit breaker reset failed: {e}")
        return {"error": str(e)}


@app.get("/api/products/search")
async def search_products_by_name(q: str, limit: int = 10):
    """Search for products by product name."""
    try:
        if not q or len(q.strip()) < 2:
            return {"error": "Query must be at least 2 characters long"}
        
        if limit > 50:
            limit = 50  # Cap the limit for performance
        
        # Search by product name
        results = await product_manager.search_products_by_name(q.strip(), limit)
        
        return {
            "query": q.strip(),
            "search_type": "product_name",
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Product search by name failed: {e}")
        return {"error": str(e)}


@app.get("/api/products/search-by-crop")
async def search_products_by_crop(q: str, limit: int = 10):
    """Search for products by crop type."""
    try:
        if not q or len(q.strip()) < 2:
            return {"error": "Query must be at least 2 characters long"}
        
        if limit > 50:
            limit = 50  # Cap the limit for performance
        
        # Search by crop (existing functionality)
        results = await product_manager.search_products(q.strip(), limit)
        
        return {
            "query": q.strip(),
            "search_type": "crop",
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Product search by crop failed: {e}")
        return {"error": str(e)}


@app.get("/api/products/{product_name}")
async def get_product_by_name(product_name: str):
    """Get a specific product by exact name."""
    try:
        if not product_name or len(product_name.strip()) < 2:
            return {"error": "Product name must be at least 2 characters long"}
        
        product = await product_manager.get_product_by_name(product_name.strip())
        
        if product:
            return {
                "product_name": product_name.strip(),
                "product": product
            }
        else:
            return {"error": "Product not found"}
        
    except Exception as e:
        logger.error(f"Get product by name failed: {e}")
        return {"error": str(e)}


@app.get("/api/crops")
async def get_all_crops():
    """Get all available crop types."""
    try:
        crops = await product_manager.get_crops()
        
        return {
            "crops_count": len(crops),
            "crops": sorted(crops)  # Sort alphabetically
        }
        
    except Exception as e:
        logger.error(f"Get crops failed: {e}")
        return {"error": str(e)}


@app.get("/debug/test-smart-chat")
async def test_smart_chat():
    """Test the new smart chat functionality with realistic scenarios."""
    try:
        scenarios = [
            {
                "name": "insufficient_info",
                "message": "What fertilizer should I use for my Grass Pastures?",
                "context": {"crop_type": "Grass"},  # Missing application type and problem
                "description": "Basic question without enough detail"
            },
            {
                "name": "specific_request",
                "message": "I need a soil fertilizer for my tobacco to help with soil salinity",
                "context": {
                    "crop_type": "Field Tobacco", 
                    "application_type": "Soil",
                    "problem": "Soil Salinity",
                    "growth_stage": "Flowering"
                },
                "description": "Detailed request with all required parameters"
            },
            {
                "name": "soil_application",
                "message": "What soil fertilizer do you recommend for potato crops to improve fertilizer efficiency?",
                "context": {
                    "crop_type": "Potatoes",
                    "application_type": "Soil", 
                    "problem": "Fertilizer Efficiency"
                },
                "description": "Specific soil application request"
            }
        ]
        
        results = []
        for scenario in scenarios:
            # Use criteria-based search for more accurate product matching
            context = scenario["context"]
            products = await product_manager.search_products_by_criteria(
                crop=context.get("crop_type"),
                application_type=context.get("application_type"),
                problem=context.get("problem")
                # No limit - get all matching products
            )
            
            # If no specific matches found, fall back to crop search
            if not products:
                products = await product_manager.search_products(context["crop_type"])
            
            # Remove duplicates by product name while preserving order
            unique_products = []
            seen_product_names = set()
            for product in products:
                product_name = product.get("product_name")
                if product_name and product_name not in seen_product_names:
                    unique_products.append(product)
                    seen_product_names.add(product_name)
            
            products = unique_products
            
            # Get AI response
            result = await llm_service.get_smart_chat_response(
                message=scenario["message"],
                product_context=products,
                user_context=scenario["context"]
            )
            
            results.append({
                "scenario": scenario["name"],
                "description": scenario["description"],
                "message": scenario["message"],
                "context": scenario["context"],
                "products_available": len(products),
                "search_method": "criteria" if products else "crop_fallback",
                "product_names": [p.get("product_name") for p in products[:5]],  # Show first 5 product names
                "ai_response": result.get("response", "No response"),  # No truncation
                "status": result.get("status"),
                "context_analysis": result.get("context_used", {}).get("context_analysis", {})
            })
        
        return {
            "test": "smart_chat_realistic_scenarios",
            "total_scenarios": len(scenarios),
            "scenarios": results,
            "note": "This demonstrates how the AI handles different levels of detail in user requests"
        }
        
    except Exception as e:
        logger.error(f"Smart chat test failed: {e}")
        return {"error": str(e)}


@app.get("/debug/test-intelligent-chat")
async def test_intelligent_chat():
    """Test the intelligent chat with automatic context retrieval."""
    try:
        # Test message
        test_message = "I need help with fertilizing my potato crop. What do you recommend?"
        
        # User context
        user_context = {
            "crop_type": "Potatoes",
            "location": "Western Cape, South Africa",
            "growth_stage": "Tuber development"
        }
        
        # Get intelligent response (context automatically retrieved)
        result = await llm_service.get_intelligent_response(
            message=test_message,
            user_context=user_context
        )
        
        return {
            "test": "intelligent_chat_auto_context",
            "message": test_message,
            "user_context": user_context,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Intelligent chat test failed: {e}")
        return {"error": str(e)}


@app.get("/debug/test-conversation")
async def test_conversation():
    """Test conversation with different farming scenarios."""
    try:
        test_scenarios = [
            {
                "message": "What NPK ratio should I use for my tomatoes?",
                "context": {"crop_type": "Tomatoes", "growth_stage": "Flowering"}
            },
            {
                "message": "My lettuce plants have yellowing leaves. What should I do?",
                "context": {"crop_type": "Lettuce", "problem": "Yellowing leaves"}
            },
            {
                "message": "I need organic fertilizer for vegetables",
                "context": {"crop_type": "Vegetables", "preference": "Organic"}
            }
        ]
        
        results = []
        for i, scenario in enumerate(test_scenarios, 1):
            result = await llm_service.get_intelligent_response(
                message=scenario["message"],
                user_context=scenario["context"]
            )
            
            results.append({
                "scenario": i,
                "message": scenario["message"],
                "context": scenario["context"],
                "response": result.get("response", "No response")[:200] + "..." if len(result.get("response", "")) > 200 else result.get("response", "No response"),
                "status": result.get("status"),
                "products_used": result.get("context_used", {}).get("products_count", 0)
            })
        
        return {
            "test": "conversation_scenarios",
            "total_scenarios": len(test_scenarios),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Conversation test failed: {e}")
        return {"error": str(e)}


# Chat API endpoints - Phase 4.1 implementation
app.include_router(chat.router)

# Admin and monitoring endpoints - Phase 5.2 implementation
app.include_router(admin.router)
