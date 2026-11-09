#!/usr/bin/env python3
"""
Database Setup Script for Analytics Hub with Neon PostgreSQL
Initializes database tables and verifies connection.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add the src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# Load environment variables
load_dotenv()

from src.core.database import init_database, engine, Base, AsyncSessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test the database connection."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute("SELECT 1")
            logger.info("✅ Database connection test successful")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False

async def create_all_tables():
    """Create all database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ All database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        return False

async def verify_tables():
    """Verify that all expected tables exist."""
    try:
        async with AsyncSessionLocal() as session:
            # Check for our main tables
            tables = ['analysis_sessions', 'file_uploads', 'user_sessions']
            
            for table in tables:
                result = await session.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    );
                """)
                exists = result.scalar()
                if exists:
                    logger.info(f"✅ Table '{table}' exists")
                else:
                    logger.warning(f"⚠️ Table '{table}' not found")
            
            return True
    except Exception as e:
        logger.error(f"❌ Failed to verify tables: {e}")
        return False

async def main():
    """Main setup function."""
    logger.info("🚀 Starting Analytics Hub Database Setup")
    
    # Check environment variables
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not set")
        logger.info("Please create a .env file in the backend directory with:")
        logger.info("DATABASE_URL=postgresql+asyncpg://neondb_owner:npg_X7oxFtQ3VzGU@ep-noisy-cell-a8dj7y1d-pooler.eastus2.azure.neon.tech/neondb?sslmode=require")
        return False
    
    if "neon" in database_url.lower():
        logger.info("✅ Neon PostgreSQL connection string detected")
    else:
        logger.warning("⚠️ Connection string doesn't appear to be Neon PostgreSQL")
    
    # Test connection
    logger.info("Testing database connection...")
    if not await test_database_connection():
        return False
    
    # Create tables
    logger.info("Creating database tables...")
    if not await create_all_tables():
        return False
    
    # Verify tables
    logger.info("Verifying database tables...")
    if not await verify_tables():
        return False
    
    logger.info("🎉 Database setup completed successfully!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Install dependencies: pip install -r requirements.txt")
    logger.info("2. Add your API keys to the .env file")
    logger.info("3. Start the server: python main.py")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1) 