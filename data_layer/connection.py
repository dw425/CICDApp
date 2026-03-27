"""
Database connection module with automatic mock-data routing.

Usage::

    from data_layer.connection import get_connection

    conn = get_connection()
    if conn.is_mock():
        df = conn.get_mock_provider().get_teams()
    else:
        df = conn.execute_query("SELECT * FROM lho_analytics.cicd.teams")
"""

from __future__ import annotations

import threading
from typing import Optional

import pandas as pd

from config.settings import (
    DATABRICKS_HTTP_PATH,
    DATABRICKS_SERVER_HOSTNAME,
    DATABRICKS_TOKEN,
    USE_MOCK,
)
from data_layer.mock.mock_provider import MockDataProvider


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
        self._use_mock = USE_MOCK
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
        """Establish a Databricks SQL connection using the configured
        credentials."""
        try:
            from databricks import sql as dbsql

            self._sql_connection = dbsql.connect(
                server_hostname=DATABRICKS_SERVER_HOSTNAME,
                http_path=DATABRICKS_HTTP_PATH,
                access_token=DATABRICKS_TOKEN,
            )
        except Exception as exc:
            raise RuntimeError(
                "Failed to connect to Databricks SQL. "
                "Ensure DATABRICKS_SERVER_HOSTNAME, DATABRICKS_HTTP_PATH, "
                "and DATABRICKS_TOKEN are set correctly."
            ) from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_mock(self) -> bool:
        """Return ``True`` when operating in mock / local-dev mode."""
        return self._use_mock

    def get_mock_provider(self) -> Optional[MockDataProvider]:
        """Return the :class:`MockDataProvider` instance, or ``None``
        when running against live Databricks."""
        return self._mock_provider

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

    def close(self) -> None:
        """Close the underlying SQL connection (no-op in mock mode)."""
        if self._sql_connection is not None:
            try:
                self._sql_connection.close()
            except Exception:
                pass


# ------------------------------------------------------------------
# Module-level convenience accessor
# ------------------------------------------------------------------

def get_connection() -> DataConnection:
    """Return the singleton :class:`DataConnection` instance."""
    return DataConnection()
