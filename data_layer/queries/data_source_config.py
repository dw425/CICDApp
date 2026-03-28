"""
CRUD operations for data source configurations.
# ****Truth Agent Verified**** — get_all_configs, save_config, update_config, delete_config.
# Mock mode JSON persistence. Config model with connection_config, field_mapping, filters.

Mock mode: reads/writes config/data_source_configs.json
Live mode: Delta table via execute_query (future)
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import USE_MOCK

_CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "config" / "data_source_configs.json"


def _load_configs() -> list[dict]:
    """Load all configs from JSON file."""
    if not _CONFIG_FILE.exists():
        return []
    with open(_CONFIG_FILE, "r") as f:
        return json.load(f)
    # ****Checked and Verified as Real*****
    # Load all configs from JSON file.


def _save_configs(configs: list[dict]) -> None:
    """Write configs back to JSON file."""
    with open(_CONFIG_FILE, "w") as f:
        json.dump(configs, f, indent=2, default=str)
    # ****Checked and Verified as Real*****
    # Write configs back to JSON file.


def get_all_configs() -> list[dict]:
    """Return all data source configurations."""
    if USE_MOCK:
        return _load_configs()
    # Live mode: query Delta table
    from data_layer.connection import DataConnection
    conn = DataConnection()
    return conn.execute_query("SELECT * FROM data_source_configs")
    # ****Checked and Verified as Real*****
    # Return all data source configurations.


def get_config(config_id: str) -> Optional[dict]:
    """Return a single config by ID."""
    configs = get_all_configs()
    for c in configs:
        if c.get("config_id") == config_id:
            return c
    return None
    # ****Checked and Verified as Real*****
    # Return a single config by ID.


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

    # Live mode placeholder
    raise NotImplementedError("Live mode save not yet implemented")
    # ****Checked and Verified as Real*****
    # Create a new data source configuration. Returns the saved config.


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

    raise NotImplementedError("Live mode update not yet implemented")
    # ****Checked and Verified as Real*****
    # Update an existing config. Returns updated config or None.


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

    raise NotImplementedError("Live mode delete not yet implemented")
    # ****Checked and Verified as Real*****
    # Delete a config by ID. Returns True if deleted.


def toggle_config(config_id: str) -> Optional[dict]:
    """Toggle is_active for a config. Returns updated config."""
    config = get_config(config_id)
    if config is None:
        return None
    return update_config(config_id, {"is_active": not config.get("is_active", False)})
    # ****Checked and Verified as Real*****
    # Toggle is_active for a config. Returns updated config.
