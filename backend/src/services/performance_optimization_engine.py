"""
Performance Optimization Engine for Analytics Hub
Provides comprehensive performance monitoring, caching strategies, and database optimizations.
"""

import asyncio
import logging
import time
import json
import hashlib
from typing import Dict, Any, Optional, List, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
from functools import wraps
import statistics

from src.core.database import database, cache_manager, get_database

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    operation_name: str
    execution_time: float
    memory_usage: Optional[float] = None
    cache_hit: bool = False
    database_queries: int = 0
    data_size: Optional[int] = None
    timestamp: datetime = None
    user_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class CacheConfig:
    """Cache configuration for different operation types."""
    ttl: int = 3600  # Time to live in seconds
    max_size: int = 1000  # Maximum number of items
    key_prefix: str = "default"
    compress: bool = False
    enable_distributed: bool = True

class PerformanceOptimizationEngine:
    """Main performance optimization engine."""
    
    def __init__(self):
        self.metrics_buffer = []
        self.cache_configs = {
            "dashboard": CacheConfig(ttl=1800, key_prefix="dash", compress=True),
            "analysis": CacheConfig(ttl=3600, key_prefix="analysis", compress=True), 
            "comparison": CacheConfig(ttl=2400, key_prefix="comparison", compress=True),
            "file_preview": CacheConfig(ttl=7200, key_prefix="preview", compress=False),
            "user_session": CacheConfig(ttl=86400, key_prefix="session", compress=False),
            "chart_data": CacheConfig(ttl=900, key_prefix="chart", compress=True)
        }
        self.performance_thresholds = {
            "slow_query": 2.0,  # seconds
            "memory_warning": 100 * 1024 * 1024,  # 100MB
            "cache_miss_rate": 0.3  # 30%
        }
        
    async def initialize(self):
        """Initialize performance monitoring and optimization systems."""
        try:
            # Initialize cache manager
            await cache_manager.init_redis()
            
            # Start background performance monitoring
            asyncio.create_task(self._performance_monitor_loop())
            asyncio.create_task(self._cache_cleanup_loop())
            
            logger.info("🚀 Performance Optimization Engine initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Performance Engine: {e}")
            return False
    
    def performance_monitor(self, operation_name: str, cache_config: Optional[str] = None):
        """Decorator for monitoring operation performance."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                cache_hit = False
                db_queries = 0
                
                # Generate cache key if caching is enabled
                cache_key = None
                if cache_config:
                    config = self.cache_configs.get(cache_config, CacheConfig())
                    cache_key = self._generate_cache_key(
                        operation_name, args, kwargs, config.key_prefix
                    )
                    
                    # Try to get from cache first
                    cached_result = await self._get_from_cache(cache_key, config)
                    if cached_result is not None:
                        cache_hit = True
                        execution_time = time.time() - start_time
                        await self._record_metrics(
                            operation_name, execution_time, cache_hit=True
                        )
                        return cached_result
                
                # Execute the actual function
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Cache the result if caching is enabled
                    if cache_config and cache_key:
                        await self._store_in_cache(cache_key, result, config)
                    
                    # Record performance metrics
                    await self._record_metrics(
                        operation_name, execution_time, cache_hit=cache_hit,
                        data_size=self._estimate_data_size(result)
                    )
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    await self._record_metrics(
                        operation_name, execution_time, cache_hit=cache_hit
                    )
                    raise e
                    
            return wrapper
        return decorator
    
    async def _get_from_cache(self, cache_key: str, config: CacheConfig) -> Optional[Any]:
        """Get data from cache with configuration."""
        try:
            cached_data = await cache_manager.get(cache_key)
            if cached_data:
                if config.compress:
                    # Decompress if needed
                    return json.loads(cached_data)
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {cache_key}: {e}")
            return None
    
    async def _store_in_cache(self, cache_key: str, data: Any, config: CacheConfig):
        """Store data in cache with configuration."""
        try:
            serialized_data = json.dumps(data, default=str)
            if config.compress:
                # Add compression logic here if needed
                pass
            
            await cache_manager.set(cache_key, serialized_data, expire=config.ttl)
            
        except Exception as e:
            logger.warning(f"Cache store error for key {cache_key}: {e}")
    
    def _generate_cache_key(self, operation: str, args: tuple, kwargs: dict, prefix: str) -> str:
        """Generate a unique cache key for the operation."""
        # Create a hash of the arguments
        arg_string = str(args) + str(sorted(kwargs.items()))
        arg_hash = hashlib.md5(arg_string.encode()).hexdigest()[:12]
        return f"{prefix}:{operation}:{arg_hash}"
    
    def _estimate_data_size(self, data: Any) -> Optional[int]:
        """Estimate the size of data in bytes."""
        try:
            if isinstance(data, str):
                return len(data.encode('utf-8'))
            elif isinstance(data, (dict, list)):
                return len(json.dumps(data, default=str).encode('utf-8'))
            else:
                return len(str(data).encode('utf-8'))
        except:
            return None
    
    async def _record_metrics(self, operation_name: str, execution_time: float, 
                            cache_hit: bool = False, data_size: Optional[int] = None):
        """Record performance metrics."""
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            execution_time=execution_time,
            cache_hit=cache_hit,
            data_size=data_size
        )
        
        self.metrics_buffer.append(metrics)
        
        # Log slow operations
        if execution_time > self.performance_thresholds["slow_query"]:
            logger.warning(f"🐌 Slow operation: {operation_name} took {execution_time:.2f}s")
        
        # Batch store metrics when buffer gets full
        if len(self.metrics_buffer) >= 50:
            await self._store_metrics_batch()
    
    async def _store_metrics_batch(self):
        """Store a batch of metrics to the database."""
        if not self.metrics_buffer:
            return
            
        try:
            # Store metrics in database for analysis
            query = """
                INSERT INTO performance_metrics 
                (operation_name, execution_time, cache_hit, data_size, timestamp)
                VALUES (:operation_name, :execution_time, :cache_hit, :data_size, :timestamp)
            """
            
            # Prepare batch data
            batch_data = []
            for metric in self.metrics_buffer:
                batch_data.append({
                    "operation_name": metric.operation_name,
                    "execution_time": metric.execution_time,
                    "cache_hit": metric.cache_hit,
                    "data_size": metric.data_size,
                    "timestamp": metric.timestamp
                })
            
            # Execute batch insert
            if database.is_connected:
                await database.execute_many(query, batch_data)
                logger.debug(f"📊 Stored {len(batch_data)} performance metrics")
            
            # Clear buffer
            self.metrics_buffer = []
            
        except Exception as e:
            logger.error(f"Failed to store performance metrics: {e}")
            # Clear buffer anyway to prevent memory buildup
            self.metrics_buffer = []
    
    async def _performance_monitor_loop(self):
        """Background loop for performance monitoring."""
        while True:
            try:
                # Store any pending metrics
                if self.metrics_buffer:
                    await self._store_metrics_batch()
                
                # Generate performance report
                await self._generate_performance_report()
                
                # Sleep for 5 minutes
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Performance monitor loop error: {e}")
                await asyncio.sleep(60)
    
    async def _cache_cleanup_loop(self):
        """Background loop for cache cleanup and optimization."""
        while True:
            try:
                # Analyze cache performance
                await self._analyze_cache_performance()
                
                # Sleep for 15 minutes
                await asyncio.sleep(900)
                
            except Exception as e:
                logger.error(f"Cache cleanup loop error: {e}")
                await asyncio.sleep(300)
    
    async def _generate_performance_report(self):
        """Generate performance analysis report."""
        try:
            if not database.is_connected:
                return
                
            # Query recent performance data
            query = """
                SELECT operation_name, 
                       AVG(execution_time) as avg_time,
                       COUNT(*) as operation_count,
                       SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::float / COUNT(*) as cache_hit_rate
                FROM performance_metrics 
                WHERE timestamp > NOW() - INTERVAL '1 hour'
                GROUP BY operation_name
                ORDER BY avg_time DESC
            """
            
            results = await database.fetch_all(query)
            
            if results:
                logger.info("📊 Performance Report (Last Hour):")
                for row in results:
                    cache_rate = (row["cache_hit_rate"] or 0) * 100
                    logger.info(
                        f"  {row['operation_name']}: "
                        f"{row['avg_time']:.3f}s avg, "
                        f"{row['operation_count']} ops, "
                        f"{cache_rate:.1f}% cache hit"
                    )
                    
                    # Alert on poor performance
                    if row["avg_time"] > self.performance_thresholds["slow_query"]:
                        logger.warning(f"⚠️ {row['operation_name']} is performing slowly")
                    
                    if (row["cache_hit_rate"] or 0) < self.performance_thresholds["cache_miss_rate"]:
                        logger.warning(f"⚠️ {row['operation_name']} has low cache hit rate")
        
        except Exception as e:
            logger.debug(f"Performance report generation error: {e}")
    
    async def _analyze_cache_performance(self):
        """Analyze and optimize cache performance."""
        try:
            # This would integrate with Redis INFO commands in a real implementation
            logger.debug("🔍 Analyzing cache performance...")
            
            # Placeholder for cache analysis logic
            # In a real implementation, this would:
            # 1. Check Redis memory usage
            # 2. Analyze hit/miss ratios
            # 3. Identify hot keys
            # 4. Optimize cache configurations
            
        except Exception as e:
            logger.debug(f"Cache analysis error: {e}")
    
    async def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the specified time period."""
        try:
            if not database.is_connected:
                return {"error": "Database not connected"}
            
            query = """
                SELECT 
                    operation_name,
                    COUNT(*) as total_operations,
                    AVG(execution_time) as avg_execution_time,
                    MIN(execution_time) as min_execution_time,
                    MAX(execution_time) as max_execution_time,
                    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::float / COUNT(*) as cache_hit_rate,
                    AVG(COALESCE(data_size, 0)) as avg_data_size
                FROM performance_metrics 
                WHERE timestamp > NOW() - INTERVAL '%s hours'
                GROUP BY operation_name
                ORDER BY total_operations DESC
            """ % hours
            
            results = await database.fetch_all(query)
            
            summary = {
                "time_period_hours": hours,
                "operations": [],
                "total_operations": 0,
                "avg_execution_time": 0,
                "overall_cache_hit_rate": 0
            }
            
            total_ops = 0
            total_time = 0
            total_cache_hits = 0
            
            for row in results:
                op_data = {
                    "operation_name": row["operation_name"],
                    "total_operations": row["total_operations"],
                    "avg_execution_time": round(row["avg_execution_time"], 3),
                    "min_execution_time": round(row["min_execution_time"], 3),
                    "max_execution_time": round(row["max_execution_time"], 3),
                    "cache_hit_rate": round((row["cache_hit_rate"] or 0) * 100, 1),
                    "avg_data_size": int(row["avg_data_size"] or 0)
                }
                summary["operations"].append(op_data)
                
                total_ops += row["total_operations"]
                total_time += row["avg_execution_time"] * row["total_operations"]
                total_cache_hits += (row["cache_hit_rate"] or 0) * row["total_operations"]
            
            if total_ops > 0:
                summary["total_operations"] = total_ops
                summary["avg_execution_time"] = round(total_time / total_ops, 3)
                summary["overall_cache_hit_rate"] = round((total_cache_hits / total_ops) * 100, 1)
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {"error": str(e)}
    
    async def optimize_operation(self, operation_name: str) -> Dict[str, Any]:
        """Provide optimization recommendations for a specific operation."""
        try:
            # Analyze recent performance for this operation
            query = """
                SELECT 
                    AVG(execution_time) as avg_time,
                    MAX(execution_time) as max_time,
                    COUNT(*) as count,
                    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::float / COUNT(*) as cache_rate
                FROM performance_metrics 
                WHERE operation_name = :operation_name 
                AND timestamp > NOW() - INTERVAL '24 hours'
            """
            
            result = await database.fetch_one(query, values={"operation_name": operation_name})
            
            recommendations = []
            
            if result:
                avg_time = result["avg_time"] or 0
                cache_rate = result["cache_rate"] or 0
                
                if avg_time > self.performance_thresholds["slow_query"]:
                    recommendations.append({
                        "type": "performance",
                        "issue": "Slow execution time",
                        "recommendation": "Consider optimizing database queries or adding indexes"
                    })
                
                if cache_rate < self.performance_thresholds["cache_miss_rate"]:
                    recommendations.append({
                        "type": "caching",
                        "issue": "Low cache hit rate",
                        "recommendation": "Review cache configuration and increase TTL"
                    })
                
                if avg_time > 1.0 and cache_rate < 0.5:
                    recommendations.append({
                        "type": "architecture",
                        "issue": "Expensive operation with poor caching",
                        "recommendation": "Consider precomputing results or background processing"
                    })
            
            return {
                "operation_name": operation_name,
                "current_performance": {
                    "avg_execution_time": round(result["avg_time"] or 0, 3),
                    "max_execution_time": round(result["max_time"] or 0, 3),
                    "cache_hit_rate": round((result["cache_rate"] or 0) * 100, 1),
                    "operation_count": result["count"] or 0
                },
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze operation {operation_name}: {e}")
            return {"error": str(e)}

# Global performance engine instance
performance_engine = PerformanceOptimizationEngine()

# Convenience decorators
def monitor_dashboard_performance(func):
    """Decorator for dashboard operations."""
    return performance_engine.performance_monitor("dashboard", "dashboard")(func)

def monitor_analysis_performance(func):
    """Decorator for analysis operations."""
    return performance_engine.performance_monitor("analysis", "analysis")(func)

def monitor_comparison_performance(func):
    """Decorator for comparison operations."""
    return performance_engine.performance_monitor("comparison", "comparison")(func)

def monitor_file_performance(func):
    """Decorator for file operations."""
    return performance_engine.performance_monitor("file_operation", "file_preview")(func) 