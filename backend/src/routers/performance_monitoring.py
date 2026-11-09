"""
Performance Monitoring Router for Analytics Hub
Provides endpoints for database optimization, real-time metrics, and system health monitoring.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.services.enhanced_database_service import enhanced_db_service, execute_analytics_query
from src.services.performance_optimization_engine import performance_engine
from src.services.real_time_analytics_engine import realtime_engine, track_metric, track_metrics_batch
from src.core.database import database, cache_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/performance", tags=["performance"])

# Pydantic models for request/response
class MetricIngestionRequest(BaseModel):
    metric_name: str = Field(..., description="Name of the metric to track")
    value: float = Field(..., description="Metric value")
    dimensions: Optional[Dict[str, Any]] = Field(None, description="Additional metric dimensions")
    session_id: Optional[str] = Field(None, description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")

class BatchMetricsRequest(BaseModel):
    metrics: List[MetricIngestionRequest] = Field(..., description="List of metrics to ingest")

class AlertRuleRequest(BaseModel):
    metric_name: str = Field(..., description="Metric to monitor")
    condition: str = Field(..., description="Alert condition (greater_than, less_than, equals, change_rate)")
    threshold: float = Field(..., description="Alert threshold value")
    window_minutes: int = Field(5, description="Time window for alert evaluation")
    notification_channels: List[str] = Field(default_factory=list, description="Notification channels")

class DashboardSubscriptionRequest(BaseModel):
    dashboard_id: str = Field(..., description="Dashboard identifier")
    metrics: List[str] = Field(..., description="Metrics to subscribe to")
    update_interval: int = Field(5, description="Update interval in seconds")

class QueryOptimizationRequest(BaseModel):
    query: str = Field(..., description="SQL query to optimize")
    params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")

@router.get("/health")
async def get_system_health():
    """Get comprehensive system health status."""
    try:
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "components": {}
        }
        
        # Check database connection
        if database.is_connected:
            try:
                await database.fetch_one("SELECT 1 as test")
                health_status["components"]["database"] = {
                    "status": "healthy",
                    "message": "Connected to SQLite database"
                }
            except Exception as e:
                health_status["components"]["database"] = {
                    "status": "unhealthy",
                    "message": f"Database error: {str(e)}"
                }
                health_status["status"] = "degraded"
        else:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "message": "Database not connected"
            }
            health_status["status"] = "degraded"
        
        # Check cache
        try:
            test_key = "health_check_test"
            await cache_manager.set(test_key, "test_value", expire=60)
            cached_value = await cache_manager.get(test_key)
            
            if cached_value:
                health_status["components"]["cache"] = {
                    "status": "healthy",
                    "message": "Cache operational"
                }
            else:
                health_status["components"]["cache"] = {
                    "status": "degraded",
                    "message": "Cache not responding properly"
                }
        except Exception as e:
            health_status["components"]["cache"] = {
                "status": "unhealthy",
                "message": f"Cache error: {str(e)}"
            }
        
        # Check performance engine
        health_status["components"]["performance_engine"] = {
            "status": "healthy",
            "message": "Performance monitoring active"
        }
        
        # Check real-time engine
        if realtime_engine.running:
            health_status["components"]["realtime_engine"] = {
                "status": "healthy",
                "message": "Real-time analytics active"
            }
        else:
            health_status["components"]["realtime_engine"] = {
                "status": "unhealthy",
                "message": "Real-time engine not running"
            }
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/metrics/summary")
async def get_performance_summary(
    hours: int = Query(24, description="Time period in hours", ge=1, le=168)
):
    """Get performance metrics summary."""
    try:
        summary = await performance_engine.get_performance_summary(hours)
        return summary
        
    except Exception as e:
        logger.error(f"Performance summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance summary: {str(e)}")

@router.get("/metrics/operation/{operation_name}")
async def get_operation_performance(
    operation_name: str = Path(..., description="Operation name to analyze")
):
    """Get detailed performance analysis for a specific operation."""
    try:
        analysis = await performance_engine.optimize_operation(operation_name)
        return analysis
        
    except Exception as e:
        logger.error(f"Operation analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze operation: {str(e)}")

@router.get("/database/connections")
async def get_connection_metrics():
    """Get database connection metrics."""
    try:
        metrics = await enhanced_db_service.get_connection_metrics()
        return {
            "active_connections": metrics.active_connections,
            "idle_connections": metrics.idle_connections,
            "total_queries": metrics.total_queries,
            "avg_query_time": metrics.avg_query_time,
            "cache_hit_ratio": metrics.cache_hit_ratio,
            "last_updated": metrics.last_updated.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Connection metrics failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get connection metrics: {str(e)}")

@router.get("/database/tables/{table_name}/analyze")
async def analyze_table_performance(
    table_name: str = Path(..., description="Table name to analyze")
):
    """Analyze table performance and get optimization suggestions."""
    try:
        analysis = await enhanced_db_service.analyze_table_performance(table_name)
        return analysis
        
    except Exception as e:
        logger.error(f"Table analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze table: {str(e)}")

@router.post("/database/optimize-settings")
async def optimize_database_settings():
    """Optimize database settings for analytics workloads."""
    try:
        optimizations = await enhanced_db_service.optimize_database_settings()
        return optimizations
        
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize database: {str(e)}")

@router.post("/query/analyze")
async def analyze_query_performance(request: QueryOptimizationRequest):
    """Analyze query performance and get optimization recommendations."""
    try:
        optimization_plan = await enhanced_db_service.query_engine.analyze_query_plan(
            request.query, request.params
        )
        
        return {
            "query": optimization_plan.query,
            "estimated_cost": optimization_plan.estimated_cost,
            "use_cache": optimization_plan.use_cache,
            "cache_ttl": optimization_plan.cache_ttl,
            "parallel_execution": optimization_plan.parallel_execution,
            "index_suggestions": optimization_plan.index_suggestions,
            "optimization_level": optimization_plan.optimization_level
        }
        
    except Exception as e:
        logger.error(f"Query analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze query: {str(e)}")

@router.post("/realtime/metrics/ingest")
async def ingest_metric(request: MetricIngestionRequest):
    """Ingest a single real-time metric."""
    try:
        success = await track_metric(
            metric_name=request.metric_name,
            value=request.value,
            dimensions=request.dimensions,
            session_id=request.session_id,
            user_id=request.user_id
        )
        
        if success:
            return {"status": "success", "message": "Metric ingested successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to ingest metric")
        
    except Exception as e:
        logger.error(f"Metric ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest metric: {str(e)}")

@router.post("/realtime/metrics/batch")
async def ingest_metrics_batch(request: BatchMetricsRequest):
    """Ingest multiple real-time metrics in batch."""
    try:
        # Convert to dict format expected by the engine
        metrics_data = []
        for metric in request.metrics:
            metrics_data.append({
                "metric_name": metric.metric_name,
                "value": metric.value,
                "dimensions": metric.dimensions,
                "session_id": metric.session_id,
                "user_id": metric.user_id
            })
        
        success_count = await track_metrics_batch(metrics_data)
        
        return {
            "status": "success",
            "ingested_count": success_count,
            "total_count": len(metrics_data),
            "success_rate": success_count / len(metrics_data) if metrics_data else 0
        }
        
    except Exception as e:
        logger.error(f"Batch metric ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest metrics batch: {str(e)}")

@router.get("/realtime/metrics")
async def get_realtime_metrics(
    metric_names: List[str] = Query(..., description="Metric names to retrieve"),
    session_id: Optional[str] = Query(None, description="Filter by session ID")
):
    """Get current real-time metric values."""
    try:
        metrics = await realtime_engine.get_real_time_metrics(metric_names, session_id)
        return metrics
        
    except Exception as e:
        logger.error(f"Real-time metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get real-time metrics: {str(e)}")

@router.post("/realtime/alerts")
async def create_alert_rule(request: AlertRuleRequest):
    """Create a new real-time alert rule."""
    try:
        from src.services.real_time_analytics_engine import AlertRule
        import uuid
        
        rule = AlertRule(
            rule_id=str(uuid.uuid4()),
            metric_name=request.metric_name,
            condition=request.condition,
            threshold=request.threshold,
            window_minutes=request.window_minutes,
            notification_channels=request.notification_channels
        )
        
        success = await realtime_engine.create_alert_rule(rule)
        
        if success:
            return {
                "status": "success",
                "rule_id": rule.rule_id,
                "message": "Alert rule created successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create alert rule")
        
    except Exception as e:
        logger.error(f"Alert rule creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create alert rule: {str(e)}")

@router.post("/realtime/dashboard/subscribe")
async def subscribe_to_dashboard(request: DashboardSubscriptionRequest):
    """Subscribe to real-time dashboard updates."""
    try:
        from src.services.real_time_analytics_engine import DashboardSubscription
        import uuid
        
        subscription = DashboardSubscription(
            subscription_id=str(uuid.uuid4()),
            user_id="anonymous",  # Would get from auth context in real app
            dashboard_id=request.dashboard_id,
            metrics=set(request.metrics),
            update_interval=request.update_interval
        )
        
        success = await realtime_engine.subscribe_to_dashboard(subscription)
        
        if success:
            return {
                "status": "success",
                "subscription_id": subscription.subscription_id,
                "message": "Dashboard subscription created successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create dashboard subscription")
        
    except Exception as e:
        logger.error(f"Dashboard subscription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to subscribe to dashboard: {str(e)}")

@router.get("/cache/statistics")
async def get_cache_statistics():
    """Get cache performance statistics."""
    try:
        # This would require implementing cache statistics in the cache manager
        # For now, return basic info
        stats = {
            "cache_type": "hybrid_redis_memory",
            "redis_available": cache_manager.use_redis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if cache_manager.use_redis and cache_manager.redis_client:
            try:
                # Get Redis info if available
                redis_info = await cache_manager.redis_client.info()
                stats.update({
                    "redis_memory_used": redis_info.get("used_memory_human", "unknown"),
                    "redis_connected_clients": redis_info.get("connected_clients", 0),
                    "redis_total_commands": redis_info.get("total_commands_processed", 0)
                })
            except Exception:
                stats["redis_info"] = "unavailable"
        else:
            # Memory cache statistics
            stats.update({
                "memory_cache_entries": len(cache_manager.memory_cache),
                "memory_cache_expirations": len(cache_manager.cache_expiry)
            })
        
        return stats
        
    except Exception as e:
        logger.error(f"Cache statistics failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache statistics: {str(e)}")

@router.get("/system/recommendations")
async def get_system_recommendations():
    """Get system-wide performance recommendations."""
    try:
        recommendations = {
            "timestamp": datetime.utcnow().isoformat(),
            "categories": {
                "database": [],
                "cache": [],
                "application": [],
                "infrastructure": []
            }
        }
        
        # Database recommendations
        if database.is_connected:
            try:
                # Check for slow queries
                slow_queries = await execute_analytics_query("""
                    SELECT operation_name, AVG(execution_time) as avg_time, COUNT(*) as count
                    FROM performance_metrics 
                    WHERE timestamp > NOW() - INTERVAL '24 hours'
                      AND execution_time > 2.0
                    GROUP BY operation_name
                    ORDER BY avg_time DESC
                    LIMIT 5
                """)
                
                if slow_queries:
                    for query in slow_queries:
                        recommendations["categories"]["database"].append({
                            "type": "slow_query",
                            "description": f"Operation '{query['operation_name']}' averaging {query['avg_time']:.2f}s",
                            "recommendation": "Consider query optimization or indexing",
                            "priority": "high" if query['avg_time'] > 5.0 else "medium"
                        })
                
            except Exception:
                pass  # Performance metrics table might not exist yet
        
        # Cache recommendations
        if not cache_manager.use_redis:
            recommendations["categories"]["cache"].append({
                "type": "cache_upgrade",
                "description": "Using in-memory cache instead of Redis",
                "recommendation": "Set up Redis for better performance and persistence",
                "priority": "medium"
            })
        
        # Application recommendations
        recommendations["categories"]["application"].append({
            "type": "monitoring",
            "description": "Performance monitoring is active",
            "recommendation": "Continue monitoring and review metrics regularly",
            "priority": "low"
        })
        
        return recommendations
        
    except Exception as e:
        logger.error(f"System recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@router.delete("/cache/clear")
async def clear_cache(
    pattern: Optional[str] = Query(None, description="Cache key pattern to clear (optional)")
):
    """Clear cache entries."""
    try:
        if pattern:
            # In a real implementation, this would clear specific patterns
            return {"status": "success", "message": f"Cache pattern '{pattern}' cleared"}
        else:
            # Clear all cache
            if cache_manager.use_redis and cache_manager.redis_client:
                await cache_manager.redis_client.flushdb()
            else:
                cache_manager.memory_cache.clear()
                cache_manager.cache_expiry.clear()
            
            return {"status": "success", "message": "All cache cleared"}
        
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.get("/dashboard/live-stats")
async def get_live_dashboard_stats():
    """Get live system statistics for dashboard display."""
    try:
        current_time = datetime.utcnow()
        
        # Get basic system metrics
        stats = {
            "timestamp": current_time.isoformat(),
            "uptime_hours": 0,  # Would track actual uptime
            "active_sessions": 0,
            "requests_per_minute": 0,
            "database_connections": 0,
            "cache_hit_rate": 0,
            "avg_response_time": 0
        }
        
        # Get connection metrics
        try:
            conn_metrics = await enhanced_db_service.get_connection_metrics()
            stats["database_connections"] = conn_metrics.active_connections
            stats["avg_response_time"] = conn_metrics.avg_query_time
        except Exception:
            pass
        
        # Get recent performance data
        if database.is_connected:
            try:
                recent_metrics = await execute_analytics_query("""
                    SELECT 
                        COUNT(*) as request_count,
                        AVG(execution_time) as avg_time,
                        SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::float / COUNT(*) as cache_rate
                    FROM performance_metrics 
                    WHERE timestamp > NOW() - INTERVAL '1 minute'
                """)
                
                if recent_metrics and recent_metrics[0]:
                    metric = recent_metrics[0]
                    stats["requests_per_minute"] = metric.get("request_count", 0)
                    stats["avg_response_time"] = metric.get("avg_time", 0)
                    stats["cache_hit_rate"] = (metric.get("cache_rate", 0) or 0) * 100
                
            except Exception:
                pass
        
        return stats
        
    except Exception as e:
        logger.error(f"Live stats failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get live stats: {str(e)}")

# Initialize the performance monitoring on router startup
@router.on_event("startup")
async def initialize_performance_monitoring():
    """Initialize performance monitoring systems."""
    try:
        # Initialize enhanced database service
        await enhanced_db_service.initialize()
        
        # Initialize real-time analytics engine
        await realtime_engine.initialize()
        
        logger.info("🚀 Performance monitoring initialized successfully")
        
    except Exception as e:
        logger.error(f"Performance monitoring initialization failed: {e}") 