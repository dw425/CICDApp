"""
CRUD operations for data source configurations.

Mock mode: reads/writes config/data_source_configs.json
Live mode: reads/writes the data_source_configs Delta table
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import USE_MOCK, get_full_table_name

_CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "config" / "data_source_configs.json"


# ---------------------------------------------------------------------------
# JSON helpers (mock mode)
# ---------------------------------------------------------------------------

def _load_configs() -> list[dict]:
    """Load all configs from JSON file."""
    if not _CONFIG_FILE.exists():
        return []
    with open(_CONFIG_FILE, "r") as f:
        return json.load(f)


def _save_configs(configs: list[dict]) -> None:
    """Write configs back to JSON file."""
    with open(_CONFIG_FILE, "w") as f:
        json.dump(configs, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_all_configs() -> list[dict]:
    """Return all data source configurations."""
    if USE_MOCK:
        return _load_configs()

    from data_layer.connection import DataConnection
    conn = DataConnection()
    table = get_full_table_name("data_source_configs")
    try:
        df = conn.execute_query(f"SELECT * FROM {table}")
        configs = df.to_dict("records")
        # Parse JSON string columns back to dicts
        for c in configs:
            for col in ("connection_config", "field_mapping", "filters"):
                val = c.get(col)
                if isinstance(val, str):
                    try:
                        c[col] = json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        pass
        return configs
    except Exception:
        return []


def get_config(config_id: str) -> Optional[dict]:
    """Return a single config by ID."""
    configs = get_all_configs()
    for c in configs:
        if c.get("config_id") == config_id:
            return c
    return None


def save_config(config: dict) -> dict:
    """Create a new data source configuration. Returns the saved config."""
    now = datetime.utcnow().isoformat()
    config.setdefault("config_id", str(uuid.uuid4()))
    config.setdefault("is_active", False)
    config.setdefault("created_at", now)
    config.setdefault("updated_at", now)
    config.setdefault("last_sync_at", None)
    config.setdefault("last_sync_status", None)
    config.setdefault("last_sync_rows", 0)

    if USE_MOCK:
        configs = _load_configs()
        configs.append(config)
        _save_configs(configs)
        return config

    # Live mode: INSERT into Delta table
    from data_layer.connection import DataConnection
    conn = DataConnection()
    table = get_full_table_name("data_source_configs")

    conn_cfg = json.dumps(config.get("connection_config", {}))
    fm = json.dumps(config.get("field_mapping", {}))
    filters = json.dumps(config.get("filters", {}))

    conn.execute_query(f"""
        INSERT INTO {table}
        (config_id, source_name, source_type, slot_id, data_type,
         is_active, connection_config, field_mapping, filters,
         target_table, created_at, updated_at,
         last_sync_at, last_sync_status, last_sync_rows)
        VALUES (
            '{config["config_id"]}',
            '{_esc(config.get("source_name", ""))}',
            '{_esc(config.get("source_type", ""))}',
            '{_esc(config.get("slot_id", ""))}',
            '{_esc(config.get("data_type", ""))}',
            {config.get("is_active", False)},
            '{_esc(conn_cfg)}',
            '{_esc(fm)}',
            '{_esc(filters)}',
            '{_esc(config.get("target_table", ""))}',
            '{config["created_at"]}',
            '{config["updated_at"]}',
            {_sql_val(config.get("last_sync_at"))},
            {_sql_val(config.get("last_sync_status"))},
            {config.get("last_sync_rows", 0)}
        )
    """)
    return config


def update_config(config_id: str, updates: dict) -> Optional[dict]:
    """Update an existing config. Returns updated config or None."""
    updates["updated_at"] = datetime.utcnow().isoformat()

    if USE_MOCK:
        configs = _load_configs()
        for i, c in enumerate(configs):
            if c.get("config_id") == config_id:
                configs[i].update(updates)
                _save_configs(configs)
                return configs[i]
        return None

    # Live mode: UPDATE Delta table
    from data_layer.connection import DataConnection
    conn = DataConnection()
    table = get_full_table_name("data_source_configs")

    set_clauses = []
    for key, val in updates.items():
        if key == "config_id":
            continue
        if key in ("connection_config", "field_mapping", "filters"):
            val = json.dumps(val) if isinstance(val, dict) else val
            set_clauses.append(f"{key} = '{_esc(str(val))}'")
        elif isinstance(val, bool):
            set_clauses.append(f"{key} = {val}")
        elif isinstance(val, (int, float)):
            set_clauses.append(f"{key} = {val}")
        elif val is None:
            set_clauses.append(f"{key} = NULL")
        else:
            set_clauses.append(f"{key} = '{_esc(str(val))}'")

    if not set_clauses:
        return get_config(config_id)

    conn.execute_query(
        f"UPDATE {table} SET {', '.join(set_clauses)} "
        f"WHERE config_id = '{_esc(config_id)}'"
    )
    return get_config(config_id)


def delete_config(config_id: str) -> bool:
    """Delete a config by ID. Returns True if deleted."""
    if USE_MOCK:
        configs = _load_configs()
        original_len = len(configs)
        configs = [c for c in configs if c.get("config_id") != config_id]
        if len(configs) < original_len:
            _save_configs(configs)
            return True
        return False

    from data_layer.connection import DataConnection
    conn = DataConnection()
    table = get_full_table_name("data_source_configs")
    conn.execute_query(
        f"DELETE FROM {table} WHERE config_id = '{_esc(config_id)}'"
    )
    return True


def toggle_config(config_id: str) -> Optional[dict]:
    """Toggle is_active for a config. Returns updated config."""
    config = get_config(config_id)
    if config is None:
        return None
    return update_config(config_id, {"is_active": not config.get("is_active", False)})


# ---------------------------------------------------------------------------
# SQL helpers
# ---------------------------------------------------------------------------

def _esc(val: str) -> str:
    """Escape single quotes for SQL."""
    return val.replace("'", "''") if val else ""


def _sql_val(val) -> str:
    """Return a SQL literal for a value (NULL-safe)."""
    if val is None:
        return "NULL"
    return f"'{_esc(str(val))}'"
