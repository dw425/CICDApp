"""Tests for Auth module."""

import os
import pytest


class TestDevAuth:
    def test_dev_backend_creation(self):
        from auth.dev_auth import DevAuthBackend
        backend = DevAuthBackend()
        assert backend is not None

    def test_dev_backend_always_authenticated(self):
        from auth.dev_auth import DevAuthBackend
        backend = DevAuthBackend()
        user = backend.get_current_user()
        assert user is not None
        assert "email" in user
        assert user["email"] == "dev@local"

    def test_dev_backend_is_admin(self):
        from auth.dev_auth import DevAuthBackend
        backend = DevAuthBackend()
        user = backend.get_current_user()
        assert backend.is_admin(user) is True

    def test_require_auth_passthrough(self):
        from auth.dev_auth import DevAuthBackend
        backend = DevAuthBackend()

        @backend.require_auth
        def my_func():
            return "ok"

        assert my_func() == "ok"


class TestAuthFactory:
    def test_get_dev_backend(self):
        from auth import get_auth_backend
        backend = get_auth_backend("dev")
        assert backend is not None
        user = backend.get_current_user()
        assert user["email"] == "dev@local"

    def test_default_is_dev(self):
        os.environ["AUTH_MODE"] = "dev"
        from auth import get_auth_backend
        backend = get_auth_backend()
        user = backend.get_current_user()
        assert user["email"] == "dev@local"

    def test_unknown_mode_falls_back_to_dev(self):
        from auth import get_auth_backend
        backend = get_auth_backend("nonexistent_mode_xyz")
        # Falls back to dev mode
        user = backend.get_current_user()
        assert user is not None
