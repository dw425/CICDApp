"""
Query functions for Databricks system tables.

Replaces custom CI/CD tables with standard system table queries that work
on any Unity-Catalog-enabled workspace without requiring customer-specific
data.  Each function transforms system-table rows into the DataFrame schema
expected by the scoring engine.

Graceful degradation: if system tables are not accessible (permissions not
yet granted), functions return empty DataFrames with the correct schema so
the app continues running.  Data fills in once access is granted.

System tables used:
- system.access.audit             → deployment_events (golden path)
- system.lakeflow.job_run_timeline → pipeline_runs (reliability)
- system.lakeflow.jobs            → pipeline_runs (git-backed flag)
- system.billing.usage            → billing_usage (cost efficiency)
- system.compute.clusters         → cluster_policies (security)
- system.information_schema.table_constraints → table_constraints (data quality)
- system.lakeflow.pipeline_events → dlt_expectations (data quality)
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from data_layer.connection import get_connection
from data_layer import precomputed

logger = logging.getLogger(__name__)


def _safe_query(conn, query: str, fallback_columns: list[str]) -> pd.DataFrame:
    """Execute a query with graceful fallback on permission errors."""
    try:
        return conn.execute_query(query)
    except Exception as e:
        logger.warning("System table query failed (access may not be granted yet): %s", e)
        return pd.DataFrame(columns=fallback_columns)


# ---------------------------------------------------------------------------
# Deployment events from audit log  → Golden Path + Environment Promotion
# ---------------------------------------------------------------------------

def get_deployment_events(team_id: Optional[str] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> pd.DataFrame:
    """Derive deployment events from ``system.access.audit``.

    Returns DataFrame with columns:
        event_id, team_id, event_date, actor_type, actor_email,
        is_golden_path, artifact_type, environment, source_system, status
    """
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_deployment_events(
            team_id=team_id, start_date=start_date, end_date=end_date,
        )

    date_filter = ""
    if start_date:
        date_filter += f" AND DATE(event_time) >= '{start_date}'"
    if end_date:
        date_filter += f" AND DATE(event_time) <= '{end_date}'"

    query = f"""
    SELECT
        event_id,
        DATE(event_time) AS event_date,
        CASE
            WHEN user_identity.email LIKE '%@%.iam.databricks.com'
              OR user_identity.email LIKE '%@%.gcp.databricks.com'
              OR user_identity.email LIKE '%.azuredatabricks.net'
              OR COALESCE(user_identity.email, '') = ''
            THEN 'service_principal'
            ELSE 'human'
        END AS actor_type,
        COALESCE(user_identity.email, 'service-principal') AS actor_email,
        CASE
            WHEN user_identity.email LIKE '%@%.iam.databricks.com'
              OR user_identity.email LIKE '%@%.gcp.databricks.com'
              OR user_identity.email LIKE '%.azuredatabricks.net'
              OR COALESCE(user_identity.email, '') = ''
            THEN true
            ELSE false
        END AS is_golden_path,
        CASE
            WHEN service_name = 'jobs' THEN 'job'
            WHEN service_name = 'pipelines' THEN 'dlt_pipeline'
            WHEN service_name = 'notebooks' THEN 'notebook'
            WHEN service_name = 'repos' THEN 'repo'
            ELSE service_name
        END AS artifact_type,
        CASE
            WHEN LOWER(COALESCE(request_params.run_name, request_params.pipeline_name,
                       request_params.notebook_path, '')) LIKE '%prod%' THEN 'prod'
            WHEN LOWER(COALESCE(request_params.run_name, request_params.pipeline_name,
                       request_params.notebook_path, '')) LIKE '%staging%' THEN 'staging'
            ELSE 'dev'
        END AS environment,
        'databricks' AS source_system,
        CASE
            WHEN response.status_code BETWEEN 200 AND 299 THEN 'success'
            ELSE 'failed'
        END AS status
    FROM system.access.audit
    WHERE service_name IN ('jobs', 'pipelines', 'notebooks', 'repos')
      AND action_name IN (
          'runNow', 'submitRun', 'runs/submit',
          'create', 'update', 'start', 'stop',
          'runCommand', 'import'
      )
      AND DATE(event_time) >= DATE_SUB(CURRENT_DATE(), 90)
      {date_filter}
    ORDER BY event_time DESC
    """
    fallback_cols = [
        "event_id", "event_date", "actor_type", "actor_email",
        "is_golden_path", "artifact_type", "environment", "source_system", "status",
    ]
    df = _safe_query(conn, query, fallback_cols)
    if not df.empty:
        return df
    return precomputed.get_deployment_events()


# ---------------------------------------------------------------------------
# Pipeline runs from job timeline → Pipeline Reliability + Env Promotion
# ---------------------------------------------------------------------------

def get_pipeline_runs(team_id: Optional[str] = None) -> pd.DataFrame:
    """Derive pipeline runs from ``system.lakeflow.job_run_timeline``
    joined with ``system.lakeflow.jobs``.

    Returns DataFrame with columns:
        run_id, team_id, job_id, job_name, run_date, status,
        duration_seconds, is_git_backed
    """
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_pipeline_runs(team_id=team_id)

    query = """
    SELECT
        r.run_id,
        r.job_id,
        j.name AS job_name,
        DATE(r.period_start_time) AS run_date,
        CASE
            WHEN r.result_state = 'SUCCEEDED' THEN 'success'
            WHEN r.result_state IN ('FAILED', 'ERROR', 'TIMEDOUT', 'CANCELED', 'CANCELLED') THEN 'failed'
            ELSE 'unknown'
        END AS status,
        COALESCE(
            TIMESTAMPDIFF(SECOND, r.period_start_time, r.period_end_time),
            0
        ) AS duration_seconds,
        CASE
            WHEN j.settings LIKE '%git_source%'
              OR j.settings LIKE '%git_provider%'
            THEN true
            ELSE false
        END AS is_git_backed
    FROM system.lakeflow.job_run_timeline r
    LEFT JOIN system.lakeflow.jobs j
        ON r.job_id = j.job_id
        AND r.workspace_id = j.workspace_id
    WHERE r.period_start_time >= DATE_SUB(CURRENT_DATE(), 90)
      AND r.result_state IS NOT NULL
    ORDER BY r.period_start_time DESC
    """
    fallback_cols = [
        "run_id", "job_id", "job_name", "run_date",
        "status", "duration_seconds", "is_git_backed",
    ]
    df = _safe_query(conn, query, fallback_cols)
    if not df.empty:
        return df
    return precomputed.get_pipeline_runs()


# ---------------------------------------------------------------------------
# Billing usage → Cost Efficiency
# ---------------------------------------------------------------------------

def get_billing_usage(team_id: Optional[str] = None) -> pd.DataFrame:
    """Query ``system.billing.usage`` for DBU consumption.

    Returns DataFrame with columns:
        usage_date, workload_type, dbu_consumed
    """
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_billing_usage(team_id=team_id)

    query = """
    SELECT
        DATE(usage_date) AS usage_date,
        CASE
            WHEN UPPER(sku_name) LIKE '%ALL_PURPOSE%'
              OR UPPER(sku_name) LIKE '%INTERACTIVE%' THEN 'INTERACTIVE'
            WHEN UPPER(sku_name) LIKE '%JOBS%'
              OR UPPER(sku_name) LIKE '%AUTOMATED%'
              OR UPPER(sku_name) LIKE '%WORKFLOW%' THEN 'JOBS'
            WHEN UPPER(sku_name) LIKE '%DLT%'
              OR UPPER(sku_name) LIKE '%DELTA_LIVE%'
              OR UPPER(sku_name) LIKE '%PIPELINES%' THEN 'DLT'
            WHEN UPPER(sku_name) LIKE '%SQL%'
              OR UPPER(sku_name) LIKE '%WAREHOUSE%' THEN 'SQL'
            ELSE 'OTHER'
        END AS workload_type,
        SUM(usage_quantity) AS dbu_consumed
    FROM system.billing.usage
    WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
    GROUP BY 1, 2
    ORDER BY 1 DESC
    """
    return _safe_query(conn, query, ["usage_date", "workload_type", "dbu_consumed"])


# ---------------------------------------------------------------------------
# Cluster policy compliance → Security & Governance
# ---------------------------------------------------------------------------

def get_cluster_policies(team_id: Optional[str] = None) -> pd.DataFrame:
    """Derive cluster policy compliance from ``system.compute.clusters``.

    Returns DataFrame with columns:
        cluster_id, cluster_name, policy_id, policy_name, is_compliant
    """
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_cluster_policies(team_id=team_id)

    query = """
    SELECT
        cluster_id,
        cluster_name,
        policy_id,
        COALESCE(policy_name, 'No Policy') AS policy_name,
        CASE
            WHEN policy_id IS NOT NULL THEN true
            ELSE false
        END AS is_compliant,
        change_time AS last_checked
    FROM system.compute.clusters
    WHERE owned_by IS NOT NULL
      AND delete_time IS NULL
    """
    return _safe_query(conn, query, [
        "cluster_id", "cluster_name", "policy_id", "policy_name", "is_compliant", "last_checked",
    ])


# ---------------------------------------------------------------------------
# Table constraints → Data Quality
# ---------------------------------------------------------------------------

def get_table_constraints(team_id: Optional[str] = None) -> pd.DataFrame:
    """Query ``system.information_schema.table_constraints`` for constraint
    metadata.

    Returns DataFrame with columns:
        table_name, constraint_type
    """
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_table_constraints(team_id=team_id)

    query = """
    SELECT
        constraint_name,
        table_name,
        table_schema,
        constraint_type
    FROM system.information_schema.table_constraints
    WHERE constraint_catalog = CURRENT_CATALOG()
    """
    return _safe_query(conn, query, ["constraint_name", "table_name", "table_schema", "constraint_type"])


# ---------------------------------------------------------------------------
# DLT expectation results → Data Quality
# ---------------------------------------------------------------------------

def get_dlt_expectations(team_id: Optional[str] = None) -> pd.DataFrame:
    """Derive DLT expectation pass/fail counts from
    ``system.lakeflow.pipeline_events``.

    Returns DataFrame with columns:
        pipeline_id, expectation_name, dataset, pass_count, fail_count
    """
    conn = get_connection()
    if conn.is_mock():
        return conn.get_mock_provider().get_dlt_expectations(team_id=team_id)

    query = """
    SELECT
        origin.pipeline_id AS pipeline_id,
        details :flow_definition.output_dataset AS dataset,
        details :flow_progress.data_quality.expectations[0].name AS expectation_name,
        COALESCE(
            CAST(details :flow_progress.data_quality.expectations[0].passed_records AS INT),
            0
        ) AS pass_count,
        COALESCE(
            CAST(details :flow_progress.data_quality.expectations[0].failed_records AS INT),
            0
        ) AS fail_count
    FROM system.lakeflow.pipeline_events
    WHERE event_type = 'flow_progress'
      AND details :flow_progress.data_quality IS NOT NULL
      AND timestamp >= DATE_SUB(CURRENT_DATE(), 90)
    """
    return _safe_query(conn, query, [
        "pipeline_id", "dataset", "expectation_name", "pass_count", "fail_count",
    ])


# ---------------------------------------------------------------------------
# Audit events (raw) — for governance / advanced analysis
# ---------------------------------------------------------------------------

def get_audit_events() -> pd.DataFrame:
    """Query ``system.access.audit`` for recent workspace events."""
    cols = ["event_id", "event_time", "event_type", "user_identity",
            "service_name", "action_name", "request_params", "response"]
    conn = get_connection()
    if conn.is_mock():
        return pd.DataFrame(columns=cols)
    query = """
    SELECT event_id, event_time, event_type,
           user_identity.email AS user_identity,
           service_name, action_name,
           request_params, response
    FROM system.access.audit
    WHERE event_time >= DATE_SUB(CURRENT_TIMESTAMP(), 7)
    ORDER BY event_time DESC
    LIMIT 10000
    """
    return _safe_query(conn, query, cols)


# ---------------------------------------------------------------------------
# Job runs (raw) — for DORA metrics / advanced analysis
# ---------------------------------------------------------------------------

def get_job_runs() -> pd.DataFrame:
    """Query ``system.lakeflow.job_run_timeline`` for recent runs."""
    cols = ["run_id", "job_id", "workspace_id", "run_start_time",
            "run_end_time", "result_state", "trigger_type", "run_duration_seconds"]
    conn = get_connection()
    if conn.is_mock():
        return pd.DataFrame(columns=cols)
    query = """
    SELECT run_id, job_id, workspace_id,
           period_start_time AS run_start_time,
           period_end_time AS run_end_time,
           result_state, trigger_type,
           TIMESTAMPDIFF(SECOND, period_start_time, period_end_time) AS run_duration_seconds
    FROM system.lakeflow.job_run_timeline
    WHERE period_start_time >= DATE_SUB(CURRENT_DATE(), 90)
      AND result_state IS NOT NULL
    ORDER BY period_start_time DESC
    """
    return _safe_query(conn, query, cols)


# ---------------------------------------------------------------------------
# Jobs metadata (raw) — for git-backed analysis
# ---------------------------------------------------------------------------

def get_jobs() -> pd.DataFrame:
    """Query ``system.lakeflow.jobs`` for job definitions."""
    cols = ["job_id", "workspace_id", "name", "creator_user_name",
            "run_as_user_name", "job_type", "schedule", "settings"]
    conn = get_connection()
    if conn.is_mock():
        return pd.DataFrame(columns=cols)
    try:
        query = """
        SELECT job_id, workspace_id, name, creator_user_name,
               run_as_user_name, job_type, schedule,
               CAST(settings AS STRING) AS settings
        FROM system.lakeflow.jobs
        WHERE delete_time IS NULL
        """
        df = _safe_query(conn, query, cols)
        if not df.empty:
            return df
    except Exception:
        pass
    return precomputed.get_jobs()


# ---------------------------------------------------------------------------
# Query history — for governance analysis
# ---------------------------------------------------------------------------

def get_query_history() -> pd.DataFrame:
    """Query ``system.query.history`` for SQL warehouse query patterns."""
    cols = ["query_id", "query_start_time", "query_end_time", "status",
            "user_name", "warehouse_id", "executed_as", "statement_type", "total_duration_ms"]
    conn = get_connection()
    if conn.is_mock():
        return pd.DataFrame(columns=cols)
    query = """
    SELECT query_id, query_start_time_ms AS query_start_time,
           query_end_time_ms AS query_end_time,
           status, executed_by AS user_name,
           warehouse_id, executed_as,
           statement_type, total_duration_ms
    FROM system.query.history
    WHERE query_start_time_ms >= DATE_SUB(CURRENT_TIMESTAMP(), 7)
    ORDER BY query_start_time_ms DESC
    LIMIT 5000
    """
    return _safe_query(conn, query, cols)


# ---------------------------------------------------------------------------
# Billing (raw) — for cost analysis
# ---------------------------------------------------------------------------

def get_billing() -> pd.DataFrame:
    """Query ``system.billing.usage`` for DBU consumption (raw)."""
    cols = ["usage_date", "workspace_id", "sku_name", "usage_quantity",
            "usage_unit", "custom_tags"]
    conn = get_connection()
    if conn.is_mock():
        return pd.DataFrame(columns=cols)
    query = """
    SELECT usage_date, workspace_id, sku_name,
           usage_quantity, usage_unit,
           CAST(custom_tags AS STRING) AS custom_tags
    FROM system.billing.usage
    WHERE usage_date >= DATE_SUB(CURRENT_DATE(), 90)
    ORDER BY usage_date DESC
    """
    return _safe_query(conn, query, cols)


# ---------------------------------------------------------------------------
# Clusters (raw) — for security / cost analysis
# ---------------------------------------------------------------------------

def get_clusters() -> pd.DataFrame:
    """Query ``system.compute.clusters`` for cluster metadata."""
    cols = ["cluster_id", "cluster_name", "cluster_source", "creator",
            "driver_node_type", "worker_node_type", "num_workers",
            "autoscale_min", "autoscale_max", "policy_id"]
    conn = get_connection()
    if conn.is_mock():
        return pd.DataFrame(columns=cols)
    try:
        query = """
        SELECT cluster_id, cluster_name, cluster_source,
               owned_by AS creator,
               driver_node_type_id AS driver_node_type,
               node_type_id AS worker_node_type,
               num_workers,
               autoscale_min_workers AS autoscale_min,
               autoscale_max_workers AS autoscale_max,
               policy_id
        FROM system.compute.clusters
        WHERE delete_time IS NULL
        """
        df = _safe_query(conn, query, cols)
        if not df.empty:
            return df
    except Exception:
        pass
    return precomputed.get_clusters()


# ---------------------------------------------------------------------------
# Table info (raw) — for data quality analysis
# ---------------------------------------------------------------------------

def get_table_info() -> pd.DataFrame:
    """Query ``system.information_schema`` for schema metadata."""
    cols = ["table_catalog", "table_schema", "table_name", "table_type",
            "column_name", "data_type", "is_nullable"]
    conn = get_connection()
    if conn.is_mock():
        return pd.DataFrame(columns=cols)
    query = """
    SELECT t.table_catalog, t.table_schema, t.table_name, t.table_type,
           c.column_name, c.data_type, c.is_nullable
    FROM system.information_schema.tables t
    LEFT JOIN system.information_schema.columns c
        ON t.table_catalog = c.table_catalog
       AND t.table_schema = c.table_schema
       AND t.table_name = c.table_name
    WHERE t.table_catalog = CURRENT_CATALOG()
      AND t.table_type = 'MANAGED'
    ORDER BY t.table_schema, t.table_name, c.ordinal_position
    """
    return _safe_query(conn, query, cols)


# ---------------------------------------------------------------------------
# DLT events (raw) — for pipeline analysis
# ---------------------------------------------------------------------------

def get_dlt_events() -> pd.DataFrame:
    """Query ``system.lakeflow.pipeline_events`` for DLT events."""
    cols = ["pipeline_id", "event_type", "timestamp", "level", "message", "details"]
    conn = get_connection()
    if conn.is_mock():
        return pd.DataFrame(columns=cols)
    query = """
    SELECT origin.pipeline_id AS pipeline_id,
           event_type, timestamp, level, message,
           CAST(details AS STRING) AS details
    FROM system.lakeflow.pipeline_events
    WHERE timestamp >= DATE_SUB(CURRENT_DATE(), 30)
    ORDER BY timestamp DESC
    LIMIT 10000
    """
    return _safe_query(conn, query, cols)
