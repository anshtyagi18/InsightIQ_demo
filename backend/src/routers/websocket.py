"""
WebSocket router for real-time updates in Analytics Hub API.
Handles real-time progress updates for file processing and dashboard generation.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, List, Set, Optional
import json
import asyncio
import logging
from datetime import datetime
import uuid

# Set up logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(
    prefix="/api/v1/ws",
    tags=["WebSocket"],
)

class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""
    
    def __init__(self):
        # Active connections: {connection_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Session subscriptions: {session_id: {connection_ids}}
        self.session_subscriptions: Dict[str, Set[str]] = {}
        # Progress tracking: {session_id: progress_data}
        self.progress_data: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str = None) -> str:
        """Accept a new WebSocket connection and assign a unique ID."""
        try:
            # Always accept the WebSocket connection first
            await websocket.accept()
            
            # Generate unique connection ID
            if connection_id is None:
                connection_id = str(uuid.uuid4())
            
            # Store the connection
            self.active_connections[connection_id] = websocket
            self.session_subscriptions[connection_id] = set()
            
            logger.info(f"WebSocket connected: {connection_id}")
            
            # Send a welcome message after connection is established
            try:
                await self.send_personal_message({
                    "type": "connected",
                    "connection_id": connection_id,
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
            except Exception as e:
                logger.error(f"Failed to send welcome message: {e}")
            
            return connection_id
        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection: {e}")
            raise
    
    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from session subscriptions
        for session_id, conn_ids in self.session_subscriptions.items():
            conn_ids.discard(connection_id)
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            # Don't re-raise to avoid breaking the connection flow
    
    async def subscribe_to_session(self, connection_id: str, session_id: str):
        """Subscribe a connection to updates for a specific session."""
        if session_id not in self.session_subscriptions:
            self.session_subscriptions[session_id] = set()
        
        self.session_subscriptions[session_id].add(connection_id)
        logger.info(f"Connection {connection_id} subscribed to session {session_id}")
        
        # Send current progress if available
        if session_id in self.progress_data:
            await self.send_to_connection(connection_id, {
                "type": "progress",
                "session_id": session_id,
                "data": self.progress_data[session_id]
            })
    
    async def unsubscribe_from_session(self, connection_id: str, session_id: str):
        """Unsubscribe a connection from a session."""
        if session_id in self.session_subscriptions:
            self.session_subscriptions[session_id].discard(connection_id)
        
        logger.info(f"Connection {connection_id} unsubscribed from session {session_id}")
    
    async def send_to_connection(self, connection_id: str, message: dict):
        """Send a message to a specific connection by ID."""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            await self.send_personal_message(message, websocket)
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        """Broadcast a message to all connections subscribed to a session."""
        if session_id not in self.session_subscriptions:
            return
        
        message_with_session = {
            **message,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send to all subscribed connections
        for connection_id in self.session_subscriptions[session_id].copy():
            try:
                await self.send_to_connection(connection_id, message_with_session)
            except Exception as e:
                logger.error(f"Failed to send to connection {connection_id}: {e}")
                # Remove failed connection
                self.disconnect(connection_id)
    
    async def update_progress(self, session_id: str, progress_data: dict):
        """Update and broadcast progress for a session."""
        # Store progress data
        self.progress_data[session_id] = progress_data
        
        # Broadcast to subscribed connections
        await self.broadcast_to_session(session_id, {
            "type": "progress",
            "data": progress_data
        })
    
    async def send_error(self, session_id: str, error_data: dict):
        """Send error message to session subscribers."""
        await self.broadcast_to_session(session_id, {
            "type": "error",
            "data": error_data
        })
    
    async def send_completion(self, session_id: str, result_data: dict):
        """Send completion message to session subscribers."""
        await self.broadcast_to_session(session_id, {
            "type": "completion",
            "data": result_data
        })
        
        # Clean up progress data
        if session_id in self.progress_data:
            del self.progress_data[session_id]
    
    def get_stats(self):
        """Get connection statistics."""
        return {
            "total_connections": len(self.active_connections),
            "active_sessions": len(self.session_subscriptions),
            "sessions_with_progress": len(self.progress_data)
        }

# Global connection manager instance
manager = ConnectionManager()

# Working WebSocket endpoint that bypasses any authentication issues
@router.websocket("/connect-working")
async def websocket_connect_working(websocket: WebSocket):
    """Working WebSocket connection endpoint that bypasses authentication issues."""
    logger.info("=== Router Working WebSocket Connect ===")
    logger.info(f"Router working WebSocket connection attempt from: {websocket.client}")
    
    try:
        await websocket.accept()
        logger.info("Router working WebSocket connection accepted!")
        
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "connection_id": "router-working",
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle basic message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "echo",
                        "original": message,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except WebSocketDisconnect:
                logger.info("Router working WebSocket disconnected normally")
                break
            except Exception as e:
                logger.info(f"Router working WebSocket disconnected: {e}")
                break
                
    except Exception as e:
        logger.error(f"Router working WebSocket connection failed: {e}")
        raise

@router.websocket("/direct-test")
async def websocket_direct_test(websocket: WebSocket):
    """Direct WebSocket test endpoint to bypass authentication issues."""
    logger.info("=== Direct WebSocket Test (Bypass Auth) ===")
    logger.info(f"Direct WebSocket connection attempt from: {websocket.client}")
    
    try:
        await websocket.accept()
        logger.info("Direct WebSocket connection accepted successfully!")
        
        # Send a welcome message
        await websocket.send_text(json.dumps({
            "type": "success",
            "message": "Direct WebSocket connection works!",
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Keep connection alive for testing
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Echo the message back
                await websocket.send_text(json.dumps({
                    "type": "echo",
                    "original": message,
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
            except WebSocketDisconnect:
                logger.info("Direct WebSocket disconnected")
                break
            except Exception as e:
                logger.error(f"Direct WebSocket error: {e}")
                break
                
    except Exception as e:
        logger.error(f"Direct WebSocket connection failed: {e}")
        raise

@router.websocket("/test")
async def websocket_test_endpoint(websocket: WebSocket):
    """Simple test WebSocket endpoint without any authentication dependencies."""
    logger.info("=== Test WebSocket Connection (No Auth) ===")
    logger.info(f"Test WebSocket connection attempt from: {websocket.client}")
    
    try:
        await websocket.accept()
        logger.info("Test WebSocket connection accepted successfully!")
        
        # Send a welcome message
        await websocket.send_text(json.dumps({
            "type": "welcome",
            "message": "Test WebSocket connection successful",
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Keep connection alive for testing
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Echo the message back
                await websocket.send_text(json.dumps({
                    "type": "echo",
                    "original": message,
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
            except WebSocketDisconnect:
                logger.info("Test WebSocket disconnected")
                break
            except Exception as e:
                logger.error(f"Test WebSocket error: {e}")
                break
                
    except Exception as e:
        logger.error(f"Test WebSocket connection failed: {e}")
        raise

@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    company_name: Optional[str] = Query(None)
):
    """Main WebSocket endpoint for establishing connections."""
    connection_id = None
    logger.info("=== WebSocket Connection Debug Start ===")
    logger.info(f"WebSocket connection attempt from: {websocket.client}")
    logger.info(f"Company name parameter: {company_name}")
    logger.info(f"WebSocket headers: {dict(websocket.headers)}")
    logger.info(f"WebSocket query params: {dict(websocket.query_params)}")
    logger.info(f"WebSocket scope path: {websocket.scope.get('path')}")
    logger.info(f"WebSocket scope method: {websocket.scope.get('method')}")
    
    try:
        # Connect and accept the WebSocket
        connection_id = await manager.connect(websocket)
        logger.info(f"WebSocket connection established successfully with ID: {connection_id}")
        logger.info("=== WebSocket Connection Debug End ===")
        
        # Main message loop
        while True:
            try:
                # Receive data from client
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    await handle_websocket_message(connection_id, message, websocket)
                except json.JSONDecodeError:
                    await manager.send_personal_message({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }, websocket)
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
                    await manager.send_personal_message({
                        "type": "error",
                        "message": "Internal server error"
                    }, websocket)
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected normally")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket message loop: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected during connection")
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        logger.info("=== WebSocket Connection Debug End ===")
        
    finally:
        # Always clean up the connection
        if connection_id:
            manager.disconnect(connection_id)
            logger.info(f"WebSocket disconnected: {connection_id}")

async def handle_websocket_message(connection_id: str, message: dict, websocket: WebSocket):
    """Handle incoming WebSocket messages from clients."""
    message_type = message.get("type")
    
    if message_type == "subscribe":
        session_id = message.get("session_id")
        if session_id:
            await manager.subscribe_to_session(connection_id, session_id)
            await manager.send_personal_message({
                "type": "subscribed",
                "session_id": session_id
            }, websocket)
        else:
            await manager.send_personal_message({
                "type": "error",
                "message": "session_id required for subscription"
            }, websocket)
    
    elif message_type == "unsubscribe":
        session_id = message.get("session_id")
        if session_id:
            await manager.unsubscribe_from_session(connection_id, session_id)
            await manager.send_personal_message({
                "type": "unsubscribed",
                "session_id": session_id
            }, websocket)
    
    elif message_type == "ping":
        # Respond to ping with pong immediately
        await manager.send_personal_message({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
    
    elif message_type == "get_status":
        session_id = message.get("session_id")
        if session_id and session_id in manager.progress_data:
            await manager.send_personal_message({
                "type": "progress",
                "session_id": session_id,
                "data": manager.progress_data[session_id]
            }, websocket)
        else:
            await manager.send_personal_message({
                "type": "no_progress",
                "session_id": session_id
            }, websocket)
    
    else:
        await manager.send_personal_message({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }, websocket)

@router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "status": "operational",
        "stats": manager.get_stats(),
        "timestamp": datetime.utcnow().isoformat()
    }

# Progress update functions for use by other services
async def update_file_processing_progress(session_id: str, stage: str, progress: int, message: str = None):
    """Update progress for file processing operations."""
    try:
        progress_data = {
            "stage": stage,
            "progress": progress,
            "message": message or f"{stage} - {progress}%",
            "type": "file_processing"
        }
        await manager.update_progress(session_id, progress_data)
    except Exception as e:
        # Log the error but don't fail the file upload process
        logger.warning(f"Failed to update progress for session {session_id}: {e}")

async def update_dashboard_generation_progress(session_id: str, stage: str, progress: int, message: str = None):
    """Update progress for dashboard generation operations."""
    try:
        progress_data = {
            "stage": stage,
            "progress": progress,
            "message": message or f"{stage} - {progress}%",
            "type": "dashboard_generation"
        }
        await manager.update_progress(session_id, progress_data)
    except Exception as e:
        # Log the error but don't fail the process
        logger.warning(f"Failed to update dashboard progress for session {session_id}: {e}")

async def send_processing_error(session_id: str, error_message: str, error_code: str = None):
    """Send error notification for processing operations."""
    try:
        error_data = {
            "message": error_message,
            "code": error_code,
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.send_error(session_id, error_data)
    except Exception as e:
        # Log the error but don't fail the process
        logger.warning(f"Failed to send error notification for session {session_id}: {e}")

async def send_processing_completion(session_id: str, result_data: dict):
    """Send completion notification for processing operations."""
    try:
        completion_data = {
            **result_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.send_completion(session_id, completion_data)
    except Exception as e:
        # Log the error but don't fail the process
        logger.warning(f"Failed to send completion notification for session {session_id}: {e}")

# Export the manager for use in other modules
__all__ = [
    "router", 
    "manager", 
    "update_file_processing_progress", 
    "update_dashboard_generation_progress",
    "send_processing_error",
    "send_processing_completion"
] 