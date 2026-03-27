"""
Stub query functions for Databricks system tables.

These will be implemented in Phase 3 when system-table access is available.
Each function currently returns an empty DataFrame with the expected column
schema so that downstream code can be developed against a stable interface.
"""

from __future__ import annotations

import pandas as pd


def get_audit_events() -> pd.DataFrame:
    """Query ``system.access.audit`` for workspace audit events.

    Phase 3: Will return login, permission, and API events for CI/CD
    governance scoring.
    """
    return pd.DataFrame(columns=[
        "event_id", "event_time", "event_type", "user_identity",
        "service_name", "action_name", "request_params", "response",
    ])


def get_job_runs() -> pd.DataFrame:
    """Query ``system.lakeflow.job_run_timeline`` for job execution history.

    Phase 3: Will return run-level metrics used for pipeline reliability
    scoring.
    """
    return pd.DataFrame(columns=[
        "run_id", "job_id", "workspace_id", "run_start_time",
        "run_end_time", "result_state", "trigger_type",
        "run_duration_seconds",
    ])


def get_jobs() -> pd.DataFrame:
    """Query ``system.lakeflow.jobs`` for job definitions.

    Phase 3: Will return job metadata including git source configuration
    for golden-path compliance checks.
    """
    return pd.DataFrame(columns=[
        "job_id", "workspace_id", "name", "creator_user_name",
        "run_as_user_name", "job_type", "schedule", "settings",
    ])


def get_query_history() -> pd.DataFrame:
    """Query ``system.query.history`` for SQL warehouse query history.

    Phase 3: Will return query patterns for cost-efficiency and governance
    analysis.
    """
    return pd.DataFrame(columns=[
        "query_id", "query_start_time", "query_end_time", "status",
        "user_name", "warehouse_id", "executed_as", "statement_type",
        "total_duration_ms",
    ])


def get_billing() -> pd.DataFrame:
    """Query ``system.billing.usage`` for DBU consumption.

    Phase 3: Will return billing records for cost-efficiency domain
    scoring.
    """
    return pd.DataFrame(columns=[
        "usage_date", "workspace_id", "sku_name", "usage_quantity",
        "usage_unit", "custom_tags",
    ])


def get_clusters() -> pd.DataFrame:
    """Query ``system.compute.clusters`` for cluster metadata.

    Phase 3: Will return cluster configurations for security-governance
    and cost-efficiency checks.
    """
    return pd.DataFrame(columns=[
        "cluster_id", "cluster_name", "cluster_source", "creator",
        "driver_node_type", "worker_node_type", "num_workers",
        "autoscale_min", "autoscale_max", "policy_id",
    ])


def get_table_info() -> pd.DataFrame:
    """Query ``system.information_schema.tables`` and columns for schema
    metadata.

    Phase 3: Will return table/column details for data-quality domain
    scoring (constraint coverage, etc.).
    """
    return pd.DataFrame(columns=[
        "table_catalog", "table_schema", "table_name", "table_type",
        "column_name", "data_type", "is_nullable",
    ])


def get_dlt_events() -> pd.DataFrame:
    """Query ``system.lakeflow.pipeline_events`` for DLT pipeline events.

    Phase 3: Will return expectation results and pipeline execution
    details for data-quality and reliability scoring.
    """
    return pd.DataFrame(columns=[
        "pipeline_id", "event_type", "timestamp", "level", "message",
        "details",
    ])
