"""Databricks workspace authentication backend."""

import os
import logging

logger = logging.getLogger(__name__)


class DatabricksAuthBackend:
    """Auth via Databricks workspace identity.

    In a Databricks App context, the user identity comes from the workspace
    session. The Databricks SDK's WorkspaceClient automatically picks up
    credentials from the environment.
    """

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from databricks.sdk import WorkspaceClient
                self._client = WorkspaceClient()
            except Exception as e:
                logger.error("Failed to initialize Databricks WorkspaceClient: %s", e)
                raise
        return self._client

    def get_current_user(self) -> dict:
        """Return current user from Databricks workspace context."""
        try:
            w = self._get_client()
            me = w.current_user.me()
            groups = [g.display for g in (me.groups or [])]
            return {
                "email": me.user_name,
                "name": me.display_name or me.user_name,
                "groups": groups,
                "role": "admin" if "admins" in groups else "user",
            }
        except Exception as e:
            logger.warning("Databricks auth failed, falling back to anonymous: %s", e)
            return {
                "email": "anonymous@databricks",
                "name": "Anonymous",
                "groups": [],
                "role": "viewer",
            }

    def require_auth(self, func):
        """Decorator that validates Databricks workspace auth."""
        def wrapper(*args, **kwargs):
            user = self.get_current_user()
            if not user.get("email"):
                raise PermissionError("Databricks workspace authentication required")
            return func(*args, user=user, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper

    def is_admin(self, user: dict) -> bool:
        return user.get("role") == "admin" or "admins" in user.get("groups", [])
