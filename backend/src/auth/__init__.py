"""
Authentication and authorization module for Analytics Hub.
Provides role-based access control for export and dashboard functionality.
"""

from .models import User, UserRole, Permission, AuthToken, get_role_permissions, SAMPLE_USERS

try:
    from .service import AuthService, get_current_user, require_permission, require_export_permission
    from .service import authenticate_as_admin, authenticate_as_editor, authenticate_as_viewer, authenticate_as_guest
    from .service import auth_service
except ImportError as e:
    print(f"Warning: Could not import auth service components: {e}")
    # Create fallback implementations
    AuthService = None
    get_current_user = None
    require_permission = None
    require_export_permission = None
    authenticate_as_admin = None
    authenticate_as_editor = None
    authenticate_as_viewer = None
    authenticate_as_guest = None
    auth_service = None

__all__ = [
    "User",
    "UserRole", 
    "Permission",
    "AuthToken",
    "get_role_permissions",
    "SAMPLE_USERS",
    "AuthService",
    "get_current_user",
    "require_permission",
    "require_export_permission",
    "authenticate_as_admin",
    "authenticate_as_editor", 
    "authenticate_as_viewer",
    "authenticate_as_guest",
    "auth_service"
] 