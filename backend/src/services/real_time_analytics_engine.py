"""
Real-Time Analytics Engine for Analytics Hub
Provides streaming data processing, live dashboard updates, and real-time insights.
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import uuid
import websockets
from contextlib import asynccontextmanager

from src.core.database import database, cache_manager
from src.services.enhanced_database_service import enhanced_db_service
from src.services.performance_optimization_engine import performance_engine, monitor_analysis_performance

logger = logging.getLogger(__name__)

@dataclass
class StreamingMetric:
    """Real-time streaming metric data point."""
    metric_name: str
    value: float
    timestamp: datetime
    dimensions: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    user_id: Optional[str] = None

@dataclass
class AlertRule:
    """Real-time alerting rule configuration."""
    rule_id: str
    metric_name: str
    condition: str  # "greater_than", "less_than", "equals", "change_rate"
    threshold: float
    window_minutes: int = 5
    enabled: bool = True
    notification_channels: List[str] = field(default_factory=list)

@dataclass
class DashboardSubscription:
    """Live dashboard subscription tracking."""
    subscription_id: str
    user_id: str
    dashboard_id: str
    metrics: Set[str]
    websocket_id: Optional[str] = None
    last_update: datetime = field(default_factory=datetime.utcnow)
    update_interval: int = 5  # seconds

class MetricsAggregator:
    """Real-time metrics aggregation engine."""
    
    def __init__(self, window_size: int = 300):  # 5 minutes default
        self.window_size = window_size
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.aggregated_metrics = {}
        self.alert_rules = {}
        
    async def add_metric(self, metric: StreamingMetric):
        """Add a new metric data point."""
        try:
            # Add to buffer
            metric_key = f"{metric.metric_name}:{metric.session_id}"
            self.metrics_buffer[metric_key].append(metric)
            
            # Trigger real-time aggregation
            await self._update_aggregations(metric_key)
            
            # Check alert rules
            await self._check_alert_rules(metric)
            
        except Exception as e:
            logger.error(f"Failed to add metric: {e}")
    
    async def _update_aggregations(self, metric_key: str):
        """Update real-time aggregations for a metric."""
        try:
            metrics = list(self.metrics_buffer[metric_key])
            if not metrics:
                return
            
            # Calculate time-windowed aggregations
            current_time = datetime.utcnow()
            window_start = current_time - timedelta(seconds=self.window_size)
            
            # Filter metrics within window
            windowed_metrics = [
                m for m in metrics 
                if m.timestamp >= window_start
            ]
            
            if not windowed_metrics:
                return
            
            # Calculate aggregations
            values = [m.value for m in windowed_metrics]
            aggregations = {
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "latest": values[-1],
                "timestamp": current_time,
                "window_start": window_start
            }
            
            # Add trend calculation
            if len(values) >= 2:
                recent_half = values[len(values)//2:]
                older_half = values[:len(values)//2]
                if older_half:
                    recent_avg = sum(recent_half) / len(recent_half)
                    older_avg = sum(older_half) / len(older_half)
                    trend = ((recent_avg - older_avg) / older_avg) * 100 if older_avg != 0 else 0
                    aggregations["trend_percent"] = trend
            
            self.aggregated_metrics[metric_key] = aggregations
            
        except Exception as e:
            logger.error(f"Aggregation update failed for {metric_key}: {e}")
    
    async def _check_alert_rules(self, metric: StreamingMetric):
        """Check if metric triggers any alert rules."""
        try:
            for rule in self.alert_rules.values():
                if rule.metric_name == metric.metric_name and rule.enabled:
                    await self._evaluate_alert_rule(rule, metric)
                    
        except Exception as e:
            logger.error(f"Alert rule checking failed: {e}")
    
    async def _evaluate_alert_rule(self, rule: AlertRule, metric: StreamingMetric):
        """Evaluate a single alert rule against a metric."""
        try:
            metric_key = f"{metric.metric_name}:{metric.session_id}"
            
            if rule.condition == "greater_than" and metric.value > rule.threshold:
                await self._trigger_alert(rule, metric, f"Value {metric.value} exceeds threshold {rule.threshold}")
            
            elif rule.condition == "less_than" and metric.value < rule.threshold:
                await self._trigger_alert(rule, metric, f"Value {metric.value} below threshold {rule.threshold}")
            
            elif rule.condition == "equals" and abs(metric.value - rule.threshold) < 0.001:
                await self._trigger_alert(rule, metric, f"Value {metric.value} equals threshold {rule.threshold}")
            
            elif rule.condition == "change_rate":
                # Check rate of change over window
                aggregations = self.aggregated_metrics.get(metric_key, {})
                if "trend_percent" in aggregations:
                    change_rate = abs(aggregations["trend_percent"])
                    if change_rate > rule.threshold:
                        await self._trigger_alert(rule, metric, f"Change rate {change_rate:.1f}% exceeds threshold {rule.threshold}%")
            
        except Exception as e:
            logger.error(f"Alert rule evaluation failed: {e}")
    
    async def _trigger_alert(self, rule: AlertRule, metric: StreamingMetric, message: str):
        """Trigger an alert notification."""
        try:
            alert_data = {
                "alert_id": str(uuid.uuid4()),
                "rule_id": rule.rule_id,
                "metric_name": metric.metric_name,
                "message": message,
                "value": metric.value,
                "threshold": rule.threshold,
                "timestamp": metric.timestamp.isoformat(),
                "session_id": metric.session_id,
                "user_id": metric.user_id
            }
            
            # Store alert in database
            if database.is_connected:
                await database.execute("""
                    INSERT INTO real_time_alerts 
                    (alert_id, rule_id, metric_name, message, metric_value, threshold_value, 
                     triggered_at, session_id, user_id, alert_data)
                    VALUES (:alert_id, :rule_id, :metric_name, :message, :value, :threshold,
                            :timestamp, :session_id, :user_id, :alert_data)
                """, values={
                    "alert_id": alert_data["alert_id"],
                    "rule_id": rule.rule_id,
                    "metric_name": metric.metric_name,
                    "message": message,
                    "value": metric.value,
                    "threshold": rule.threshold,
                    "timestamp": metric.timestamp,
                    "session_id": metric.session_id,
                    "user_id": metric.user_id,
                    "alert_data": json.dumps(alert_data)
                })
            
            logger.warning(f"🚨 Alert triggered: {message}")
            
        except Exception as e:
            logger.error(f"Alert trigger failed: {e}")
    
    def get_current_aggregations(self, metric_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get current aggregated metrics."""
        if metric_names:
            return {
                key: value for key, value in self.aggregated_metrics.items()
                if any(key.startswith(f"{name}:") for name in metric_names)
            }
        return dict(self.aggregated_metrics)

class RealTimeAnalyticsEngine:
    """Main real-time analytics engine."""
    
    def __init__(self):
        self.metrics_aggregator = MetricsAggregator()
        self.dashboard_subscriptions = {}
        self.websocket_connections = {}
        self.data_streams = {}
        self.running = False
        
    async def initialize(self):
        """Initialize the real-time analytics engine."""
        try:
            # Ensure real-time tables exist
            await self._ensure_realtime_tables()
            
            # Start background tasks
            asyncio.create_task(self._metrics_processing_loop())
            asyncio.create_task(self._dashboard_update_loop())
            asyncio.create_task(self._cleanup_loop())
            
            self.running = True
            logger.info("🚀 Real-Time Analytics Engine initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Real-Time Analytics Engine: {e}")
            return False
    
    async def _ensure_realtime_tables(self):
        """Ensure real-time analytics tables exist."""
        try:
            if not database.is_connected:
                return
            
            # Real-time metrics table
            await database.execute("""
                CREATE TABLE IF NOT EXISTS real_time_metrics (
                    id TEXT PRIMARY KEY,
                    metric_name VARCHAR(255) NOT NULL,
                    metric_value FLOAT NOT NULL,
                    dimensions JSON,
                    session_id VARCHAR(255),
                    user_id VARCHAR(255),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await database.execute("""
                CREATE INDEX IF NOT EXISTS idx_realtime_metrics_name_time 
                ON real_time_metrics(metric_name, timestamp)
            """)
            
            # Real-time alerts table
            await database.execute("""
                CREATE TABLE IF NOT EXISTS real_time_alerts (
                    id TEXT PRIMARY KEY,
                    alert_id VARCHAR(255) NOT NULL,
                    rule_id VARCHAR(255) NOT NULL,
                    metric_name VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    metric_value FLOAT,
                    threshold_value FLOAT,
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_id VARCHAR(255),
                    user_id VARCHAR(255),
                    alert_data JSON,
                    acknowledged BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Alert rules table
            await database.execute("""
                CREATE TABLE IF NOT EXISTS alert_rules (
                    rule_id VARCHAR(255) PRIMARY KEY,
                    metric_name VARCHAR(255) NOT NULL,
                    condition VARCHAR(50) NOT NULL,
                    threshold FLOAT NOT NULL,
                    window_minutes INTEGER DEFAULT 5,
                    enabled BOOLEAN DEFAULT TRUE,
                    notification_channels JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Dashboard subscriptions table
            await database.execute("""
                CREATE TABLE IF NOT EXISTS dashboard_subscriptions (
                    subscription_id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    dashboard_id VARCHAR(255) NOT NULL,
                    metrics JSON NOT NULL,
                    update_interval INTEGER DEFAULT 5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            logger.info("✅ Real-time analytics tables ensured")
            
        except Exception as e:
            logger.warning(f"Real-time tables creation failed: {e}")
    
    @monitor_analysis_performance
    async def ingest_metric(self, metric_name: str, value: float, 
                          dimensions: Optional[Dict] = None,
                          session_id: Optional[str] = None,
                          user_id: Optional[str] = None):
        """Ingest a real-time metric."""
        try:
            metric = StreamingMetric(
                metric_name=metric_name,
                value=value,
                timestamp=datetime.utcnow(),
                dimensions=dimensions or {},
                session_id=session_id,
                user_id=user_id
            )
            
            # Add to aggregator
            await self.metrics_aggregator.add_metric(metric)
            
            # Store in database for historical analysis
            if database.is_connected:
                await database.execute("""
                    INSERT INTO real_time_metrics 
                    (metric_name, metric_value, dimensions, session_id, user_id, timestamp)
                    VALUES (:metric_name, :value, :dimensions, :session_id, :user_id, :timestamp)
                """, values={
                    "metric_name": metric_name,
                    "value": value,
                    "dimensions": json.dumps(dimensions or {}),
                    "session_id": session_id,
                    "user_id": user_id,
                    "timestamp": metric.timestamp
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Metric ingestion failed: {e}")
            return False
    
    async def ingest_batch_metrics(self, metrics: List[Dict[str, Any]]) -> int:
        """Ingest multiple metrics in batch."""
        try:
            success_count = 0
            
            # Process metrics in parallel
            tasks = []
            for metric_data in metrics:
                # Skip invalid metrics
                metric_name = metric_data.get("metric_name")
                value = metric_data.get("value")
                
                if not metric_name or value is None:
                    continue
                    
                task = self.ingest_metric(
                    metric_name,
                    float(value),
                    metric_data.get("dimensions"),
                    metric_data.get("session_id"),
                    metric_data.get("user_id")
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            
            logger.info(f"📊 Batch ingested {success_count}/{len(metrics)} metrics")
            return success_count
            
        except Exception as e:
            logger.error(f"Batch metric ingestion failed: {e}")
            return 0
    
    async def create_alert_rule(self, rule: AlertRule) -> bool:
        """Create a new alert rule."""
        try:
            self.metrics_aggregator.alert_rules[rule.rule_id] = rule
            
            # Store in database
            if database.is_connected:
                await database.execute("""
                    INSERT INTO alert_rules 
                    (rule_id, metric_name, condition, threshold, window_minutes, enabled, 
                     notification_channels, created_at)
                    VALUES (:rule_id, :metric_name, :condition, :threshold, :window_minutes, 
                            :enabled, :notification_channels, :created_at)
                    ON CONFLICT (rule_id) DO UPDATE SET
                        metric_name = EXCLUDED.metric_name,
                        condition = EXCLUDED.condition,
                        threshold = EXCLUDED.threshold,
                        window_minutes = EXCLUDED.window_minutes,
                        enabled = EXCLUDED.enabled,
                        notification_channels = EXCLUDED.notification_channels
                """, values={
                    "rule_id": rule.rule_id,
                    "metric_name": rule.metric_name,
                    "condition": rule.condition,
                    "threshold": rule.threshold,
                    "window_minutes": rule.window_minutes,
                    "enabled": rule.enabled,
                    "notification_channels": json.dumps(rule.notification_channels),
                    "created_at": datetime.utcnow()
                })
            
            logger.info(f"✅ Alert rule created: {rule.rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Alert rule creation failed: {e}")
            return False
    
    async def subscribe_to_dashboard(self, subscription: DashboardSubscription) -> bool:
        """Subscribe to real-time dashboard updates."""
        try:
            self.dashboard_subscriptions[subscription.subscription_id] = subscription
            
            # Store in database
            if database.is_connected:
                await database.execute("""
                    INSERT INTO dashboard_subscriptions 
                    (subscription_id, user_id, dashboard_id, metrics, update_interval, created_at)
                    VALUES (:subscription_id, :user_id, :dashboard_id, :metrics, :update_interval, :created_at)
                    ON CONFLICT (subscription_id) DO UPDATE SET
                        metrics = EXCLUDED.metrics,
                        update_interval = EXCLUDED.update_interval,
                        last_updated = CURRENT_TIMESTAMP
                """, values={
                    "subscription_id": subscription.subscription_id,
                    "user_id": subscription.user_id,
                    "dashboard_id": subscription.dashboard_id,
                    "metrics": json.dumps(list(subscription.metrics)),
                    "update_interval": subscription.update_interval,
                    "created_at": datetime.utcnow()
                })
            
            logger.info(f"✅ Dashboard subscription created: {subscription.subscription_id}")
            return True
            
        except Exception as e:
            logger.error(f"Dashboard subscription failed: {e}")
            return False
    
    async def get_real_time_metrics(self, metric_names: List[str], 
                                  session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current real-time metric values."""
        try:
            # Get aggregated metrics
            aggregations = self.metrics_aggregator.get_current_aggregations(metric_names)
            
            # Filter by session if specified
            if session_id:
                filtered_aggregations = {
                    key: value for key, value in aggregations.items()
                    if key.endswith(f":{session_id}")
                }
                aggregations = filtered_aggregations
            
            # Format response
            response = {
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": {},
                "summary": {
                    "total_metrics": len(aggregations),
                    "window_size_seconds": self.metrics_aggregator.window_size
                }
            }
            
            for key, agg in aggregations.items():
                metric_name = key.split(":")[0]
                if metric_name not in response["metrics"]:
                    response["metrics"][metric_name] = []
                
                response["metrics"][metric_name].append({
                    "session_id": key.split(":", 1)[1] if ":" in key else None,
                    "aggregations": agg
                })
            
            return response
            
        except Exception as e:
            logger.error(f"Real-time metrics retrieval failed: {e}")
            return {"error": str(e)}
    
    async def _metrics_processing_loop(self):
        """Background loop for processing metrics."""
        while self.running:
            try:
                # Process any pending metrics aggregations
                await asyncio.sleep(1)  # Process every second
                
            except Exception as e:
                logger.error(f"Metrics processing loop error: {e}")
                await asyncio.sleep(5)
    
    async def _dashboard_update_loop(self):
        """Background loop for updating dashboard subscriptions."""
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                for subscription in list(self.dashboard_subscriptions.values()):
                    # Check if update is due
                    time_since_update = (current_time - subscription.last_update).total_seconds()
                    
                    if time_since_update >= subscription.update_interval:
                        await self._send_dashboard_update(subscription)
                        subscription.last_update = current_time
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Dashboard update loop error: {e}")
                await asyncio.sleep(5)
    
    async def _send_dashboard_update(self, subscription: DashboardSubscription):
        """Send real-time update to a dashboard subscription."""
        try:
            # Get current metrics for subscription
            metrics_data = await self.get_real_time_metrics(list(subscription.metrics))
            
            update_message = {
                "type": "dashboard_update",
                "subscription_id": subscription.subscription_id,
                "dashboard_id": subscription.dashboard_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": metrics_data
            }
            
            # Send via WebSocket if connected
            if subscription.websocket_id and subscription.websocket_id in self.websocket_connections:
                websocket = self.websocket_connections[subscription.websocket_id]
                await websocket.send(json.dumps(update_message))
            
        except Exception as e:
            logger.debug(f"Dashboard update send failed: {e}")
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while self.running:
            try:
                # Clean up old metrics (keep last 24 hours)
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                if database.is_connected:
                    deleted_count = await database.execute("""
                        DELETE FROM real_time_metrics 
                        WHERE timestamp < :cutoff_time
                    """, values={"cutoff_time": cutoff_time})
                    
                    if deleted_count and deleted_count > 0:
                        logger.info(f"🧹 Cleaned up {deleted_count} old real-time metrics")
                
                # Sleep for 1 hour
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(1800)  # Retry in 30 minutes

# Global real-time analytics engine instance
realtime_engine = RealTimeAnalyticsEngine()

# Convenience functions
async def track_metric(metric_name: str, value: float, session_id: Optional[str] = None,
                      dimensions: Optional[Dict] = None, user_id: Optional[str] = None):
    """Track a real-time metric."""
    return await realtime_engine.ingest_metric(metric_name, value, dimensions, session_id, user_id)

async def track_metrics_batch(metrics: List[Dict]) -> int:
    """Track multiple metrics in batch."""
    return await realtime_engine.ingest_batch_metrics(metrics)

async def create_performance_alert(metric_name: str, threshold: float, 
                                 condition: str = "greater_than") -> Optional[str]:
    """Create a performance monitoring alert."""
    rule_id = f"perf_alert_{int(time.time())}"
    rule = AlertRule(
        rule_id=rule_id,
        metric_name=metric_name,
        condition=condition,
        threshold=threshold,
        window_minutes=5
    )
    
    success = await realtime_engine.create_alert_rule(rule)
    return rule_id if success else None 