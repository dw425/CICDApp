"""
Database connection module with automatic mock-data routing.

Usage::

    from data_layer.connection import get_connection

    conn = get_connection()
    if conn.is_mock():
        df = conn.get_mock_provider().get_teams()
    else:
        df = conn.execute_query("SELECT * FROM demos.cicd.teams")
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Optional

import pandas as pd

import config.settings as _cfg
from data_layer.mock.mock_provider import MockDataProvider

logger = logging.getLogger(__name__)


class DataConnection:
    """Singleton database connection that delegates to either the mock
    provider or a live Databricks SQL connection."""

    _instance: Optional["DataConnection"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "DataConnection":
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._initialized = False
                cls._instance = instance
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._use_mock = _cfg.USE_MOCK
        self._mock_provider: Optional[MockDataProvider] = None
        self._sql_connection = None

        if self._use_mock:
            self._mock_provider = MockDataProvider()
        else:
            self._init_sql_connection()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _init_sql_connection(self) -> None:
        """Establish a Databricks SQL connection.

        Supports two modes:
        1. **Databricks Apps** (AUTH_MODE=databricks): Uses the SDK's built-in
           service-principal auth — no token needed.
        2. **External / local**: Uses explicit hostname + http_path + token.
        """
        try:
            from databricks import sql as dbsql

            auth_mode = os.getenv("AUTH_MODE", "dev")
            if auth_mode == "databricks" and not _cfg.DATABRICKS_TOKEN:
                # Running inside Databricks Apps — use SDK-based auth
                from databricks.sdk import WorkspaceClient

                w = WorkspaceClient()
                host = (_cfg.DATABRICKS_SERVER_HOSTNAME
                        or w.config.host.replace("https://", "").rstrip("/"))
                http_path = (_cfg.DATABRICKS_HTTP_PATH
                             or os.getenv("DATABRICKS_WAREHOUSE_HTTP_PATH"))
                if not http_path:
                    raise RuntimeError(
                        "DATABRICKS_HTTP_PATH or DATABRICKS_WAREHOUSE_HTTP_PATH "
                        "must be set when running in Databricks Apps mode."
                    )
                self._sql_connection = dbsql.connect(
                    server_hostname=host,
                    http_path=http_path,
                    credentials_provider=w.config.authenticate,
                )
            else:
                # External mode — explicit credentials
                self._sql_connection = dbsql.connect(
                    server_hostname=_cfg.DATABRICKS_SERVER_HOSTNAME,
                    http_path=_cfg.DATABRICKS_HTTP_PATH,
                    access_token=_cfg.DATABRICKS_TOKEN,
                )
        except Exception as exc:
            logger.error(
                "Failed to connect to Databricks SQL: %s. "
                "Queries will return empty results until connection is available.",
                exc,
            )
            self._sql_connection = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_mock(self) -> bool:
        """Return ``True`` when operating in mock / local-dev mode."""
        return self._use_mock
        # ****Checked and Verified as Real*****
        # Return ``True`` when operating in mock / local-dev mode.

    def get_mock_provider(self) -> Optional[MockDataProvider]:
        """Return the :class:`MockDataProvider` instance, or ``None``
        when running against live Databricks."""
        return self._mock_provider
        # ****Checked and Verified as Real*****
        # Return the :class:`MockDataProvider` instance, or ``None`` when running against live Databricks.

    def execute_query(self, query: str, params: Optional[dict] = None) -> pd.DataFrame:
        """Execute a SQL query against the Databricks SQL warehouse and
        return the result as a DataFrame.

        Raises :class:`NotImplementedError` in mock mode -- callers should
        use :meth:`get_mock_provider` for mock data access.
        """
        if self._use_mock:
            raise NotImplementedError(
                "execute_query is not available in mock mode. "
                "Use get_mock_provider() methods instead."
            )

        # Lazy retry: if initial connection failed, try again
        if self._sql_connection is None:
            logger.info("SQL connection not available, retrying...")
            self._init_sql_connection()

        if self._sql_connection is None:
            raise ConnectionError(
                "No SQL connection available. Check warehouse and auth configuration."
            )

        cursor = self._sql_connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return pd.DataFrame(rows, columns=columns)
        finally:
            cursor.close()
        # ****Checked and Verified as Real*****
        # Execute a SQL query against the Databricks SQL warehouse and return the result as a DataFrame. Raises :class:`NotImplementedError` in mock mode -- callers should use :meth:`get_mock_provider` for m...

    def close(self) -> None:
        """Close the underlying SQL connection (no-op in mock mode)."""
        if self._sql_connection is not None:
            try:
                self._sql_connection.close()
            except Exception:
                pass
        # ****Checked and Verified as Real*****
        # Close the underlying SQL connection (no-op in mock mode).

    @classmethod
    def reset(cls) -> None:
        """Destroy the singleton so the next get_connection() creates a fresh instance."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance.close()
                cls._instance = None


# ------------------------------------------------------------------
# Module-level convenience accessor
# ------------------------------------------------------------------

def get_connection() -> DataConnection:
    """Return the singleton :class:`DataConnection` instance."""
    return DataConnection()
    # ****Checked and Verified as Real*****
    # Return the singleton :class:`DataConnection` instance.
