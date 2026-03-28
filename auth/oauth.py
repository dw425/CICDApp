"""OAuth2 authentication backend for standalone Docker deployment."""

import os
import logging
import hashlib
import hmac
import time
import json
import base64

logger = logging.getLogger(__name__)


class OAuthBackend:
    """OAuth2/JWT authentication for production deployments.

    Supports Auth0, Azure AD (Entra ID), and generic OIDC providers.
    Configure via environment variables:
        OAUTH_PROVIDER: auth0, azure, oidc
        OAUTH_CLIENT_ID: client ID
        OAUTH_CLIENT_SECRET: client secret
        OAUTH_DOMAIN: provider domain (e.g. myapp.auth0.com)
        OAUTH_AUDIENCE: API identifier
    """

    def __init__(self):
        self.provider = os.environ.get("OAUTH_PROVIDER", "auth0")
        self.client_id = os.environ.get("OAUTH_CLIENT_ID", "")
        self.client_secret = os.environ.get("OAUTH_CLIENT_SECRET", "")
        self.domain = os.environ.get("OAUTH_DOMAIN", "")
        self.audience = os.environ.get("OAUTH_AUDIENCE", "")
        self._jwks_cache = None
        self._jwks_expiry = 0

    def get_current_user(self, token: str = None) -> dict:
        """Decode and validate JWT token, return user info."""
        if not token:
            return {"email": "", "name": "Unauthenticated", "groups": [], "role": "none"}

        try:
            payload = self._decode_token(token)
            return {
                "email": payload.get("email", payload.get("sub", "")),
                "name": payload.get("name", payload.get("nickname", "")),
                "groups": payload.get("groups", payload.get("roles", [])),
                "role": self._resolve_role(payload),
            }
        except Exception as e:
            logger.warning("Token validation failed: %s", e)
            return {"email": "", "name": "Invalid Token", "groups": [], "role": "none"}

    def _decode_token(self, token: str) -> dict:
        """Decode JWT token. In production use PyJWT with JWKS validation."""
        try:
            import jwt
            from jwt import PyJWKClient

            jwks_url = f"https://{self.domain}/.well-known/jwks.json"
            jwks_client = PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=f"https://{self.domain}/",
            )
        except ImportError:
            # Fallback: decode without verification (dev only)
            parts = token.split(".")
            if len(parts) != 3:
                raise ValueError("Invalid JWT format")
            payload = parts[1] + "=" * (4 - len(parts[1]) % 4)
            return json.loads(base64.b64decode(payload))

    def _resolve_role(self, payload: dict) -> str:
        """Map token claims to app roles."""
        groups = payload.get("groups", payload.get("roles", []))
        if "admin" in groups or "pipeline-compass-admin" in groups:
            return "admin"
        elif "editor" in groups or "pipeline-compass-editor" in groups:
            return "editor"
        return "viewer"

    def require_auth(self, func):
        """Decorator requiring valid OAuth token."""
        def wrapper(*args, **kwargs):
            from flask import request
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                raise PermissionError("Bearer token required")
            token = auth_header[7:]
            user = self.get_current_user(token)
            if not user.get("email"):
                raise PermissionError("Invalid or expired token")
            return func(*args, user=user, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper

    def is_admin(self, user: dict) -> bool:
        return user.get("role") == "admin"

    def get_login_url(self, redirect_uri: str) -> str:
        """Generate OAuth2 authorization URL."""
        if self.provider == "auth0":
            return (
                f"https://{self.domain}/authorize"
                f"?response_type=code"
                f"&client_id={self.client_id}"
                f"&redirect_uri={redirect_uri}"
                f"&scope=openid profile email"
                f"&audience={self.audience}"
            )
        elif self.provider == "azure":
            tenant = os.environ.get("OAUTH_TENANT_ID", "common")
            return (
                f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
                f"?response_type=code"
                f"&client_id={self.client_id}"
                f"&redirect_uri={redirect_uri}"
                f"&scope=openid profile email"
            )
        return ""
