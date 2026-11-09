"""
Authentication models for role-based access control.
Defines user roles, permissions, and authentication structures.
"""

from enum import Enum
from typing import List, Optional, Set
from datetime import datetime
from pydantic import BaseModel, Field

class UserRole(str, Enum):
    """User roles with hierarchical permissions."""
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    GUEST = "guest"

class Permission(str, Enum):
    """Specific permissions for various actions."""
    # Export permissions
    EXPORT_PDF = "export:pdf"
    EXPORT_PNG = "export:png"
    EXPORT_HTML = "export:html"
    EXPORT_BULK = "export:bulk"
    EXPORT_SHARE = "export:share"
    
    # Dashboard permissions
    DASHBOARD_VIEW = "dashboard:view"
    DASHBOARD_CREATE = "dashboard:create"
    DASHBOARD_EDIT = "dashboard:edit"
    DASHBOARD_DELETE = "dashboard:delete"
    DASHBOARD_SHARE = "dashboard:share"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    USER_MANAGE = "user:manage"

class User(BaseModel):
    """User model with authentication and authorization data."""
    id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="User email address")
    role: UserRole = Field(..., description="User role")
    permissions: Set[Permission] = Field(default_factory=set, description="Additional permissions")
    is_active: bool = Field(True, description="Whether user account is active")
    created_at: datetime = Field(default_factory=datetime.now, description="Account creation date")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        # Check explicit permissions first
        if permission in self.permissions:
            return True
        
        # Check role-based permissions
        role_permissions = get_role_permissions(self.role)
        return permission in role_permissions
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(self.has_permission(perm) for perm in permissions)
    
    def can_export(self, format_type: str = None) -> bool:
        """Check if user can perform export operations."""
        export_permissions = [
            Permission.EXPORT_PDF,
            Permission.EXPORT_PNG,
            Permission.EXPORT_HTML
        ]
        
        if format_type:
            format_permission_map = {
                "pdf": Permission.EXPORT_PDF,
                "png": Permission.EXPORT_PNG,
                "html": Permission.EXPORT_HTML
            }
            specific_permission = format_permission_map.get(format_type.lower())
            if specific_permission:
                return self.has_permission(specific_permission)
        
        return self.has_any_permission(export_permissions)

class AuthToken(BaseModel):
    """Authentication token model."""
    token: str = Field(..., description="JWT token string")
    user_id: str = Field(..., description="User ID associated with token")
    expires_at: datetime = Field(..., description="Token expiration time")
    scopes: List[str] = Field(default_factory=list, description="Token scopes")

def get_role_permissions(role: UserRole) -> Set[Permission]:
    """Get permissions for a specific role."""
    permissions_map = {
        UserRole.ADMIN: {
            # Full system access
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
            Permission.USER_MANAGE,
        },
        UserRole.EDITOR: {
            # Editor permissions
            Permission.EXPORT_PDF,
            Permission.EXPORT_PNG,
            Permission.EXPORT_HTML,
            Permission.EXPORT_SHARE,
            Permission.DASHBOARD_VIEW,
            Permission.DASHBOARD_CREATE,
            Permission.DASHBOARD_EDIT,
            Permission.DASHBOARD_SHARE,
        },
        UserRole.VIEWER: {
            # View and basic export permissions
            Permission.EXPORT_PDF,
            Permission.EXPORT_PNG,
            Permission.EXPORT_HTML,
            Permission.DASHBOARD_VIEW,
        },
        UserRole.GUEST: {
            # Very limited permissions
            Permission.DASHBOARD_VIEW,
            Permission.EXPORT_HTML,  # Only HTML export for guests
        }
    }
    
    return permissions_map.get(role, set())

# Sample users for testing/demo
SAMPLE_USERS = {
    "admin_user": User(
        id="admin_001",
        username="admin",
        email="admin@analytics-hub.com",
        role=UserRole.ADMIN,
        is_active=True
    ),
    "editor_user": User(
        id="editor_001",
        username="editor",
        email="editor@analytics-hub.com",
        role=UserRole.EDITOR,
        is_active=True
    ),
    "viewer_user": User(
        id="viewer_001", 
        username="viewer",
        email="viewer@analytics-hub.com",
        role=UserRole.VIEWER,
        is_active=True
    ),
    "guest_user": User(
        id="guest_001",
        username="guest",
        email="guest@analytics-hub.com",
        role=UserRole.GUEST,
        is_active=True
    )
} 