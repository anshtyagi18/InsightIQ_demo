#!/usr/bin/env python3
"""
Fix UUID generation in PostgreSQL for Analytics Hub.
This script enables the uuid-ossp extension and fixes UUID generation.
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

async def fix_uuid_generation():
    """Enable UUID extension and fix UUID generation."""
    
    # Connect directly to PostgreSQL
    conn = await asyncpg.connect(SYNC_DATABASE_URL)
    
    try:
        print("🔧 Enabling UUID extension...")
        
        # Enable uuid-ossp extension (for gen_random_uuid())
        await conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
        print("✅ UUID extension enabled")
        
        # Check current table structure
        print("🔍 Checking current table constraints...")
        
        tables = ['analysis_sessions', 'file_uploads', 'user_sessions', 'comparison_results']
        
        for table in tables:
            # Check if default is properly set
            result = await conn.fetch(f"""
                SELECT column_name, column_default, is_nullable
                FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = 'id';
            """)
            
            if result:
                row = result[0]
                print(f"📋 {table}.id - Default: {row['column_default']}, Nullable: {row['is_nullable']}")
                
                # If the default is not properly set, fix it
                if not row['column_default'] or 'gen_random_uuid' not in str(row['column_default']):
                    print(f"🔧 Fixing default for {table}.id...")
                    await conn.execute(f"""
                        ALTER TABLE {table} 
                        ALTER COLUMN id SET DEFAULT gen_random_uuid();
                    """)
                    print(f"✅ Fixed default for {table}.id")
        
        print("🧪 Testing UUID generation...")
        
        # Test UUID generation
        test_uuid = await conn.fetchval("SELECT gen_random_uuid();")
        print(f"✅ UUID generation working: {test_uuid}")
        
        # Test inserting a record to verify auto-generation
        print("🧪 Testing database insert with auto-generated UUID...")
        
        test_session_id = "test_session_" + str(test_uuid)[:8]
        
        # Test analysis_sessions insert
        try:
            await conn.execute("""
                INSERT INTO analysis_sessions (session_id, analysis_type, file_info, dashboard_config) 
                VALUES ($1, 'test', '{}', '{}')
            """, test_session_id)
            
            # Verify the record was inserted with auto-generated UUID
            result = await conn.fetchrow("""
                SELECT id, session_id FROM analysis_sessions WHERE session_id = $1
            """, test_session_id)
            
            if result and result['id']:
                print(f"✅ Auto UUID generation working! Generated ID: {result['id']}")
                
                # Clean up test record
                await conn.execute("DELETE FROM analysis_sessions WHERE session_id = $1", test_session_id)
                print("🧹 Test record cleaned up")
            else:
                print("❌ UUID auto-generation failed")
                
        except Exception as e:
            print(f"❌ Insert test failed: {e}")
        
        print("✅ UUID generation fix completed successfully!")
        
    except Exception as e:
        print(f"❌ Error fixing UUID generation: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    print("🚀 Starting UUID generation fix...")
    asyncio.run(fix_uuid_generation())
    print("✅ UUID generation fix completed!") 