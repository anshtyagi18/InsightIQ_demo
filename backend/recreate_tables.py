#!/usr/bin/env python3
"""
Database table recreation script for Analytics Hub.
This script drops existing tables and recreates them with proper auto-incrementing UUIDs.
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://neondb_owner:npg_X7oxFtQ3VzGU@ep-noisy-cell-a8dj7y1d-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
)

# Remove asyncpg driver specification for direct connection
SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")

async def recreate_tables():
    """Drop and recreate all tables with proper schema."""
    
    # Connect directly to PostgreSQL
    conn = await asyncpg.connect(SYNC_DATABASE_URL)
    
    try:
        print("🔄 Dropping existing tables...")
        
        # Drop tables in reverse dependency order
        await conn.execute("DROP TABLE IF EXISTS comparison_results CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS file_uploads CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS analysis_sessions CASCADE;")
        await conn.execute("DROP TABLE IF EXISTS user_sessions CASCADE;")
        
        print("✅ Existing tables dropped")
        
        print("🔨 Creating tables with proper schema...")
        
        # Create analysis_sessions table
        await conn.execute("""
            CREATE TABLE analysis_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id VARCHAR(255) NOT NULL,
                analysis_type VARCHAR(100) NOT NULL,
                file_info JSONB,
                dashboard_config JSONB,
                ai_insights JSONB,
                performance_summary JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create index for analysis_sessions
        await conn.execute("CREATE INDEX idx_analysis_sessions_session_id ON analysis_sessions(session_id);")
        
        # Create file_uploads table
        await conn.execute("""
            CREATE TABLE file_uploads (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                file_hash VARCHAR(255) NOT NULL,
                filename VARCHAR(500) NOT NULL,
                file_size INTEGER,
                mime_type VARCHAR(200),
                upload_path VARCHAR(1000),
                metadata_info JSONB,
                processed BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create index for file_uploads
        await conn.execute("CREATE INDEX idx_file_uploads_file_hash ON file_uploads(file_hash);")
        
        # Create user_sessions table
        await conn.execute("""
            CREATE TABLE user_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_token VARCHAR(500) NOT NULL,
                user_data JSONB,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create index for user_sessions
        await conn.execute("CREATE INDEX idx_user_sessions_session_token ON user_sessions(session_token);")
        
        # Create comparison_results table
        await conn.execute("""
            CREATE TABLE comparison_results (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id VARCHAR(255) NOT NULL,
                estimated_file_hash VARCHAR(255),
                actual_file_hash VARCHAR(255),
                comparison_data JSONB,
                insights JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create index for comparison_results
        await conn.execute("CREATE INDEX idx_comparison_results_session_id ON comparison_results(session_id);")
        
        print("✅ All tables created successfully with proper schema")
        
        # Verify tables exist
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        print(f"📋 Created tables: {[table['table_name'] for table in tables]}")
        
    except Exception as e:
        print(f"❌ Error recreating tables: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    print("🚀 Starting database table recreation...")
    asyncio.run(recreate_tables())
    print("✅ Database table recreation completed!") 