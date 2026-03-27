"""
Central configuration module for the CI/CD Maturity Intelligence App.

Loads settings from environment variables with sensible defaults for local
development.  Import this module wherever you need configuration values:

    from config.settings import CATALOG, SCHEMA, USE_MOCK, get_full_table_name
"""

import os
from dotenv import load_dotenv

# Load .env file if present (no-op in Databricks Apps runtime)
load_dotenv()

# ---------------------------------------------------------------------------
# Data catalog / schema
# ---------------------------------------------------------------------------
CATALOG: str = os.getenv("CICD_APP_CATALOG", "lho_analytics")
SCHEMA: str = os.getenv("CICD_APP_SCHEMA", "cicd")

# ---------------------------------------------------------------------------
# Mock-data toggle (default True for local development)
# ---------------------------------------------------------------------------
_use_mock_raw = os.getenv("CICD_APP_USE_MOCK", "true")
USE_MOCK: bool = _use_mock_raw.strip().lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------------
# Databricks SQL connection (only required when USE_MOCK is False)
# ---------------------------------------------------------------------------
DATABRICKS_SERVER_HOSTNAME: str | None = os.getenv("DATABRICKS_SERVER_HOSTNAME")
DATABRICKS_HTTP_PATH: str | None = os.getenv("DATABRICKS_HTTP_PATH")
DATABRICKS_TOKEN: str | None = os.getenv("DATABRICKS_TOKEN")

# ---------------------------------------------------------------------------
# Application server
# ---------------------------------------------------------------------------
APP_PORT: int = int(os.getenv("APP_PORT", "8050"))
APP_DEBUG: bool = USE_MOCK if os.getenv("APP_DEBUG") is None else os.getenv("APP_DEBUG", "").strip().lower() in ("true", "1", "yes")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_full_table_name(table: str) -> str:
    """Return the fully-qualified three-level table name.

    Example::

        >>> get_full_table_name("deployment_events")
        'lho_analytics.cicd.deployment_events'
    """
    return f"{CATALOG}.{SCHEMA}.{table}"
