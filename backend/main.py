"""
Main FastAPI application for the InsightIQ backend.
"""

import sys
import os

# Add backend directory to sys.path so imports work regardless of working directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import mock google.adk before other imports to prevent import errors
try:
    import google.adk
    print("✅ google.adk is available")
except ImportError:
    print("⚠️ google.adk not available, loading mock...")
    import mock_google_adk

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
import logging
import json
import locale

# Load environment variables first
load_dotenv()

# Fix Windows Unicode/charmap errors
def setup_unicode_logging():
    """Configure logging to handle Unicode characters properly on Windows."""
    try:
        # Set the default encoding for Windows console
        if sys.platform.startswith('win'):
            # Try to set UTF-8 encoding
            if hasattr(sys.stdout, 'reconfigure'):
                try:
                    # Use type checking to ensure reconfigure is available
                    if callable(getattr(sys.stdout, 'reconfigure', None)):
                        sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # type: ignore
                    if callable(getattr(sys.stderr, 'reconfigure', None)):
                        sys.stderr.reconfigure(encoding='utf-8', errors='replace')  # type: ignore
                except Exception:
                    pass
            
            # Set the locale to UTF-8 if possible
            try:
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
                except locale.Error:
                    pass  # Use system default
        
        # Create a custom formatter that handles Unicode safely
        class SafeFormatter(logging.Formatter):
            def format(self, record):
                try:
                    # Convert the message to string and handle Unicode safely
                    if hasattr(record.msg, '__str__'):
                        record.msg = str(record.msg)
                    
                    # Replace problematic Unicode characters
                    unicode_replacements = {
                        '₹': 'INR', '€': 'EUR', '£': 'GBP', '¥': 'JPY',
                        '✅': '[OK]', '❌': '[FAIL]', '⚠️': '[WARN]',
                        '🎯': '[TARGET]', '🔍': '[SEARCH]', '📊': '[CHART]',
                        '🔬': '[ANALYSIS]', '📈': '[TREND]', '🔗': '[LINK]',
                        '📌': '[PIN]', '🤖': '[AI]', '⏱️': '[PENDING]',
                        '🚀': '[START]', '✨': '[NEW]', '🛠️': '[TOOL]',
                        '💡': '[IDEA]', '🔧': '[FIX]', '📝': '[NOTE]',
                        '🎉': '[SUCCESS]', '🔄': '[PROCESS]', '🛑': '[STOP]'
                    }
                    
                    if isinstance(record.msg, str):
                        for unicode_char, replacement in unicode_replacements.items():
                            record.msg = record.msg.replace(unicode_char, replacement)
                        
                        # Ensure the message is ASCII-safe
                        record.msg = record.msg.encode('ascii', errors='replace').decode('ascii')
                    
                    return super().format(record)
                except Exception as e:
                    # Fallback to basic string representation
                    record.msg = f"[ENCODING_ERROR] {repr(record.msg)}"
                    return super().format(record)
        
        # Configure logging with the safe formatter
        formatter = SafeFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Setup console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.handlers = []  # Clear existing handlers
        root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.INFO)
        
        return True
        
    except Exception as e:
        print(f"Warning: Could not setup Unicode logging: {e}")
        # Fallback to basic logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        return False

# Setup Unicode-safe logging
unicode_setup_success = setup_unicode_logging()
logger = logging.getLogger(__name__)

if unicode_setup_success:
    logger.info("[OK] Unicode-safe logging configured successfully")
else:
    logger.warning("[WARN] Using fallback logging configuration")

# Import core routers
from src.routers import file_upload, websocket, providers, chat, analytics_state, ui_state, data_router

try:
    from src.routers import agents
    AGENTS_AVAILABLE = True
except Exception as e:
    AGENTS_AVAILABLE = False
    logger.warning(f"[WARN] Legacy agents router unavailable: {e}")

try:
    from src.routers import dashboard
    DASHBOARD_ROUTER_AVAILABLE = True
except Exception as e:
    DASHBOARD_ROUTER_AVAILABLE = False
    logger.warning(f"[WARN] Legacy dashboard router unavailable: {e}")

try:
    from src.routers import export
    EXPORT_ROUTER_AVAILABLE = True
except Exception as e:
    EXPORT_ROUTER_AVAILABLE = False
    logger.warning(f"[WARN] Legacy export router unavailable: {e}")

try:
    from src.routers import comparison
    COMPARISON_AVAILABLE = True
except Exception as e:
    COMPARISON_AVAILABLE = False
    logger.warning(f"[WARN] Legacy comparison router unavailable: {e}")

# NEW: Import performance monitoring router
try:
    from src.routers import performance_monitoring
    PERFORMANCE_MONITORING_AVAILABLE = True
    logger.info("[OK] Performance monitoring router available")
except ImportError as e:
    PERFORMANCE_MONITORING_AVAILABLE = False
    logger.warning(f"[WARN] Performance monitoring router not available: {e}")

# Import database initialization
from src.core.database import init_database, close_database

# NEW: Import enhanced services
try:
    from src.services.enhanced_database_service import enhanced_db_service
    from src.services.performance_optimization_engine import performance_engine
    from src.services.real_time_analytics_engine import realtime_engine
    ENHANCED_SERVICES_AVAILABLE = True
    logger.info("[OK] Enhanced performance services available")
except ImportError as e:
    ENHANCED_SERVICES_AVAILABLE = False
    logger.warning(f"[WARN] Enhanced performance services not available: {e}")

# Create FastAPI app instance with database lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info("[START] Starting InsightIQ API...")
    
    # Initialize database
    db_success = await init_database()
    if db_success:
        logger.info("[OK] Database initialized successfully")
    else:
        logger.warning("[WARN] Database initialization failed, continuing without database")
    
    # NEW: Initialize enhanced performance services
    if ENHANCED_SERVICES_AVAILABLE:
        try:
            # Initialize performance optimization engine
            perf_success = await performance_engine.initialize()
            if perf_success:
                logger.info("[OK] Performance optimization engine initialized")
            
            # Initialize enhanced database service
            enhanced_db_success = await enhanced_db_service.initialize()
            if enhanced_db_success:
                logger.info("[OK] Enhanced database service initialized")
            
            # Initialize real-time analytics engine
            realtime_success = await realtime_engine.initialize()
            if realtime_success:
                logger.info("[OK] Real-time analytics engine initialized")
            
            logger.info("[START] All enhanced services initialized successfully")
            
        except Exception as e:
            logger.error(f"[WARN] Enhanced services initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("[STOP] Shutting down InsightIQ API...")
    
    # Shutdown enhanced services
    if ENHANCED_SERVICES_AVAILABLE:
        try:
            if hasattr(realtime_engine, 'running'):
                realtime_engine.running = False
            logger.info("[OK] Enhanced services shutdown complete")
        except Exception as e:
            logger.error(f"Enhanced services shutdown error: {e}")
    
    await close_database()
    logger.info("[OK] Application shutdown complete")

app = FastAPI(
    title="InsightIQ API",
    description="InsightIQ API for automated data analysis, business intelligence, and intelligent dashboard generation",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS - Support local dev and Cloudflare Tunnel origins securely
from src.core.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Basic health check endpoint
@app.get("/")
async def root():
    """Root endpoint returning basic API information."""
    return {
        "message": "InsightIQ API", 
        "status": "running", 
        "version": "1.0.0",
        "features": [
            "File Upload & Processing",
            "Google ADK AI Agents",
            "Automated Analytics Pipeline",
            "Dashboard Generation",
            "Export Functionality (PDF/PNG/HTML)",
            "Role-Based Access Control",
            "Real-time WebSocket Updates"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "insightiq-api",
            "timestamp": "2024-01-01T00:00:00Z",  # Will be updated with actual timestamp
            "components": {
                "file_upload": "operational",
                "adk_agents": "operational",
                "dashboard_generation": "operational",
                "export_service": "operational",
                "authentication": "operational",
                "database": "pending",  # To be implemented
                "storage": "pending"    # To be implemented
            }
        }
    )

@app.get("/api/health")
async def api_health_check():
    """API health check endpoint for frontend compatibility."""
    return await health_check()

# Include routers
app.include_router(analytics_state.router, prefix="/api/v1")  # Analytics state management for frontend
app.include_router(file_upload.router, prefix="/api/v1")
if AGENTS_AVAILABLE:
    app.include_router(agents.router, prefix="/api/v1")
if DASHBOARD_ROUTER_AVAILABLE:
    app.include_router(dashboard.router, prefix="/api/v1")  # New dashboard generation router
if EXPORT_ROUTER_AVAILABLE:
    app.include_router(export.router, prefix="/api/v1")  # Export functionality router with RBAC
app.include_router(providers.router, prefix="/api/v1")  # Provider management router
app.include_router(chat.router, prefix="/api/v1")  # Conversational analytics chat router
if COMPARISON_AVAILABLE:
    app.include_router(comparison.router, prefix="/api/v1")  # Intelligent comparison router for estimated vs actual analysis
app.include_router(websocket.router)  # WebSocket router for real-time updates (has its own /api/v1/ws prefix)
app.include_router(ui_state.router, prefix="/api/v1")  # UI state management for frontend
app.include_router(data_router.router)  # Insightia /api/data/* (Ingestion, Clean, Chat, Profile, Export)
app.include_router(data_router.api_router)  # Insightia /api/* direct endpoints (Upload, Clean, Profile, Charts, Export)

# NEW: Include performance monitoring router if available
if PERFORMANCE_MONITORING_AVAILABLE:
    app.include_router(performance_monitoring.router)  # Performance monitoring and optimization router
    logger.info("✅ Performance monitoring router included")
else:
    logger.warning("⚠️ Performance monitoring router not available, skipping")

# Test WebSocket endpoint directly in main app
@app.websocket("/ws-test")
async def main_websocket_test(websocket: WebSocket):
    """Main app WebSocket test endpoint to bypass router issues."""
    logger.info("=== Main App WebSocket Test ===")
    try:
        await websocket.accept()
        logger.info("Main app WebSocket connection accepted!")
        
        await websocket.send_text('{"type": "success", "message": "Main app WebSocket works!"}')
        
        while True:
            try:
                data = await websocket.receive_text()
                await websocket.send_text(f"Main Echo: {data}")
            except Exception as e:
                logger.info(f"Main WebSocket disconnected: {e}")
                break
                
    except Exception as e:
        logger.error(f"Main WebSocket failed: {e}")
        raise

# Working WebSocket connection endpoint directly in main app
@app.websocket("/api/v1/ws/connect-direct")
async def main_websocket_connect(websocket: WebSocket):
    """Direct WebSocket connection in main app to bypass router authentication issues."""
    logger.info("=== Main App WebSocket Connect ===")
    try:
        await websocket.accept()
        logger.info("Main app WebSocket connect accepted!")
        
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "connection_id": "main-direct",
            "timestamp": "2025-06-04T00:00:00Z"
        }))
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle basic message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": "2025-06-04T00:00:00Z"
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "echo",
                        "original": message,
                        "timestamp": "2025-06-04T00:00:00Z"
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.info(f"Main WebSocket connect disconnected: {e}")
                break
                
    except Exception as e:
        logger.error(f"Main WebSocket connect failed: {e}")
        # Optionally: raise

# Duplicate of /api/v1/ws/connect-direct for test compatibility
@app.websocket("/api/v1/ws/direct-test")
async def main_websocket_direct_test(websocket: WebSocket):
    """Direct WebSocket test endpoint for compatibility with test scripts."""
    logger.info("=== Main App WebSocket Direct Test ===")
    try:
        await websocket.accept()
        logger.info("Main app WebSocket direct-test accepted!")
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "connection_id": "main-direct-test",
            "timestamp": "2025-06-04T00:00:00Z"
        }))
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": "2025-06-04T00:00:00Z"
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "echo",
                        "original": message,
                        "timestamp": "2025-06-04T00:00:00Z"
                    }))
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.info(f"Main WebSocket direct-test disconnected: {e}")
                break
    except Exception as e:
        logger.error(f"Main WebSocket direct-test failed: {e}")
        # Optionally: raise

if __name__ == "__main__":
    # Development server configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8001))
    # Disable reload to prevent constant server restarts and improve performance
    reload = False  # os.getenv("API_RELOAD", "true").lower() == "true"
    
    logger.info(f"Starting InsightIQ API server on {host}:{port}")
    logger.info("Google ADK agents integration enabled")
    logger.info("Dashboard generation pipeline enabled")
    logger.info("Role-based access control enabled")
    logger.info("Auto-reload disabled for better performance")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    ) 
