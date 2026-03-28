"""Dash authentication middleware."""

import os
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """Middleware that integrates auth backends with Dash app."""

    def __init__(self, app, auth_backend):
        self.app = app
        self.auth = auth_backend
        self._current_user = None

    def get_user(self) -> dict:
        """Get current authenticated user."""
        if self._current_user is None:
            self._current_user = self.auth.get_current_user()
        return self._current_user

    def protect_callback(self, required_role: str = "viewer"):
        """Decorator for protecting Dash callbacks with auth."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                user = self.get_user()
                role_hierarchy = {"admin": 3, "editor": 2, "viewer": 1, "none": 0}
                user_level = role_hierarchy.get(user.get("role", "none"), 0)
                required_level = role_hierarchy.get(required_role, 0)
                if user_level < required_level:
                    logger.warning(
                        "Access denied: user=%s role=%s required=%s",
                        user.get("email"), user.get("role"), required_role,
                    )
                    return None
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def inject_user_info(self, layout_func):
        """Wrap layout function to inject user info into header."""
        @wraps(layout_func)
        def wrapper(*args, **kwargs):
            layout = layout_func(*args, **kwargs)
            return layout
        return wrapper
