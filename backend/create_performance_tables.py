"""
Database Migration Script for Performance Monitoring Tables
Creates all necessary tables for performance optimization and real-time analytics.
"""

import asyncio
import logging
import os
from datetime import datetime
from databases import Database
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://neondb_owner:npg_X7oxFtQ3VzGU@ep-noisy-cell-a8dj7y1d-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
)

async def create_performance_tables():
    """Create all performance monitoring tables."""
    
    database = Database(DATABASE_URL)
    
    try:
        await database.connect()
        logger.info("✅ Connected to Neon database")
        
        # Performance metrics table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                operation_name VARCHAR(255) NOT NULL,
                execution_time FLOAT NOT NULL,
                cache_hit BOOLEAN DEFAULT FALSE,
                data_size INTEGER,
                user_id VARCHAR(255),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ Created performance_metrics table")
        
        # Create indexes for performance metrics
        await database.execute("""
            CREATE INDEX IF NOT EXISTS idx_performance_metrics_operation 
            ON performance_metrics(operation_name)
        """)
        
        await database.execute("""
            CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp 
            ON performance_metrics(timestamp)
        """)
        
        await database.execute("""
            CREATE INDEX IF NOT EXISTS idx_performance_metrics_user 
            ON performance_metrics(user_id)
        """)
        logger.info("✅ Created performance_metrics indexes")
        
        # Query optimization history table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS query_optimization_history (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                query_hash VARCHAR(64) NOT NULL,
                original_query TEXT NOT NULL,
                optimized_query TEXT,
                execution_time_before FLOAT,
                execution_time_after FLOAT,
                optimization_suggestions JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ Created query_optimization_history table")
        
        await database.execute("""
            CREATE INDEX IF NOT EXISTS idx_query_optimization_hash 
            ON query_optimization_history(query_hash)
        """)
        
        # Real-time metrics table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS real_time_metrics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                metric_name VARCHAR(255) NOT NULL,
                metric_value FLOAT NOT NULL,
                dimensions JSON,
                session_id VARCHAR(255),
                user_id VARCHAR(255),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ Created real_time_metrics table")
        
        await database.execute("""
            CREATE INDEX IF NOT EXISTS idx_realtime_metrics_name_time 
            ON real_time_metrics(metric_name, timestamp)
        """)
        
        await database.execute("""
            CREATE INDEX IF NOT EXISTS idx_realtime_metrics_session 
            ON real_time_metrics(session_id)
        """)
        
        # Real-time alerts table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS real_time_alerts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
        logger.info("✅ Created real_time_alerts table")
        
        await database.execute("""
            CREATE INDEX IF NOT EXISTS idx_realtime_alerts_rule 
            ON real_time_alerts(rule_id)
        """)
        
        await database.execute("""
            CREATE INDEX IF NOT EXISTS idx_realtime_alerts_triggered 
            ON real_time_alerts(triggered_at)
        """)
        
        # Alert rules table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS alert_rules (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                rule_id VARCHAR(255) UNIQUE NOT NULL,
                metric_name VARCHAR(255) NOT NULL,
                condition VARCHAR(50) NOT NULL,
                threshold FLOAT NOT NULL,
                window_minutes INTEGER DEFAULT 5,
                enabled BOOLEAN DEFAULT TRUE,
                notification_channels JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ Created alert_rules table")
        
        # Dashboard subscriptions table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS dashboard_subscriptions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                subscription_id VARCHAR(255) UNIQUE NOT NULL,
                user_id VARCHAR(255) NOT NULL,
                dashboard_id VARCHAR(255) NOT NULL,
                metrics JSON NOT NULL,
                update_interval INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ Created dashboard_subscriptions table")
        
        # System health metrics table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS system_health_metrics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                metric_type VARCHAR(100) NOT NULL,
                metric_name VARCHAR(255) NOT NULL,
                metric_value FLOAT NOT NULL,
                metric_unit VARCHAR(50),
                additional_data JSON,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ Created system_health_metrics table")
        
        await database.execute("""
            CREATE INDEX IF NOT EXISTS idx_system_health_type_time 
            ON system_health_metrics(metric_type, timestamp)
        """)
        
        # Database optimization recommendations table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS optimization_recommendations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                recommendation_type VARCHAR(100) NOT NULL,
                priority VARCHAR(20) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                action_required TEXT,
                estimated_impact VARCHAR(50),
                table_name VARCHAR(255),
                query_pattern TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'pending',
                applied_at TIMESTAMP
            )
        """)
        logger.info("✅ Created optimization_recommendations table")
        
        # Cache performance metrics table
        await database.execute("""
            CREATE TABLE IF NOT EXISTS cache_performance_metrics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                cache_type VARCHAR(50) NOT NULL,
                operation VARCHAR(50) NOT NULL,
                hit_count INTEGER DEFAULT 0,
                miss_count INTEGER DEFAULT 0,
                total_requests INTEGER DEFAULT 0,
                avg_response_time FLOAT,
                memory_usage BIGINT,
                eviction_count INTEGER DEFAULT 0,
                measurement_window_start TIMESTAMP NOT NULL,
                measurement_window_end TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("✅ Created cache_performance_metrics table")
        
        # Add some sample optimization recommendations
        await database.execute("""
            INSERT INTO optimization_recommendations 
            (recommendation_type, priority, title, description, action_required, estimated_impact)
            VALUES 
            ('index', 'high', 'Add index on analysis_sessions.session_id', 
             'Frequent queries on session_id would benefit from an index', 
             'CREATE INDEX idx_analysis_sessions_session_id ON analysis_sessions(session_id)',
             'high'),
            ('query', 'medium', 'Optimize dashboard data queries', 
             'Dashboard queries could be optimized with better aggregation strategies', 
             'Review and optimize dashboard generation queries',
             'medium'),
            ('cache', 'low', 'Implement Redis caching', 
             'Setting up Redis would improve cache performance over in-memory caching', 
             'Configure Redis connection and update cache strategy',
             'medium')
            ON CONFLICT DO NOTHING
        """)
        logger.info("✅ Added sample optimization recommendations")
        
        # Create a view for performance summary
        await database.execute("""
            CREATE OR REPLACE VIEW performance_summary AS
            SELECT 
                operation_name,
                COUNT(*) as total_operations,
                AVG(execution_time) as avg_execution_time,
                MIN(execution_time) as min_execution_time,
                MAX(execution_time) as max_execution_time,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY execution_time) as median_execution_time,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time) as p95_execution_time,
                SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::float / COUNT(*) as cache_hit_rate,
                DATE_TRUNC('hour', timestamp) as hour_bucket
            FROM performance_metrics 
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            GROUP BY operation_name, DATE_TRUNC('hour', timestamp)
            ORDER BY hour_bucket DESC, avg_execution_time DESC
        """)
        logger.info("✅ Created performance_summary view")
        
        # Create a view for real-time dashboard
        await database.execute("""
            CREATE OR REPLACE VIEW real_time_dashboard AS
            SELECT 
                metric_name,
                AVG(metric_value) as avg_value,
                MIN(metric_value) as min_value,
                MAX(metric_value) as max_value,
                COUNT(*) as data_points,
                DATE_TRUNC('minute', timestamp) as minute_bucket
            FROM real_time_metrics 
            WHERE timestamp > NOW() - INTERVAL '1 hour'
            GROUP BY metric_name, DATE_TRUNC('minute', timestamp)
            ORDER BY minute_bucket DESC
        """)
        logger.info("✅ Created real_time_dashboard view")
        
        # Add trigger to automatically update updated_at timestamp
        await database.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        """)
        
        await database.execute("""
            CREATE TRIGGER update_alert_rules_updated_at 
            BEFORE UPDATE ON alert_rules 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """)
        logger.info("✅ Created update triggers")
        
        logger.info("🎉 All performance monitoring tables created successfully!")
        
        # Verify tables were created
        tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN (
                'performance_metrics', 'query_optimization_history', 'real_time_metrics',
                'real_time_alerts', 'alert_rules', 'dashboard_subscriptions',
                'system_health_metrics', 'optimization_recommendations', 'cache_performance_metrics'
            )
            ORDER BY table_name
        """
        
        tables = await database.fetch_all(tables_query)
        logger.info(f"📊 Created {len(tables)} performance tables:")
        for table in tables:
            logger.info(f"  - {table['table_name']}")
        
    except Exception as e:
        logger.error(f"❌ Failed to create performance tables: {e}")
        raise
    finally:
        await database.disconnect()
        logger.info("✅ Database connection closed")

async def verify_performance_tables():
    """Verify all performance tables exist and are accessible."""
    
    database = Database(DATABASE_URL)
    
    try:
        await database.connect()
        logger.info("🔍 Verifying performance tables...")
        
        # Test each table
        tables_to_test = [
            'performance_metrics',
            'query_optimization_history', 
            'real_time_metrics',
            'real_time_alerts',
            'alert_rules',
            'dashboard_subscriptions',
            'system_health_metrics',
            'optimization_recommendations',
            'cache_performance_metrics'
        ]
        
        for table in tables_to_test:
            try:
                count = await database.fetch_one(f"SELECT COUNT(*) as count FROM {table}")
                logger.info(f"✅ {table}: {count['count']} rows")
            except Exception as e:
                logger.error(f"❌ {table}: {e}")
        
        # Test views
        views_to_test = ['performance_summary', 'real_time_dashboard']
        for view in views_to_test:
            try:
                result = await database.fetch_one(f"SELECT COUNT(*) as count FROM {view}")
                logger.info(f"✅ {view} view: {result['count']} rows")
            except Exception as e:
                logger.error(f"❌ {view} view: {e}")
        
        logger.info("🎉 Performance tables verification complete!")
        
    except Exception as e:
        logger.error(f"❌ Performance tables verification failed: {e}")
        raise
    finally:
        await database.disconnect()

async def main():
    """Main function to create and verify performance tables."""
    logger.info("🚀 Starting Performance Tables Migration")
    logger.info("=" * 50)
    
    try:
        # Create tables
        await create_performance_tables()
        
        logger.info("=" * 50)
        
        # Verify tables
        await verify_performance_tables()
        
        logger.info("=" * 50)
        logger.info("🎉 Performance monitoring database setup complete!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Start the Analytics Hub API server")
        logger.info("2. Check /api/v1/performance/health for system status")
        logger.info("3. View performance metrics at /api/v1/performance/metrics/summary")
        logger.info("4. Monitor real-time metrics at /api/v1/performance/realtime/metrics")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main()) 