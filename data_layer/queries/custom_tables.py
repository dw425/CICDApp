"""
Query functions for custom CI/CD maturity tables.

Each function checks whether the application is running in mock mode:
- **Mock mode** -- delegates to :class:`MockDataProvider` methods.
- **Live mode** -- executes a SQL query against the Databricks SQL warehouse.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from config.settings import get_full_table_name
from data_layer.connection import get_connection


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------

def get_teams() -> pd.DataFrame:
    """Return all registered teams."""
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_teams()
    return conn.execute_query(
        f"SELECT * FROM {get_full_table_name('team_registry')}"
    )


# ---------------------------------------------------------------------------
# Deployment Events
# ---------------------------------------------------------------------------

def get_deployment_events(
    team_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """Return deployment events with optional filters."""
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_deployment_events(
            team_id=team_id, start_date=start_date, end_date=end_date,
        )

    clauses: list[str] = []
    params: dict = {}
    if team_id:
        clauses.append("team_id = %(team_id)s")
        params["team_id"] = team_id
    if start_date:
        clauses.append("event_date >= %(start_date)s")
        params["start_date"] = start_date
    if end_date:
        clauses.append("event_date <= %(end_date)s")
        params["end_date"] = end_date

    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    query = f"SELECT * FROM {get_full_table_name('deployment_events')}{where}"
    return conn.execute_query(query, params or None)


# ---------------------------------------------------------------------------
# Maturity Scores
# ---------------------------------------------------------------------------

def get_maturity_scores(
    team_id: Optional[str] = None,
    latest: bool = False,
) -> pd.DataFrame:
    """Return maturity scores, optionally only the latest per team."""
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
# Maturity Trends
# ---------------------------------------------------------------------------

def get_maturity_trends(
    team_id: Optional[str] = None,
    period_type: str = "weekly",
) -> pd.DataFrame:
    """Return maturity trend rollups for the given period type."""
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
# Coaching Alerts
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
# Pipeline Runs
# ---------------------------------------------------------------------------

def get_pipeline_runs(
    team_id: Optional[str] = None,
) -> pd.DataFrame:
    """Return pipeline run records."""
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_pipeline_runs(team_id=team_id)

    clauses: list[str] = []
    params: dict = {}
    if team_id:
        clauses.append("team_id = %(team_id)s")
        params["team_id"] = team_id
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    query = f"SELECT * FROM {get_full_table_name('pipeline_runs')}{where}"
    return conn.execute_query(query, params or None)


# ---------------------------------------------------------------------------
# Billing Usage
# ---------------------------------------------------------------------------

def get_billing_usage(
    team_id: Optional[str] = None,
) -> pd.DataFrame:
    """Return DBU / billing usage records."""
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_billing_usage(team_id=team_id)

    clauses: list[str] = []
    params: dict = {}
    if team_id:
        clauses.append("team_id = %(team_id)s")
        params["team_id"] = team_id
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    query = f"SELECT * FROM {get_full_table_name('billing_usage')}{where}"
    return conn.execute_query(query, params or None)


# ---------------------------------------------------------------------------
# External Quality Metrics
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
# Cluster Policies
# ---------------------------------------------------------------------------

def get_cluster_policies(
    team_id: Optional[str] = None,
) -> pd.DataFrame:
    """Return cluster policy compliance records."""
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_cluster_policies(team_id=team_id)

    clauses: list[str] = []
    params: dict = {}
    if team_id:
        clauses.append("team_id = %(team_id)s")
        params["team_id"] = team_id
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    query = f"SELECT * FROM {get_full_table_name('cluster_policies')}{where}"
    return conn.execute_query(query, params or None)


# ---------------------------------------------------------------------------
# DLT Expectations
# ---------------------------------------------------------------------------

def get_dlt_expectations(
    team_id: Optional[str] = None,
) -> pd.DataFrame:
    """Return DLT expectation results."""
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_dlt_expectations(team_id=team_id)

    clauses: list[str] = []
    params: dict = {}
    if team_id:
        clauses.append("team_id = %(team_id)s")
        params["team_id"] = team_id
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    query = f"SELECT * FROM {get_full_table_name('dlt_expectations')}{where}"
    return conn.execute_query(query, params or None)


# ---------------------------------------------------------------------------
# Table Constraints
# ---------------------------------------------------------------------------

def get_table_constraints(
    team_id: Optional[str] = None,
) -> pd.DataFrame:
    """Return table constraint metadata."""
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_table_constraints(team_id=team_id)

    clauses: list[str] = []
    params: dict = {}
    if team_id:
        clauses.append("team_id = %(team_id)s")
        params["team_id"] = team_id
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    query = f"SELECT * FROM {get_full_table_name('table_constraints')}{where}"
    return conn.execute_query(query, params or None)


# ---------------------------------------------------------------------------
# Service Principals
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
