"""
Enhanced Database Service for InsightIQ
SQLite-optimized query management, connection tracking, and caching.
"""

import asyncio
import logging
import json
import time
import hashlib
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from dataclasses import dataclass
import uuid

from databases import Database
import sqlalchemy
from sqlalchemy import text, MetaData, Table

from src.core.database import database, cache_manager, metadata

logger = logging.getLogger(__name__)

@dataclass
class QueryOptimizationPlan:
    """Query optimization plan with execution strategy."""
    query: str
    estimated_cost: float
    use_cache: bool
    cache_ttl: int
    parallel_execution: bool
    index_suggestions: List[str]
    optimization_level: str

@dataclass
class ConnectionMetrics:
    """Database connection performance metrics."""
    active_connections: int
    idle_connections: int
    total_queries: int
    avg_query_time: float
    cache_hit_ratio: float
    last_updated: datetime

class SQLiteOptimizedQueryEngine:
    """Query optimization engine for SQLite analytics."""
    
    def __init__(self):
        self.query_cache = {}
        self.optimization_cache = {}
        
    async def analyze_query_plan(self, query: str, params: Optional[Dict] = None) -> QueryOptimizationPlan:
        """Analyze query execution plan."""
        try:
            plan_key = hashlib.md5(f"{query}{params}".encode()).hexdigest()
            if plan_key in self.optimization_cache:
                return self.optimization_cache[plan_key]
            
            plan = QueryOptimizationPlan(
                query=query,
                estimated_cost=1.0,
                use_cache=True,
                cache_ttl=1800,
                parallel_execution=False,
                index_suggestions=[],
                optimization_level="fast"
            )
            self.optimization_cache[plan_key] = plan
            return plan
        except Exception as e:
            logger.warning(f"Query plan analysis fallback: {e}")
            return QueryOptimizationPlan(
                query=query,
                estimated_cost=0,
                use_cache=True,
                cache_ttl=1800,
                parallel_execution=False,
                index_suggestions=[],
                optimization_level="fast"
            )

class EnhancedDatabaseService:
    """Enhanced database service for SQLite backend."""
    
    def __init__(self):
        self.query_engine = SQLiteOptimizedQueryEngine()
        self.query_count = 0
        self.total_query_time = 0.0
        
    async def initialize(self):
        """Initialize enhanced database service."""
        try:
            await self._ensure_performance_tables()
            logger.info("Enhanced Database Service initialized for SQLite")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Enhanced Database Service: {e}")
            return False
    
    async def _ensure_performance_tables(self):
        """Ensure performance monitoring tables exist in SQLite."""
        try:
            if database.is_connected:
                await database.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id TEXT PRIMARY KEY,
                        operation_name TEXT NOT NULL,
                        execution_time REAL NOT NULL,
                        cache_hit INTEGER DEFAULT 0,
                        data_size INTEGER,
                        user_id TEXT,
                        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                await database.execute("""
                    CREATE TABLE IF NOT EXISTS query_optimization_history (
                        id TEXT PRIMARY KEY,
                        query_hash TEXT NOT NULL,
                        original_query TEXT NOT NULL,
                        optimized_query TEXT,
                        execution_time_before REAL,
                        execution_time_after REAL,
                        optimization_suggestions TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        except Exception as e:
            logger.warning(f"Performance tables setup warning: {e}")
    
    async def execute_optimized_query(
        self, 
        query: str, 
        params: Optional[Dict] = None,
        use_cache: bool = True,
        cache_ttl: int = 1800
    ) -> List[Dict[str, Any]]:
        """Execute a query with tracking and caching."""
        start_time = time.time()
        self.query_count += 1
        
        query_hash = hashlib.md5(f"{query}{params}".encode()).hexdigest()
        cache_key = f"db_query:{query_hash}"
        
        if use_cache:
            cached = await cache_manager.get(cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except Exception:
                    pass
        
        results = await database.fetch_all(query, values=params or {})
        rows = [dict(r._mapping) for r in results]
        
        elapsed = time.time() - start_time
        self.total_query_time += elapsed
        
        if use_cache and len(rows) < 5000:
            try:
                await cache_manager.set(cache_key, json.dumps(rows, default=str), expire=cache_ttl)
            except Exception:
                pass
                
        return rows
    
    async def get_table_performance_analysis(self, table_name: str) -> Dict[str, Any]:
        """Analyze table stats in SQLite."""
        try:
            count_res = await database.fetch_one(f"SELECT COUNT(*) as count FROM {table_name}")
            row_count = count_res["count"] if count_res else 0
            
            return {
                "table_name": table_name,
                "row_count": row_count,
                "table_size": "N/A (SQLite)",
                "size_bytes": 0,
                "index_count": 1,
                "indexes": [],
                "missing_indexes": [],
                "optimization_suggestions": []
            }
        except Exception as e:
            logger.warning(f"Table stats error for {table_name}: {e}")
            return {"table_name": table_name, "error": str(e)}
    
    async def get_connection_metrics(self) -> ConnectionMetrics:
        """Get database connection metrics."""
        avg_time = (self.total_query_time / self.query_count) if self.query_count > 0 else 0.0
        return ConnectionMetrics(
            active_connections=1 if database.is_connected else 0,
            idle_connections=0,
            total_queries=self.query_count,
            avg_query_time=avg_time,
            cache_hit_ratio=0.0,
            last_updated=datetime.utcnow()
        )
    
    async def optimize_database_settings(self) -> Dict[str, Any]:
        """Apply SQLite PRAGMA optimizations."""
        try:
            if database.is_connected:
                await database.execute("PRAGMA journal_mode = WAL;")
                await database.execute("PRAGMA synchronous = NORMAL;")
                await database.execute("PRAGMA cache_size = 10000;")
            return {
                "applied": ["journal_mode=WAL", "synchronous=NORMAL", "cache_size=10000"],
                "status": "optimized"
            }
        except Exception as e:
            return {"error": str(e)}

# Global service instance
enhanced_db_service = EnhancedDatabaseService()

async def execute_analytics_query(query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
    """Helper function to execute analytics queries."""
    return await enhanced_db_service.execute_optimized_query(query, params)
