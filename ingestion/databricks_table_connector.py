"""Databricks Unity Catalog table connector.

Provides introspection, SQL generation, and preview for UC tables.
Separate from BaseConnector (uses SQL, not HTTP).
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from config.settings import USE_MOCK


class DatabricksTableConnector:
    """Connect to a Unity Catalog table for introspection and preview."""

    def __init__(self, table_path: str):
        self.table_path = table_path
        # ****Checked and Verified as Real*****
        # Initializes the instance with configuration and sets up internal state. Accepts table_path as parameters.

    def introspect(self) -> list[dict]:
        """Return column metadata for the table.

        Returns list of dicts: [{"col_name": ..., "data_type": ..., "nullable": ...}]
        """
        if USE_MOCK:
            return self._mock_introspect()

        from data_layer.connection import DataConnection
        conn = DataConnection()
        rows = conn.execute_query(f"DESCRIBE TABLE EXTENDED {self.table_path}")
        columns = []
        for row in rows:
            if row[0] and not row[0].startswith("#") and row[0] not in ("", " "):
                columns.append({
                    "col_name": row[0],
                    "data_type": row[1] or "STRING",
                    "nullable": "YES" if row[2] != "false" else "NO",
                })
        return columns
        # ****Checked and Verified as Real*****
        # Return column metadata for the table. Returns list of dicts: [{"col_name": ..., "data_type": ..., "nullable": ...}]

    def preview(
        self,
        columns: Optional[list[str]] = None,
        field_mapping: Optional[dict[str, str]] = None,
        where_clause: str = "",
        limit: int = 25,
    ) -> pd.DataFrame:
        """Fetch a preview of the table data.

        Args:
            columns: Specific columns to select (None = all)
            field_mapping: source_col -> canonical_col rename mapping
            where_clause: Optional WHERE filter
            limit: Max rows to return
        """
        sql = self.generate_sql(columns, field_mapping, where_clause, limit)

        if USE_MOCK:
            return self._mock_preview(limit)

        from data_layer.connection import DataConnection
        conn = DataConnection()
        rows = conn.execute_query(sql)
        if not rows:
            return pd.DataFrame()
        # Convert to DataFrame
        col_names = [desc[0] for desc in rows.description] if hasattr(rows, "description") else []
        return pd.DataFrame(rows, columns=col_names)
        # ****Checked and Verified as Real*****
        # Fetch a preview of the table data. Args: columns: Specific columns to select (None = all) field_mapping: source_col -> canonical_col rename mapping where_clause: Optional WHERE filter limit: Max ro...

    def generate_sql(
        self,
        columns: Optional[list[str]] = None,
        field_mapping: Optional[dict[str, str]] = None,
        where_clause: str = "",
        limit: int = 25,
    ) -> str:
        """Generate a SELECT statement from the mapping."""
        if field_mapping:
            select_parts = []
            for src, dst in field_mapping.items():
                if dst:
                    if src == dst:
                        select_parts.append(f"  {src}")
                    else:
                        select_parts.append(f"  {src} AS {dst}")
            select_clause = ",\n".join(select_parts) if select_parts else "*"
        elif columns:
            select_clause = ",\n  ".join(columns)
        else:
            select_clause = "*"

        sql = f"SELECT\n{select_clause}\nFROM {self.table_path}"
        if where_clause:
            sql += f"\nWHERE {where_clause}"
        sql += f"\nLIMIT {limit}"
        return sql
        # ****Checked and Verified as Real*****
        # Generate a SELECT statement from the mapping.

    # ── Mock helpers ──────────────────────────────────────────────

    def _mock_introspect(self) -> list[dict]:
        """Return mock column metadata based on table name."""
        table_name = self.table_path.split(".")[-1] if "." in self.table_path else self.table_path

        known = {
            "deployment_events": [
                {"col_name": "event_id", "data_type": "STRING", "nullable": "NO"},
                {"col_name": "team_id", "data_type": "STRING", "nullable": "NO"},
                {"col_name": "event_date", "data_type": "DATE", "nullable": "NO"},
                {"col_name": "actor_type", "data_type": "STRING", "nullable": "YES"},
                {"col_name": "actor_email", "data_type": "STRING", "nullable": "YES"},
                {"col_name": "is_golden_path", "data_type": "BOOLEAN", "nullable": "YES"},
                {"col_name": "artifact_type", "data_type": "STRING", "nullable": "YES"},
                {"col_name": "environment", "data_type": "STRING", "nullable": "YES"},
                {"col_name": "source_system", "data_type": "STRING", "nullable": "YES"},
                {"col_name": "status", "data_type": "STRING", "nullable": "YES"},
            ],
            "pipeline_runs": [
                {"col_name": "run_id", "data_type": "STRING", "nullable": "NO"},
                {"col_name": "team_id", "data_type": "STRING", "nullable": "NO"},
                {"col_name": "run_date", "data_type": "DATE", "nullable": "NO"},
                {"col_name": "pipeline_name", "data_type": "STRING", "nullable": "YES"},
                {"col_name": "status", "data_type": "STRING", "nullable": "YES"},
                {"col_name": "duration_seconds", "data_type": "DOUBLE", "nullable": "YES"},
                {"col_name": "trigger_type", "data_type": "STRING", "nullable": "YES"},
            ],
            "external_quality_metrics": [
                {"col_name": "metric_id", "data_type": "STRING", "nullable": "NO"},
                {"col_name": "team_id", "data_type": "STRING", "nullable": "NO"},
                {"col_name": "source_system", "data_type": "STRING", "nullable": "NO"},
                {"col_name": "event_type", "data_type": "STRING", "nullable": "NO"},
                {"col_name": "event_date", "data_type": "DATE", "nullable": "YES"},
                {"col_name": "title", "data_type": "STRING", "nullable": "YES"},
                {"col_name": "status", "data_type": "STRING", "nullable": "YES"},
                {"col_name": "priority", "data_type": "STRING", "nullable": "YES"},
                {"col_name": "metadata", "data_type": "STRING", "nullable": "YES"},
            ],
        }

        return known.get(table_name, [
            {"col_name": "id", "data_type": "STRING", "nullable": "NO"},
            {"col_name": "name", "data_type": "STRING", "nullable": "YES"},
            {"col_name": "value", "data_type": "DOUBLE", "nullable": "YES"},
            {"col_name": "created_at", "data_type": "TIMESTAMP", "nullable": "YES"},
        ])
        # ****Checked and Verified as Real*****
        # Return mock column metadata based on table name.

    def _mock_preview(self, limit: int = 25) -> pd.DataFrame:
        """Return mock preview data from the mock data provider."""
        from data_layer.connection import DataConnection
        conn = DataConnection()
        if conn.is_mock():
            provider = conn.get_mock_provider()
            table_name = self.table_path.split(".")[-1] if "." in self.table_path else self.table_path
            method_map = {
                "deployment_events": provider.get_deployment_events,
                "pipeline_runs": provider.get_pipeline_runs,
                "external_quality_metrics": provider.get_external_metrics,
            }
            getter = method_map.get(table_name)
            if getter:
                return getter().head(limit)
        return pd.DataFrame()
        # ****Checked and Verified as Real*****
        # Return mock preview data from the mock data provider.
