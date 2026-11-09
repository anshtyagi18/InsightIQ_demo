"""
Authentication service for user management and permission validation.
Provides authentication dependencies for FastAPI endpoints.
"""

import logging
from typing import Optional, Dict, Callable, List
from fastapi import HTTPException, Depends, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .models import User, UserRole, Permission, SAMPLE_USERS

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service for managing users and permissions."""
    
    def __init__(self):
        """Initialize authentication service with sample users."""
        self.users: Dict[str, User] = SAMPLE_USERS.copy()
        self.user_sessions: Dict[str, str] = {}  # Simple session storage
        
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        for user in self.users.values():
            if user.id == user_id:
                return user
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.users.get(username)
    
    def authenticate_user(self, username: str, password: str = None) -> Optional[User]:
        """Authenticate user (simplified for demo)."""
        # In production, this would validate against a database and hash
        user = self.get_user_by_username(username)
        if user and user.is_active:
            # For demo purposes, accept any password or no password
            return user
        return None
    
    def create_session(self, user: User) -> str:
        """Create a simple session for the user."""
        session_id = f"session_{user.id}_{len(self.user_sessions)}"
        self.user_sessions[session_id] = user.id
        return session_id
    
    def get_user_by_session(self, session_id: str) -> Optional[User]:
        """Get user from session ID."""
        user_id = self.user_sessions.get(session_id)
        if user_id:
            return self.get_user_by_id(user_id)
        return None
    
    def validate_permission(self, user: User, permission: Permission) -> bool:
        """Validate if user has specific permission."""
        return user.has_permission(permission)
    
    def validate_export_permission(self, user: User, format_type: str) -> bool:
        """Validate if user can export in specific format."""
        return user.can_export(format_type)

# Global auth service instance
auth_service = AuthService()

# FastAPI security scheme
security = HTTPBearer(auto_error=False)

async def get_current_user(
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_user_session: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None)
) -> User:
    """
    Get current user. Authentication is disabled; returns default admin user.
    """
    admin_user = auth_service.get_user_by_username("admin_user")
    if not admin_user:
        admin_user = User(
            id="admin_001",
            username="admin_user",
            email="admin@analytics.hub",
            role=UserRole.ADMIN,
            permissions={
                Permission.EXPORT_PDF,
                Permission.EXPORT_PNG,
                Permission.EXPORT_HTML,
                Permission.EXPORT_BULK,
                Permission.EXPORT_SHARE,
                Permission.DASHBOARD_VIEW,
                Permission.DASHBOARD_CREATE,
                Permission.DASHBOARD_EDIT,
                Permission.DASHBOARD_DELETE,
                Permission.DASHBOARD_SHARE,
                Permission.SYSTEM_ADMIN,
                Permission.USER_MANAGE
            }
        )
    return admin_user

def require_permission(permission: Permission) -> Callable:
    def check_permission(user: User = Depends(get_current_user)) -> User:
        return user
    return check_permission

def require_any_permission(permissions: List[Permission]) -> Callable:
    def check_permissions(user: User = Depends(get_current_user)) -> User:
        return user
    return check_permissions

def require_export_permission(format_type: str = None) -> Callable:
    def check_export_permission(user: User = Depends(get_current_user)) -> User:
        return user
    return check_export_permission

# Helper functions for testing authentication
def authenticate_as_admin() -> User:
    """Get admin user for testing."""
    return auth_service.get_user_by_username("admin_user")

def authenticate_as_editor() -> User:
    """Get editor user for testing."""
    return auth_service.get_user_by_username("editor_user")

def authenticate_as_viewer() -> User:
    """Get viewer user for testing."""
    return auth_service.get_user_by_username("viewer_user")

def authenticate_as_guest() -> User:
    """Get guest user for testing."""
    return auth_service.get_user_by_username("guest_user") 