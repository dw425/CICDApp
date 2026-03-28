"""Development auth backend — no authentication required."""


class DevAuthBackend:
    """Passthrough auth for local development."""

    def get_current_user(self):
        return {
            "email": "dev@local",
            "name": "Developer",
            "groups": ["admin"],
            "role": "admin",
        }

    def require_auth(self, func):
        """Decorator that passes through without auth check."""
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper

    def is_admin(self, user: dict) -> bool:
        return True
