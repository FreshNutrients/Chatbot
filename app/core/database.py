"""
Database connection and operations module.

This module handles:
- Azure SQL Database connections
- Product data retrieval
- Chat logging
- Conversation history management
"""

import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import asyncio
from datetime import datetime

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Manages database connections and operations for Azure SQL Database."""
    
    def __init__(self):
        self.engine: Optional[Engine] = None
        self.async_engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[sessionmaker] = None
        self.async_session_factory: Optional[async_sessionmaker] = None
        self._connection_string: Optional[str] = None
        self._async_connection_string: Optional[str] = None
        
    def _build_connection_strings(self) -> tuple[str, str]:
        """Build synchronous and asynchronous connection strings."""
        # Production: Use Private Endpoint hostname instead of public
        # Development: Use public hostname with firewall rules
        
        if settings.ENVIRONMENT == "production":
            # Private endpoint hostname (no firewall restrictions)
            server_host = settings.AZURE_SQL_PRIVATE_ENDPOINT or settings.AZURE_SQL_SERVER
        else:
            # Public hostname (requires firewall rules for development)
            server_host = settings.AZURE_SQL_SERVER
        
        # Synchronous connection string (pymssql)
        sync_conn_str = (
            f"mssql+pymssql://{settings.AZURE_SQL_USERNAME}:{settings.AZURE_SQL_PASSWORD}"
            f"@{server_host}/{settings.AZURE_SQL_DATABASE}"
            f"?charset=utf8"
        )
        
        # For now, we'll use the sync connection string for both since aioodbc may not be available
        # In production, you'd want to use aioodbc for true async operations
        async_conn_str = sync_conn_str
        
        return sync_conn_str, async_conn_str
    
    async def initialize(self) -> bool:
        """Initialize database connections and engines."""
        try:
            logger.info("Initializing database connections...")
            
            # Build connection strings
            self._connection_string, self._async_connection_string = self._build_connection_strings()
            
            # Create synchronous engine
            self.engine = create_engine(
                self._connection_string,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=settings.ENVIRONMENT == "development"
            )
            
            # Create session factory
            self.session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
            
            # Test connection
            await self.test_connection()
            
            logger.info("Database connections initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """Test database connectivity."""
        try:
            loop = asyncio.get_event_loop()
            
            def _test_sync():
                with self.engine.connect() as conn:
                    result = conn.execute(text("SELECT 1 as test"))
                    return result.scalar()
            
            test_value = await loop.run_in_executor(None, _test_sync)
            
            if test_value == 1:
                logger.info("Database connection test successful")
                return True
            else:
                logger.error("Database connection test failed - unexpected result")
                return False
                    
        except SQLAlchemyError as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection test: {str(e)}")
            return False
    
    @asynccontextmanager
    async def get_session(self, auto_commit=True):
        """Get a database session with automatic cleanup - async compatible."""
        if not self.session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        # Run session operations in thread pool to make them async-compatible
        loop = asyncio.get_event_loop()
        
        # Create session in thread pool
        session = await loop.run_in_executor(None, self.session_factory)
        
        try:
            yield session
            # Only commit if auto_commit is True and we're not handling it manually
            if auto_commit:
                await loop.run_in_executor(None, session.commit)
        except Exception as e:
            # Rollback in thread pool
            await loop.run_in_executor(None, session.rollback)
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            # Close in thread pool
            await loop.run_in_executor(None, session.close)
    
    async def _execute_in_session(self, session, sql_text, params=None, fetch_results=True):
        """Execute SQL in a session within thread pool."""
        loop = asyncio.get_event_loop()
        
        def _execute():
            if params:
                result = session.execute(sql_text, params)
            else:
                result = session.execute(sql_text)
            
            if not fetch_results:
                # For INSERT, UPDATE, DELETE operations
                return result
            
            # For SELECT operations, fetch all results immediately
            try:
                return result.fetchall()
            except:
                # If fetchall() fails, return the result object
                return result
        
        return await loop.run_in_executor(None, _execute)
    
    async def get_database_info(self) -> Dict[str, Any]:
        """Get database connection information and status."""
        try:
            async with self.get_session() as session:
                # Get database version
                version_result = await self._execute_in_session(session, text("SELECT @@VERSION as version"))
                version = version_result[0].version if version_result else "Unknown"
                
                # Get database name
                db_result = await self._execute_in_session(session, text("SELECT DB_NAME() as db_name"))
                db_name = db_result[0].db_name if db_result else "Unknown"
                
                # Get server info
                server_result = await self._execute_in_session(session, text("SELECT @@SERVERNAME as server_name"))
                server_name = server_result[0].server_name if server_result else "Unknown"
                
                return {
                    "status": "connected",
                    "database_name": db_name,
                    "server_name": server_name,
                    "version": version,
                    "connection_pool_size": self.engine.pool.size() if self.engine else 0,
                    "checked_out_connections": self.engine.pool.checkedout() if self.engine else 0
                }
        except Exception as e:
            logger.error(f"Failed to get database info: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def close(self):
        """Close all database connections."""
        try:
            if self.engine:
                self.engine.dispose()
                logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {str(e)}")


class ProductDataManager:
    """Manages product data retrieval and context operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def search_products(self, query: str, limit: int = None) -> List[Dict[str, Any]]:
        """Search for products based on query string."""
        try:
            async with self.db_manager.get_session() as session:
                # Build SQL with optional limit
                if limit:
                    sql = text(f"""
                        SELECT TOP {limit}
                            Application,
                            ApplicationType,
                            Crop,
                            Directions,
                            GrowthStage,
                            Label,
                            M_Intervention,
                            MSDS,
                            Notes,
                            Problem,
                            ProductName,
                            TechDoc
                        FROM Products
                        WHERE Crop LIKE :query
                        ORDER BY ProductName
                    """)
                else:
                    sql = text("""
                        SELECT 
                            Application,
                            ApplicationType,
                            Crop,
                            Directions,
                            GrowthStage,
                            Label,
                            M_Intervention,
                            MSDS,
                            Notes,
                            Problem,
                            ProductName,
                            TechDoc
                        FROM Products
                        WHERE Crop LIKE :query
                        ORDER BY ProductName
                    """)
                
                result = await self.db_manager._execute_in_session(session, sql, {"query": f"%{query}%"})
                
                products = []
                for row in result:
                    products.append({
                        "application": row.Application,
                        "application_type": row.ApplicationType,
                        "crop": row.Crop,
                        "directions": row.Directions,
                        "growth_stage": row.GrowthStage,
                        "label": row.Label,
                        "m_intervention": row.M_Intervention,
                        "msds": row.MSDS,
                        "notes": row.Notes,
                        "problem": row.Problem,
                        "product_name": row.ProductName,
                        "tech_doc": row.TechDoc
                    })
                
                return products
                
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            return []
    
    async def get_product_by_name(self, product_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific product by name."""
        try:
            async with self.db_manager.get_session() as session:
                sql = text("""
                    SELECT 
                        Application,
                        ApplicationType,
                        Crop,
                        Directions,
                        GrowthStage,
                        Label,
                        M_Intervention,
                        MSDS,
                        Notes,
                        Problem,
                        ProductName,
                        TechDoc
                    FROM Products
                    WHERE ProductName = :product_name
                """)
                
                result = session.execute(sql, {"product_name": product_name})
                row = result.fetchone()
                
                if row:
                    return {
                        "application": row.Application,
                        "application_type": row.ApplicationType,
                        "crop": row.Crop,
                        "directions": row.Directions,
                        "growth_stage": row.GrowthStage,
                        "label": row.Label,
                        "m_intervention": row.M_Intervention,
                        "msds": row.MSDS,
                        "notes": row.Notes,
                        "problem": row.Problem,
                        "product_name": row.ProductName,
                        "tech_doc": row.TechDoc
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting product by name: {str(e)}")
            return None
    
    async def search_products_by_name(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for products by product name (partial match)."""
        try:
            async with self.db_manager.get_session() as session:
                sql = text(f"""
                    SELECT TOP {limit}
                        Application,
                        ApplicationType,
                        Crop,
                        Directions,
                        GrowthStage,
                        Label,
                        M_Intervention,
                        MSDS,
                        Notes,
                        Problem,
                        ProductName,
                        TechDoc
                    FROM Products
                    WHERE ProductName LIKE :query
                    ORDER BY ProductName
                """)
                
                result = session.execute(sql, {"query": f"%{query}%"})
                
                products = []
                for row in result:
                    products.append({
                        "application": row.Application,
                        "application_type": row.ApplicationType,
                        "crop": row.Crop,
                        "directions": row.Directions,
                        "growth_stage": row.GrowthStage,
                        "label": row.Label,
                        "m_intervention": row.M_Intervention,
                        "msds": row.MSDS,
                        "notes": row.Notes,
                        "problem": row.Problem,
                        "product_name": row.ProductName,
                        "tech_doc": row.TechDoc
                    })
                
                return products
                
        except Exception as e:
            logger.error(f"Error searching products by name: {str(e)}")
            return []
    
    async def search_products_by_criteria(self, 
                                          crop: str = None, 
                                          application_type: str = None, 
                                          problem: str = None, 
                                          limit: int = None) -> List[Dict[str, Any]]:
        """Search for products by multiple criteria (crop, application type, problem)."""
        try:
            async with self.db_manager.get_session() as session:
                # Build dynamic WHERE clause
                where_conditions = []
                params = {}
                
                if crop:
                    where_conditions.append("Crop LIKE :crop")
                    params["crop"] = f"%{crop}%"
                
                if application_type:
                    where_conditions.append("ApplicationType LIKE :application_type")
                    params["application_type"] = f"%{application_type}%"
                
                if problem:
                    where_conditions.append("Problem LIKE :problem")
                    params["problem"] = f"%{problem}%"
                
                # If no criteria provided, return empty list
                if not where_conditions:
                    return []
                
                where_clause = " AND ".join(where_conditions)
                
                # Build SQL with optional limit
                if limit:
                    sql = text(f"""
                        SELECT TOP {limit}
                            Application,
                            ApplicationType,
                            Crop,
                            Directions,
                            GrowthStage,
                            Label,
                            M_Intervention,
                            MSDS,
                            Notes,
                            Problem,
                            ProductName,
                            TechDoc
                        FROM Products
                        WHERE {where_clause}
                        ORDER BY ProductName
                    """)
                else:
                    sql = text(f"""
                        SELECT 
                            Application,
                            ApplicationType,
                            Crop,
                            Directions,
                            GrowthStage,
                            Label,
                            M_Intervention,
                            MSDS,
                            Notes,
                            Problem,
                            ProductName,
                            TechDoc
                        FROM Products
                        WHERE {where_clause}
                        ORDER BY ProductName
                    """)
                
                result = session.execute(sql, params)
                
                products = []
                for row in result:
                    products.append({
                        "application": row.Application,
                        "application_type": row.ApplicationType,
                        "crop": row.Crop,
                        "directions": row.Directions,
                        "growth_stage": row.GrowthStage,
                        "label": row.Label,
                        "m_intervention": row.M_Intervention,
                        "msds": row.MSDS,
                        "notes": row.Notes,
                        "problem": row.Problem,
                        "product_name": row.ProductName,
                        "tech_doc": row.TechDoc
                    })
                
                return products
                
        except Exception as e:
            logger.error(f"Error searching products by criteria: {str(e)}")
            return []
    
    async def get_crops(self) -> List[str]:
        """Get all crop types."""
        try:
            async with self.db_manager.get_session() as session:
                sql = text("""
                    SELECT DISTINCT Crop
                    FROM Products
                    WHERE Crop IS NOT NULL
                    ORDER BY Crop
                """)
                
                result = session.execute(sql)
                crops = [row.Crop for row in result]
                
                return crops
                
        except Exception as e:
            logger.error(f"Error getting crops: {str(e)}")
            return []
    
    async def get_problems(self) -> List[str]:
        """Get all problem types."""
        try:
            async with self.db_manager.get_session() as session:
                sql = text("""
                    SELECT DISTINCT Problem
                    FROM Products
                    WHERE Problem IS NOT NULL
                    ORDER BY Problem
                """)
                
                result = session.execute(sql)
                problems = [row.Problem for row in result]
                
                return problems
                
        except Exception as e:
            logger.error(f"Error getting problems: {str(e)}")
            return []
    
    async def get_application_types(self) -> List[str]:
        """Get all application types."""
        try:
            async with self.db_manager.get_session() as session:
                sql = text("""
                    SELECT DISTINCT ApplicationType
                    FROM Products
                    WHERE ApplicationType IS NOT NULL
                    ORDER BY ApplicationType
                """)
                
                result = session.execute(sql)
                app_types = [row.ApplicationType for row in result]
                
                return app_types
                
        except Exception as e:
            logger.error(f"Error getting application types: {str(e)}")
            return []
    
    async def get_growth_stages(self) -> List[str]:
        """Get all growth stages."""
        try:
            async with self.db_manager.get_session() as session:
                sql = text("""
                    SELECT DISTINCT GrowthStage
                    FROM Products
                    WHERE GrowthStage IS NOT NULL
                    ORDER BY GrowthStage
                """)
                
                result = session.execute(sql)
                stages = [row.GrowthStage for row in result]
                
                return stages
                
        except Exception as e:
            logger.error(f"Error getting growth stages: {str(e)}")
            return []
    
    async def search_products_by_crop(self, crop: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for products by crop type."""
        try:
            async with self.db_manager.get_session() as session:
                sql = text("""
                    SELECT TOP :limit
                        Application,
                        ApplicationType,
                        Crop,
                        Directions,
                        GrowthStage,
                        Label,
                        M_Intervention,
                        MSDS,
                        Notes,
                        Problem,
                        ProductName,
                        TechDoc
                    FROM Products
                    WHERE Crop LIKE :crop
                    ORDER BY ProductName
                """)
                
                result = session.execute(sql, {
                    "crop": f"%{crop}%",
                    "limit": limit
                })
                
                products = []
                for row in result:
                    products.append({
                        "application": row.Application,
                        "application_type": row.ApplicationType,
                        "crop": row.Crop,
                        "directions": row.Directions,
                        "growth_stage": row.GrowthStage,
                        "label": row.Label,
                        "m_intervention": row.M_Intervention,
                        "msds": row.MSDS,
                        "notes": row.Notes,
                        "problem": row.Problem,
                        "product_name": row.ProductName,
                        "tech_doc": row.TechDoc
                    })
                
                return products
                
        except Exception as e:
            logger.error(f"Error searching products by crop: {str(e)}")
            return []
    
    async def search_products_by_problem(self, problem: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for products by problem type."""
        try:
            async with self.db_manager.get_session() as session:
                sql = text("""
                    SELECT TOP :limit
                        Application,
                        ApplicationType,
                        Crop,
                        Directions,
                        GrowthStage,
                        Label,
                        M_Intervention,
                        MSDS,
                        Notes,
                        Problem,
                        ProductName,
                        TechDoc
                    FROM Products
                    WHERE Problem LIKE :problem
                    ORDER BY ProductName
                """)
                
                result = session.execute(sql, {
                    "problem": f"%{problem}%",
                    "limit": limit
                })
                
                products = []
                for row in result:
                    products.append({
                        "application": row.Application,
                        "application_type": row.ApplicationType,
                        "crop": row.Crop,
                        "directions": row.Directions,
                        "growth_stage": row.GrowthStage,
                        "label": row.Label,
                        "m_intervention": row.M_Intervention,
                        "msds": row.MSDS,
                        "notes": row.Notes,
                        "problem": row.Problem,
                        "product_name": row.ProductName,
                        "tech_doc": row.TechDoc
                    })
                
                return products
                
        except Exception as e:
            logger.error(f"Error searching products by problem: {str(e)}")
            return []


class ChatLogManager:
    """Manages chat logging and conversation history."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_chat_logs_table(self):
        """Create the chat logs table if it doesn't exist."""
        try:
            async with self.db_manager.get_session() as session:
                sql = text("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ChatLogs' AND xtype='U')
                    CREATE TABLE ChatLogs (
                        LogID bigint IDENTITY(1,1) PRIMARY KEY,
                        SessionID varchar(255) NOT NULL,
                        UserMessage nvarchar(max) NOT NULL,
                        BotResponse nvarchar(max) NOT NULL,
                        MessageCategory varchar(100),
                        ProductContext nvarchar(max),
                        ResponseTime int,
                        Timestamp datetime2 DEFAULT GETDATE(),
                        UserIP varchar(45),
                        UserAgent varchar(500),
                        IsResolved bit DEFAULT 0,
                        Feedback int,
                        
                        INDEX IX_ChatLogs_SessionID (SessionID),
                        INDEX IX_ChatLogs_Timestamp (Timestamp),
                        INDEX IX_ChatLogs_Category (MessageCategory)
                    )
                """)
                
                await self.db_manager._execute_in_session(session, sql, fetch_results=False)
                logger.info("ChatLogs table created/verified successfully")
                
        except Exception as e:
            logger.error(f"Error creating chat logs table: {str(e)}")
    
    async def log_chat_interaction(self, 
                                   session_id: str,
                                   user_message: str,
                                   bot_response: str,
                                   category: Optional[str] = None,
                                   product_context: Optional[str] = None,
                                   response_time: Optional[int] = None,
                                   user_ip: Optional[str] = None,
                                   user_agent: Optional[str] = None) -> bool:
        """Log a chat interaction."""
        try:
            # Simple synchronous approach run in thread pool
            loop = asyncio.get_event_loop()
            
            def _log_sync():
                with self.db_manager.engine.connect() as conn:
                    sql = text("""
                        INSERT INTO ChatLogs 
                        (SessionID, UserMessage, BotResponse, MessageCategory, 
                         ProductContext, ResponseTime, UserIP, UserAgent)
                        VALUES 
                        (:session_id, :user_message, :bot_response, :category,
                         :product_context, :response_time, :user_ip, :user_agent)
                    """)
                    
                    conn.execute(sql, {
                        "session_id": session_id,
                        "user_message": user_message,
                        "bot_response": bot_response,
                        "category": category,
                        "product_context": product_context,
                        "response_time": response_time,
                        "user_ip": user_ip,
                        "user_agent": user_agent
                    })
                    conn.commit()
                    return True
            
            result = await loop.run_in_executor(None, _log_sync)
            return result
                
        except Exception as e:
            logger.error(f"Error logging chat interaction: {str(e)}")
            return False
    
    async def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a session."""
        try:
            # Simple synchronous approach run in thread pool
            loop = asyncio.get_event_loop()
            
            def _get_history_sync():
                with self.db_manager.engine.connect() as conn:
                    # Fix the TOP parameter issue - can't use parameter binding for TOP clause
                    sql = text(f"""
                        SELECT TOP {limit}
                            LogID,
                            UserMessage,
                            BotResponse,
                            MessageCategory,
                            Timestamp,
                            IsResolved,
                            Feedback
                        FROM ChatLogs
                        WHERE SessionID = :session_id
                        ORDER BY Timestamp DESC
                    """)
                    
                    result = conn.execute(sql, {
                        "session_id": session_id
                    })
                    
                    history = []
                    for row in result:
                        history.append({
                            "log_id": row.LogID,
                            "user_message": row.UserMessage,
                            "bot_response": row.BotResponse,
                            "category": row.MessageCategory,
                            "timestamp": row.Timestamp,
                            "is_resolved": row.IsResolved,
                            "feedback": row.Feedback
                        })
                    
                    return history
            
            history = await loop.run_in_executor(None, _get_history_sync)
            return history
                
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            return []


# Global database manager instance
db_manager = DatabaseManager()
product_manager = ProductDataManager(db_manager)
chat_log_manager = ChatLogManager(db_manager)
