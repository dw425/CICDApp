"""Source Manager — orchestrates connector → normalize → validate → write.

Coordinates the full data flow from a configured source to a target
Delta table in the lakehouse.  Each sync run:
1. Fetches data from the external API (GitHub, Jira, etc.)
2. Normalizes to the canonical slot schema
3. Validates required fields
4. Writes to the target Delta table (persists until next sync)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from config.data_source_slots import DATA_SOURCE_SLOTS
from config.settings import USE_MOCK, get_full_table_name
from data_layer.queries.data_source_config import get_config, update_config
from ingestion.api_connectors.registry import get_connector
from ingestion.transformers.normalize import normalize_to_canonical
from ingestion.transformers.validators import validate_schema

logger = logging.getLogger(__name__)


class SourceManager:
    """Orchestrate ingestion for a single data source config."""

    def __init__(self, config_id: str):
        self.config = get_config(config_id)
        if self.config is None:
            raise ValueError(f"Config not found: {config_id}")

    def sync(self) -> dict:
        """Run a full sync: fetch → normalize → validate → write.

        Returns:
            dict with keys: success, rows, errors, duration_seconds
        """
        start = datetime.utcnow()
        errors = []

        try:
            # 1. Fetch data from external source
            df = self._fetch()
            if df is None or df.empty:
                update_config(self.config["config_id"], {
                    "last_sync_at": datetime.utcnow().isoformat(),
                    "last_sync_status": "empty",
                    "last_sync_rows": 0,
                })
                return self._result(False, 0, ["No data returned from source"], start)

            # 2. Normalize to canonical schema
            df = self._normalize(df)

            # 3. Validate required fields
            target_table = self.config.get("target_table", "")
            is_valid, validation_errors = validate_schema(df, target_table)
            if not is_valid:
                errors.extend(validation_errors)
                update_config(self.config["config_id"], {
                    "last_sync_at": datetime.utcnow().isoformat(),
                    "last_sync_status": "validation_failed",
                })
                return self._result(False, 0, errors, start)

            # 4. Write to lakehouse Delta table
            rows_written = self._write(df, target_table)

            # 5. Update config with sync status
            update_config(self.config["config_id"], {
                "last_sync_at": datetime.utcnow().isoformat(),
                "last_sync_status": "success",
                "last_sync_rows": rows_written,
            })

            logger.info(
                "Sync complete: source=%s rows=%d duration=%.1fs",
                self.config.get("source_name"), rows_written,
                (datetime.utcnow() - start).total_seconds(),
            )
            return self._result(True, rows_written, errors, start)

        except Exception as e:
            logger.error("Sync failed: %s", e, exc_info=True)
            errors.append(str(e))
            try:
                update_config(self.config["config_id"], {
                    "last_sync_at": datetime.utcnow().isoformat(),
                    "last_sync_status": "failed",
                })
            except Exception:
                pass
            return self._result(False, 0, errors, start)

    def preview(self, limit: int = 25) -> pd.DataFrame:
        """Fetch and normalize a small preview without writing."""
        df = self._fetch(limit=limit)
        if df is None or df.empty:
            return pd.DataFrame()
        return self._normalize(df).head(limit)

    def test_connection(self) -> tuple[bool, str]:
        """Test the source connection. Returns (success, message)."""
        source_type = self.config.get("source_type", "")
        conn_config = self.config.get("connection_config", {})

        try:
            if source_type == "databricks_table":
                from ingestion.databricks_table_connector import DatabricksTableConnector
                table_path = conn_config.get("table_path", "")
                connector = DatabricksTableConnector(table_path)
                columns = connector.introspect()
                return True, f"Connected. Found {len(columns)} columns."

            elif source_type in ("github", "azure_devops", "gitlab",
                                 "jenkins", "jira", "databricks"):
                connector = get_connector(source_type, conn_config)
                success = connector.authenticate()
                if success:
                    data_types = connector.get_data_types()
                    return True, f"Connected. Available data types: {', '.join(data_types)}"
                return False, "Authentication failed."

            elif source_type == "csv_upload":
                return True, "CSV source — no connection needed."

            return False, f"Unknown source type: {source_type}"

        except Exception as e:
            return False, str(e)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fetch(self, limit: Optional[int] = None) -> Optional[pd.DataFrame]:
        """Fetch data from the configured source."""
        source_type = self.config.get("source_type", "")
        conn_config = self.config.get("connection_config", {})
        data_type = self.config.get("data_type", "")
        fetch_limit = limit or 10000

        if source_type == "databricks_table":
            from ingestion.databricks_table_connector import DatabricksTableConnector
            table_path = conn_config.get("table_path", "")
            field_mapping = self.config.get("field_mapping", {})
            where_clause = self.config.get("filters", {}).get("where_clause", "")
            connector = DatabricksTableConnector(table_path)
            return connector.preview(
                field_mapping=field_mapping,
                where_clause=where_clause,
                limit=fetch_limit,
            )

        elif source_type in ("github", "azure_devops", "gitlab",
                             "jenkins", "jira", "databricks"):
            connector = get_connector(source_type, conn_config)
            auth_ok = connector.authenticate()
            if not auth_ok:
                raise ConnectionError(
                    f"Authentication failed for {source_type}"
                )
            records = connector.fetch_records(
                data_type=data_type, limit=fetch_limit,
            )
            return pd.DataFrame(records) if records else pd.DataFrame()

        elif source_type == "csv_upload":
            csv_data = conn_config.get("csv_data", [])
            return pd.DataFrame(csv_data) if csv_data else pd.DataFrame()

        return None

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply field mapping and normalize to canonical schema."""
        field_mapping = self.config.get("field_mapping", {})
        slot_id = self.config.get("slot_id", "")
        source_type = self.config.get("source_type", "")

        # Apply field mapping (rename columns)
        if field_mapping:
            rename_map = {
                src: dst for src, dst in field_mapping.items()
                if dst and src in df.columns
            }
            df = df.rename(columns=rename_map)

        # Use normalize_to_canonical for external_quality_metrics targets
        slot = DATA_SOURCE_SLOTS.get(slot_id, {})
        event_type = slot.get("event_type")
        if event_type:
            df = normalize_to_canonical(df, source_type, event_type)

        return df

    def _write(self, df: pd.DataFrame, target_table: str) -> int:
        """Write normalized data to the target Delta table.

        Uses batch INSERT for efficiency.  Data persists in the lakehouse
        until the next sync run replaces it.
        """
        if USE_MOCK:
            # In mock mode, just count rows (no actual write)
            return len(df)

        from data_layer.connection import DataConnection
        conn = DataConnection()
        fq_table = get_full_table_name(target_table) if "." not in target_table else target_table

        # Batch INSERT — build VALUES list and insert in chunks of 500
        total_written = 0
        batch_size = 500
        columns = list(df.columns)
        col_list = ", ".join(columns)

        for start in range(0, len(df), batch_size):
            batch = df.iloc[start:start + batch_size]
            value_rows = []
            for _, row in batch.iterrows():
                vals = []
                for col in columns:
                    v = row[col]
                    if pd.isna(v) or v is None:
                        vals.append("NULL")
                    elif isinstance(v, bool):
                        vals.append(str(v).lower())
                    elif isinstance(v, (int, float)):
                        vals.append(str(v))
                    else:
                        vals.append(f"'{str(v).replace(chr(39), chr(39)+chr(39))}'")
                value_rows.append(f"({', '.join(vals)})")

            values_sql = ",\n".join(value_rows)
            conn.execute_query(
                f"INSERT INTO {fq_table} ({col_list}) VALUES {values_sql}"
            )
            total_written += len(batch)

        logger.info("Wrote %d rows to %s", total_written, fq_table)
        return total_written

    @staticmethod
    def _result(success, rows, errors, start) -> dict:
        duration = (datetime.utcnow() - start).total_seconds()
        return {
            "success": success,
            "rows": rows,
            "errors": errors,
            "duration_seconds": round(duration, 2),
        }
