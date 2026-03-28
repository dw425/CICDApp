"""Authentication layer — supports dev, Databricks workspace, and OAuth2 modes."""

import os
from auth.dev_auth import DevAuthBackend
from auth.databricks_auth import DatabricksAuthBackend
from auth.oauth import OAuthBackend


def get_auth_backend(mode: str = None):
    """Return the appropriate auth backend based on AUTH_MODE env var."""
    mode = mode or os.environ.get("AUTH_MODE", "dev")
    if mode == "databricks":
        return DatabricksAuthBackend()
    elif mode == "oauth":
        return OAuthBackend()
    else:
        return DevAuthBackend()
