"""
Database Configuration for InsightIQ
SQLite async-first storage engine using the databases library.
Simplified, robust local storage with in-memory caching.
"""

import os
import json
import logging
import asyncio
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from databases import Database
import sqlalchemy
from sqlalchemy import Column, String, DateTime, JSON, Float, Integer, Boolean, Text, MetaData

logger = logging.getLogger(__name__)

# Database configuration - defaults to SQLite for local standalone operation
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./insightiq.db")

# Create database instance using databases library
database = Database(DATABASE_URL)

# SQLAlchemy metadata for table definitions
metadata = MetaData()

# Define database tables using SQLAlchemy Core
analysis_sessions = sqlalchemy.Table(
    "analysis_sessions",
    metadata,
    Column("id", String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
    Column("session_id", String(255), index=True, nullable=False),
    Column("analysis_type", String(100), nullable=False),
    Column("file_info", JSON),
    Column("dashboard_config", JSON),
    Column("ai_insights", JSON),
    Column("performance_summary", JSON),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
)

file_uploads = sqlalchemy.Table(
    "file_uploads",
    metadata,
    Column("id", String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
    Column("file_hash", String(255), index=True, nullable=False),
    Column("filename", String(500), nullable=False),
    Column("file_size", Integer),
    Column("mime_type", String(200)),
    Column("upload_path", String(1000)),
    Column("metadata_info", JSON),
    Column("processed", Boolean, default=False),
    Column("created_at", DateTime, default=datetime.utcnow)
)

user_sessions = sqlalchemy.Table(
    "user_sessions",
    metadata,
    Column("id", String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
    Column("session_token", String(500), index=True, nullable=False),
    Column("user_data", JSON),
    Column("last_activity", DateTime, default=datetime.utcnow),
    Column("created_at", DateTime, default=datetime.utcnow)
)

comparison_results = sqlalchemy.Table(
    "comparison_results",
    metadata,
    Column("id", String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
    Column("session_id", String(255), index=True, nullable=False),
    Column("estimated_file_hash", String(255)),
    Column("actual_file_hash", String(255)),
    Column("comparison_data", JSON),
    Column("insights", JSON),
    Column("created_at", DateTime, default=datetime.utcnow)
)

# UI State table
ui_state = sqlalchemy.Table(
    "ui_state",
    metadata,
    Column("id", String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
    Column("user_id", String(255), index=True, nullable=False),
    Column("state_type", String(100), index=True, nullable=False),
    Column("state_key", String(255), nullable=False),
    Column("state_value", JSON, nullable=False),
    Column("last_updated", DateTime, default=datetime.utcnow),
    Column("created_at", DateTime, default=datetime.utcnow),
    sqlalchemy.UniqueConstraint("user_id", "state_type", "state_key", name="uq_user_state")
)

# Dashboard state table
dashboard_state = sqlalchemy.Table(
    "dashboard_state",
    metadata,
    Column("id", String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
    Column("user_id", String(255), index=True, nullable=False),
    Column("dashboard_id", String(255), index=True, nullable=False),
    Column("layout_config", JSON),
    Column("theme_config", JSON),
    Column("filters_config", JSON),
    Column("last_updated", DateTime, default=datetime.utcnow),
    Column("created_at", DateTime, default=datetime.utcnow),
    sqlalchemy.UniqueConstraint("user_id", "dashboard_id", name="uq_user_dashboard")
)

class CacheManager:
    """In-memory cache manager with automatic TTL expiration."""
    
    def __init__(self):
        self.memory_cache: Dict[str, str] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self._cleanup_task = None
        
    async def init(self):
        """Initialize in-memory cache and start cleanup task."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_cache())
        logger.info("In-memory cache initialized")
        return True
    
    # Backward compatibility alias
    async def init_redis(self):
        return await self.init()
    
    async def _cleanup_expired_cache(self):
        """Background task to clean up expired in-memory cache entries."""
        while True:
            try:
                current_time = datetime.utcnow()
                expired_keys = [
                    key for key, expiry_time in list(self.cache_expiry.items())
                    if expiry_time <= current_time
                ]
                
                for key in expired_keys:
                    self.memory_cache.pop(key, None)
                    self.cache_expiry.pop(key, None)
                
                await asyncio.sleep(300)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Cache cleanup warning: {e}")
                await asyncio.sleep(60)
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        if key in self.cache_expiry:
            if self.cache_expiry[key] <= datetime.utcnow():
                self.memory_cache.pop(key, None)
                self.cache_expiry.pop(key, None)
                return None
            return self.memory_cache.get(key)
        return None
    
    async def set(self, key: str, value: str, expire: int = 3600):
        """Set value in cache with TTL in seconds."""
        self.memory_cache[key] = value
        self.cache_expiry[key] = datetime.utcnow() + timedelta(seconds=expire)
        
        if len(self.memory_cache) > 2000:
            oldest_keys = sorted(self.cache_expiry.items(), key=lambda x: x[1])[:200]
            for old_key, _ in oldest_keys:
                self.memory_cache.pop(old_key, None)
                self.cache_expiry.pop(old_key, None)
        return True

    async def close(self):
        """Clear cache and cancel cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        self.memory_cache.clear()
        self.cache_expiry.clear()

# Global cache manager instance
cache_manager = CacheManager()

async def init_database() -> bool:
    """
    Initialize database connection and create tables.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info(f"Connecting to SQLite database: {DATABASE_URL}")
        
        # Connect to async database
        await database.connect()
        logger.info("Database connected successfully")
        
        # Create sync engine for table creation
        sync_url = DATABASE_URL
        if sync_url.startswith("sqlite+aiosqlite:"):
            sync_url = sync_url.replace("sqlite+aiosqlite:", "sqlite:")
            
        sync_engine = sqlalchemy.create_engine(sync_url)
        metadata.create_all(sync_engine, checkfirst=True)
        logger.info("Database tables created/verified")
        
        # Initialize in-memory cache
        await cache_manager.init()
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

async def close_database():
    """Close database and cache connections."""
    try:
        if database.is_connected:
            await database.disconnect()
            logger.info("Database disconnected")
        
        await cache_manager.close()
        logger.info("Cache disconnected")
    except Exception as e:
        logger.error(f"Error closing database: {e}")

async def get_database() -> Database:
    """FastAPI dependency to get database instance."""
    return database

# Storage operations
async def store_analysis_session(
    session_id: str,
    analysis_type: str,
    file_info: Dict[str, Any],
    dashboard_config: Dict[str, Any],
    ai_insights: Optional[Dict[str, Any]] = None,
    performance_summary: Optional[Dict[str, Any]] = None
) -> str:
    """Store analysis session in database."""
    try:
        query = """
            INSERT INTO analysis_sessions (id, session_id, analysis_type, file_info, dashboard_config, ai_insights, performance_summary, created_at, updated_at)
            VALUES (:id, :session_id, :analysis_type, :file_info, :dashboard_config, :ai_insights, :performance_summary, :created_at, :updated_at)
        """
        now = datetime.utcnow()
        await database.execute(
            query,
            values={
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "analysis_type": analysis_type,
                "file_info": json.dumps(file_info),
                "dashboard_config": json.dumps(dashboard_config),
                "ai_insights": json.dumps(ai_insights or {}),
                "performance_summary": json.dumps(performance_summary or {}),
                "created_at": now,
                "updated_at": now
            }
        )
        logger.info(f"Analysis session stored: {session_id}")
        return session_id
    except Exception as e:
        logger.error(f"Failed to store analysis session: {e}")
        raise

async def get_analysis_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve analysis session from database."""
    try:
        query = analysis_sessions.select().where(
            analysis_sessions.c.session_id == session_id
        )
        result = await database.fetch_one(query)
        if result:
            return dict(result._mapping)
        return None
    except Exception as e:
        logger.error(f"Failed to get analysis session: {e}")
        return None

async def store_file_info(
    file_hash: str,
    filename: str,
    file_size: int,
    mime_type: str,
    upload_path: str,
    metadata_info: Optional[Dict[str, Any]] = None
) -> str:
    """Store file upload information."""
    try:
        query = """
            INSERT INTO file_uploads (id, file_hash, filename, file_size, mime_type, upload_path, metadata_info, processed, created_at)
            VALUES (:id, :file_hash, :filename, :file_size, :mime_type, :upload_path, :metadata_info, :processed, :created_at)
        """
        await database.execute(
            query,
            values={
                "id": str(uuid.uuid4()),
                "file_hash": file_hash,
                "filename": filename,
                "file_size": file_size,
                "mime_type": mime_type,
                "upload_path": upload_path,
                "metadata_info": json.dumps(metadata_info or {}),
                "processed": False,
                "created_at": datetime.utcnow()
            }
        )
        logger.info(f"File info stored: {filename}")
        return file_hash
    except Exception as e:
        logger.error(f"Failed to store file info: {e}")
        raise

async def get_file_info(file_hash: str) -> Optional[Dict[str, Any]]:
    """Retrieve file information by hash."""
    try:
        query = file_uploads.select().where(
            file_uploads.c.file_hash == file_hash
        )
        result = await database.fetch_one(query)
        if result:
            return dict(result._mapping)
        return None
    except Exception as e:
        logger.error(f"Failed to get file info: {e}")
        return None

async def store_comparison_result(
    session_id: str,
    estimated_file_hash: str,
    actual_file_hash: str,
    comparison_data: Dict[str, Any],
    insights: Optional[Dict[str, Any]] = None
) -> str:
    """Store comparison analysis results."""
    try:
        query = """
            INSERT INTO comparison_results (id, session_id, estimated_file_hash, actual_file_hash, comparison_data, insights, created_at)
            VALUES (:id, :session_id, :estimated_file_hash, :actual_file_hash, :comparison_data, :insights, :created_at)
        """
        await database.execute(
            query,
            values={
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "estimated_file_hash": estimated_file_hash,
                "actual_file_hash": actual_file_hash,
                "comparison_data": json.dumps(comparison_data),
                "insights": json.dumps(insights or {}),
                "created_at": datetime.utcnow()
            }
        )
        logger.info(f"Comparison result stored: {session_id}")
        return session_id
    except Exception as e:
        logger.error(f"Failed to store comparison result: {e}")
        raise

async def get_comparison_result(session_id: str) -> Optional[Dict[str, Any]]:
    """Get comparison result from database."""
    try:
        query = """
            SELECT id, session_id, estimated_file_hash, actual_file_hash, 
                   comparison_data, insights, created_at
            FROM comparison_results 
            WHERE session_id = :session_id
            ORDER BY created_at DESC
            LIMIT 1
        """
        result = await database.fetch_one(query, {"session_id": session_id})
        if result:
            return {
                "id": str(result["id"]),
                "session_id": result["session_id"],
                "estimated_file_hash": result["estimated_file_hash"],
                "actual_file_hash": result["actual_file_hash"],
                "comparison_data": result["comparison_data"],
                "insights": result["insights"],
                "created_at": str(result["created_at"])
            }
        return None
    except Exception as e:
        logger.error(f"Failed to get comparison result: {e}")
        return None

# UI State management
async def store_ui_state(user_id: str, state_type: str, state_key: str, state_value: Any) -> bool:
    """Store UI state in SQLite database."""
    try:
        json_value = json.dumps(state_value)
        query = """
            INSERT INTO ui_state (id, user_id, state_type, state_key, state_value, last_updated, created_at)
            VALUES (:id, :user_id, :state_type, :state_key, :state_value, :last_updated, :created_at)
            ON CONFLICT (user_id, state_type, state_key) 
            DO UPDATE SET 
                state_value = excluded.state_value,
                last_updated = excluded.last_updated
        """
        now = datetime.utcnow()
        values = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "state_type": state_type,
            "state_key": state_key,
            "state_value": json_value,
            "last_updated": now,
            "created_at": now
        }
        await database.execute(query, values)
        return True
    except Exception as e:
        logger.error(f"Failed to store UI state: {e}")
        return False

async def get_ui_state(user_id: str, state_type: str, state_key: str) -> Optional[Any]:
    """Get UI state from database."""
    try:
        query = """
            SELECT state_value FROM ui_state 
            WHERE user_id = :user_id AND state_type = :state_type AND state_key = :state_key
            ORDER BY last_updated DESC
            LIMIT 1
        """
        result = await database.fetch_one(query, {
            "user_id": user_id,
            "state_type": state_type,
            "state_key": state_key
        })
        if result:
            try:
                return json.loads(result["state_value"]) if isinstance(result["state_value"], str) else result["state_value"]
            except json.JSONDecodeError:
                return result["state_value"]
        return None
    except Exception as e:
        logger.error(f"Failed to get UI state: {e}")
        return None

async def get_all_ui_state(user_id: str, state_type: str) -> Dict[str, Any]:
    """Get all UI state for a specific type."""
    try:
        query = """
            SELECT state_key, state_value FROM ui_state 
            WHERE user_id = :user_id AND state_type = :state_type
            ORDER BY last_updated DESC
        """
        results = await database.fetch_all(query, {
            "user_id": user_id,
            "state_type": state_type
        })
        state_dict = {}
        for result in results:
            try:
                value = json.loads(result["state_value"]) if isinstance(result["state_value"], str) else result["state_value"]
                state_dict[result["state_key"]] = value
            except json.JSONDecodeError:
                state_dict[result["state_key"]] = result["state_value"]
        return state_dict
    except Exception as e:
        logger.error(f"Failed to get all UI state: {e}")
        return {}

async def store_dashboard_state(user_id: str, dashboard_id: str, layout_config: Dict, theme_config: Optional[Dict] = None, filters_config: Optional[Dict] = None) -> bool:
    """Store dashboard state in database."""
    try:
        query = """
            INSERT INTO dashboard_state (id, user_id, dashboard_id, layout_config, theme_config, filters_config, last_updated, created_at)
            VALUES (:id, :user_id, :dashboard_id, :layout_config, :theme_config, :filters_config, :last_updated, :created_at)
            ON CONFLICT (user_id, dashboard_id) 
            DO UPDATE SET 
                layout_config = excluded.layout_config,
                theme_config = excluded.theme_config,
                filters_config = excluded.filters_config,
                last_updated = excluded.last_updated
        """
        now = datetime.utcnow()
        values = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "dashboard_id": dashboard_id,
            "layout_config": json.dumps(layout_config) if layout_config else None,
            "theme_config": json.dumps(theme_config) if theme_config else None,
            "filters_config": json.dumps(filters_config) if filters_config else None,
            "last_updated": now,
            "created_at": now
        }
        await database.execute(query, values)
        return True
    except Exception as e:
        logger.error(f"Failed to store dashboard state: {e}")
        return False

async def get_dashboard_state(user_id: str, dashboard_id: str) -> Optional[Dict[str, Any]]:
    """Get dashboard state from database."""
    try:
        query = """
            SELECT layout_config, theme_config, filters_config, last_updated
            FROM dashboard_state 
            WHERE user_id = :user_id AND dashboard_id = :dashboard_id
            ORDER BY last_updated DESC
            LIMIT 1
        """
        result = await database.fetch_one(query, {
            "user_id": user_id,
            "dashboard_id": dashboard_id
        })
        if result:
            return {
                "layout_config": json.loads(result["layout_config"]) if result["layout_config"] else {},
                "theme_config": json.loads(result["theme_config"]) if result["theme_config"] else {},
                "filters_config": json.loads(result["filters_config"]) if result["filters_config"] else {},
                "last_updated": str(result["last_updated"])
            }
        return None
    except Exception as e:
        logger.error(f"Failed to get dashboard state: {e}")
        return None

async def delete_ui_state(user_id: str, state_type: str, state_key: Optional[str] = None) -> bool:
    """Delete UI state from database."""
    try:
        if state_key:
            query = "DELETE FROM ui_state WHERE user_id = :user_id AND state_type = :state_type AND state_key = :state_key"
            values = {"user_id": user_id, "state_type": state_type, "state_key": state_key}
        else:
            query = "DELETE FROM ui_state WHERE user_id = :user_id AND state_type = :state_type"
            values = {"user_id": user_id, "state_type": state_type}
        
        await database.execute(query, values)
        return True
    except Exception as e:
        logger.error(f"Failed to delete UI state: {e}")
        return False
