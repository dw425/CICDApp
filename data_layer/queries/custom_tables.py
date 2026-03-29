"""
Query functions for CI/CD maturity data.

In **mock mode**, delegates to the MockDataProvider (CSV-based).
In **live mode**, queries Databricks system tables — no custom customer
tables required (except team_registry for team definitions).

The scoring engine and UI callbacks consume the same DataFrame interfaces
regardless of the backend.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from config.settings import get_full_table_name
from data_layer.connection import get_connection
from data_layer.queries import system_tables


# ---------------------------------------------------------------------------
# Teams — the ONE table that requires customer configuration
# ---------------------------------------------------------------------------

def get_teams() -> pd.DataFrame:
    """Return all registered teams.

    This is the only table that must be customer-managed.  It defines which
    teams exist and maps workspace artefacts to team ownership.
    """
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_teams()
    return conn.execute_query(
        f"SELECT * FROM {get_full_table_name('team_registry')}"
    )


# ---------------------------------------------------------------------------
# Deployment Events — backed by system.access.audit
# ---------------------------------------------------------------------------

def get_deployment_events(
    team_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """Return deployment events derived from system audit log."""
    return system_tables.get_deployment_events(
        team_id=team_id, start_date=start_date, end_date=end_date,
    )


# ---------------------------------------------------------------------------
# Pipeline Runs — backed by system.lakeflow.*
# ---------------------------------------------------------------------------

def get_pipeline_runs(
    team_id: Optional[str] = None,
) -> pd.DataFrame:
    """Return pipeline run records from system job run timeline."""
    return system_tables.get_pipeline_runs(team_id=team_id)


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
    """Return maturity scores.

    These are computed by the scoring engine and stored in the app's schema.
    Falls back to mock data in dev mode.
    """
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_maturity_scores(
            team_id=team_id, latest=latest,
        )

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

    clauses: list[str] = ["period_type = %(period_type)s"]
    params: dict = {"period_type": period_type}
    if team_id:
        clauses.append("team_id = %(team_id)s")
        params["team_id"] = team_id
    where = " WHERE " + " AND ".join(clauses)
    query = f"SELECT * FROM {get_full_table_name('maturity_trends')}{where}"
    return conn.execute_query(query, params)


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
