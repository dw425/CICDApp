"""
Query functions for CI/CD maturity data.

In **mock mode**, delegates to the MockDataProvider (CSV-based).
In **live mode**, tries Databricks SQL first, falls back to precomputed
JSON files if the warehouse is unavailable.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from config.settings import get_full_table_name
from data_layer.connection import get_connection
from data_layer.queries import system_tables
from data_layer import precomputed

logger = logging.getLogger(__name__)


def _with_fallback(live_fn, precomputed_fn, *args, **kwargs) -> pd.DataFrame:
    """Try live SQL query, fall back to precomputed JSON on failure."""
    conn = get_connection()
    if conn.is_mock():
        return live_fn(*args, **kwargs)
    try:
        return live_fn(*args, **kwargs)
    except Exception:
        logger.info("SQL query failed, using precomputed data for %s", precomputed_fn.__name__)
        return precomputed_fn(**kwargs)


# ---------------------------------------------------------------------------
# Teams — the ONE table that requires customer configuration
# ---------------------------------------------------------------------------

def get_teams() -> pd.DataFrame:
    """Return all registered teams."""
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_teams()
    try:
        return conn.execute_query(
            f"SELECT * FROM {get_full_table_name('team_registry')}"
        )
    except Exception:
        return precomputed.get_teams()


# ---------------------------------------------------------------------------
# Deployment Events — backed by system.access.audit
# ---------------------------------------------------------------------------

def get_deployment_events(
    team_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """Return deployment events derived from system audit log."""
    try:
        df = system_tables.get_deployment_events(
            team_id=team_id, start_date=start_date, end_date=end_date,
        )
        if not df.empty:
            return df
    except Exception:
        pass
    return precomputed.get_deployment_events()


# ---------------------------------------------------------------------------
# Pipeline Runs — backed by system.lakeflow.*
# ---------------------------------------------------------------------------

def get_pipeline_runs(
    team_id: Optional[str] = None,
) -> pd.DataFrame:
    """Return pipeline run records from system job run timeline."""
    try:
        df = system_tables.get_pipeline_runs(team_id=team_id)
        if not df.empty:
            return df
    except Exception:
        pass
    return precomputed.get_pipeline_runs()


# ---------------------------------------------------------------------------
# Billing Usage — backed by system.billing.usage
# ---------------------------------------------------------------------------

def get_billing_usage(
    team_id: Optional[str] = None,
) -> pd.DataFrame:
    """Return DBU / billing usage from system billing tables."""
    return system_tables.get_billing_usage(team_id=team_id)


# ---------------------------------------------------------------------------
# Cluster Policies — backed by system.compute.clusters
# ---------------------------------------------------------------------------

def get_cluster_policies(
    team_id: Optional[str] = None,
) -> pd.DataFrame:
    """Return cluster policy compliance from system compute tables."""
    return system_tables.get_cluster_policies(team_id=team_id)


# ---------------------------------------------------------------------------
# Table Constraints — backed by system.information_schema
# ---------------------------------------------------------------------------

def get_table_constraints(
    team_id: Optional[str] = None,
) -> pd.DataFrame:
    """Return table constraint metadata from information schema."""
    return system_tables.get_table_constraints(team_id=team_id)


# ---------------------------------------------------------------------------
# DLT Expectations — backed by system.lakeflow.pipeline_events
# ---------------------------------------------------------------------------

def get_dlt_expectations(
    team_id: Optional[str] = None,
) -> pd.DataFrame:
    """Return DLT expectation results from pipeline events."""
    return system_tables.get_dlt_expectations(team_id=team_id)


# ---------------------------------------------------------------------------
# Maturity Scores — computed & persisted by the scoring engine
# ---------------------------------------------------------------------------

def get_maturity_scores(
    team_id: Optional[str] = None,
    latest: bool = False,
) -> pd.DataFrame:
    """Return maturity scores."""
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_maturity_scores(
            team_id=team_id, latest=latest,
        )
    try:
        if latest:
            subquery = (
                f"SELECT *, ROW_NUMBER() OVER "
                f"(PARTITION BY team_id ORDER BY score_date DESC) AS rn "
                f"FROM {get_full_table_name('maturity_scores')}"
            )
            clauses: list[str] = ["rn = 1"]
            params: dict = {}
            if team_id:
                clauses.append("team_id = %(team_id)s")
                params["team_id"] = team_id
            where = " WHERE " + " AND ".join(clauses)
            query = f"SELECT * FROM ({subquery}){where}"
        else:
            clauses = []
            params = {}
            if team_id:
                clauses.append("team_id = %(team_id)s")
                params["team_id"] = team_id
            where = " WHERE " + " AND ".join(clauses) if clauses else ""
            query = f"SELECT * FROM {get_full_table_name('maturity_scores')}{where}"
        return conn.execute_query(query, params or None)
    except Exception:
        return precomputed.get_maturity_scores(team_id=team_id, latest=latest)


# ---------------------------------------------------------------------------
# Maturity Trends — computed from scores
# ---------------------------------------------------------------------------

def get_maturity_trends(
    team_id: Optional[str] = None,
    period_type: str = "weekly",
) -> pd.DataFrame:
    """Return maturity trend rollups."""
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_maturity_trends(
            team_id=team_id, period_type=period_type,
        )
    try:
        clauses: list[str] = ["period_type = %(period_type)s"]
        params: dict = {"period_type": period_type}
        if team_id:
            clauses.append("team_id = %(team_id)s")
            params["team_id"] = team_id
        where = " WHERE " + " AND ".join(clauses)
        query = f"SELECT * FROM {get_full_table_name('maturity_trends')}{where}"
        return conn.execute_query(query, params)
    except Exception:
        return precomputed.get_maturity_trends(team_id=team_id, period_type=period_type)


# ---------------------------------------------------------------------------
# Coaching Alerts — generated by the scoring engine
# ---------------------------------------------------------------------------

def get_coaching_alerts(
    team_id: Optional[str] = None,
    acknowledged: Optional[bool] = None,
) -> pd.DataFrame:
    """Return coaching alerts."""
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_coaching_alerts(
            team_id=team_id, acknowledged=acknowledged,
        )
    try:
        clauses: list[str] = []
        params: dict = {}
        if team_id:
            clauses.append("team_id = %(team_id)s")
            params["team_id"] = team_id
        if acknowledged is not None:
            clauses.append("is_acknowledged = %(acknowledged)s")
            params["acknowledged"] = acknowledged
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        query = f"SELECT * FROM {get_full_table_name('coaching_alerts')}{where}"
        return conn.execute_query(query, params or None)
    except Exception:
        return precomputed.get_coaching_alerts()


# ---------------------------------------------------------------------------
# External Quality Metrics — from connected APIs (Jira, ADO, etc.)
# ---------------------------------------------------------------------------

def get_external_metrics(
    team_id: Optional[str] = None,
    source_system: Optional[str] = None,
) -> pd.DataFrame:
    """Return external quality metrics (Jira / Azure DevOps)."""
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_external_metrics(
            team_id=team_id, source_system=source_system,
        )
    try:
        clauses: list[str] = []
        params: dict = {}
        if team_id:
            clauses.append("team_id = %(team_id)s")
            params["team_id"] = team_id
        if source_system:
            clauses.append("source_system = %(source_system)s")
            params["source_system"] = source_system
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        query = (
            f"SELECT * FROM {get_full_table_name('external_quality_metrics')}{where}"
        )
        return conn.execute_query(query, params or None)
    except Exception:
        return precomputed.get_external_metrics()


# ---------------------------------------------------------------------------
# Service Principals — from workspace identity (optional)
# ---------------------------------------------------------------------------

def get_service_principals(
    team_id: Optional[str] = None,
) -> pd.DataFrame:
    """Return service principal records."""
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_service_principals(team_id=team_id)

    clauses: list[str] = []
    params: dict = {}
    if team_id:
        clauses.append("team_id = %(team_id)s")
        params["team_id"] = team_id
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    query = f"SELECT * FROM {get_full_table_name('service_principals')}{where}"
    return conn.execute_query(query, params or None)
