#!/usr/bin/env python3
"""
Database schema verification script for Analytics Hub.
This script checks the actual PostgreSQL schema to debug UUID generation issues.
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

async def check_database_schema():
    """Check actual database schema and constraints."""
    
    try:
        # Connect directly to PostgreSQL
        conn = await asyncpg.connect(SYNC_DATABASE_URL)
        
        print("🔍 Checking actual database schema...")
        print("=" * 60)
        
        # Check if tables exist
        tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
        
        tables = await conn.fetch(tables_query)
        print(f"📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        print("\n" + "=" * 60)
        
        # Check file_uploads table structure
        if any(t['table_name'] == 'file_uploads' for t in tables):
            print("🔍 Checking file_uploads table schema:")
            
            columns_query = """
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = 'file_uploads' 
                AND table_schema = 'public'
                ORDER BY ordinal_position;
            """
            
            columns = await conn.fetch(columns_query)
            for col in columns:
                print(f"  📊 {col['column_name']}: {col['data_type']}")
                print(f"     ↳ Nullable: {col['is_nullable']}")
                print(f"     ↳ Default: {col['column_default']}")
                if col['character_maximum_length']:
                    print(f"     ↳ Max Length: {col['character_maximum_length']}")
                print()
            
            # Check constraints
            constraints_query = """
                SELECT 
                    constraint_name,
                    constraint_type,
                    column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name
                WHERE tc.table_name = 'file_uploads'
                AND tc.table_schema = 'public';
            """
            
            constraints = await conn.fetch(constraints_query)
            print("🔒 Constraints:")
            for constraint in constraints:
                print(f"  - {constraint['constraint_name']} ({constraint['constraint_type']}) on {constraint['column_name']}")
        
        print("\n" + "=" * 60)
        
        # Test UUID generation directly
        print("🧪 Testing UUID generation:")
        
        try:
            # Test gen_random_uuid() function
            uuid_test = await conn.fetchval("SELECT gen_random_uuid();")
            print(f"✅ gen_random_uuid() works: {uuid_test}")
        except Exception as e:
            print(f"❌ gen_random_uuid() failed: {e}")
        
        # Test a direct insert with minimal data
        print("\n🧪 Testing direct insert:")
        try:
            test_query = """
                INSERT INTO file_uploads (file_hash, filename, file_size, mime_type, upload_path, metadata_info)
                VALUES ('test_hash_123', 'test_file.txt', 100, 'text/plain', '/test/path', '{}')
                RETURNING id, file_hash;
            """
            result = await conn.fetchrow(test_query)
            print(f"✅ Direct insert works! Generated ID: {result['id']}")
            
            # Clean up test data
            await conn.execute("DELETE FROM file_uploads WHERE file_hash = 'test_hash_123';")
            print("🧹 Cleaned up test data")
            
        except Exception as e:
            print(f"❌ Direct insert failed: {e}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_database_schema()) 