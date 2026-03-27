"""
Admin Configuration Store for Pipeline Compass.

Persists assessment-wide settings (scoring profile, industry, org size, etc.)
that apply to all new assessments. Stored as JSON in the compass/data directory.
"""

import json
import os
from typing import Optional

_STORE_DIR = os.path.join(os.path.dirname(__file__), "data")
_CONFIG_FILE = os.path.join(_STORE_DIR, "admin_config.json")

DEFAULTS = {
    "scoring_profile": "balanced",
    "industry": "tech",
    "org_size": "mid_market",
    "uses_databricks": False,
    "organization_name": "",
}


def _ensure_file():
    os.makedirs(_STORE_DIR, exist_ok=True)
    if not os.path.exists(_CONFIG_FILE):
        with open(_CONFIG_FILE, "w") as f:
            json.dump(DEFAULTS, f, indent=2)


def get_admin_config() -> dict:
    """Read the current admin configuration."""
    _ensure_file()
    try:
        with open(_CONFIG_FILE, "r") as f:
            data = json.load(f)
            # Merge with defaults so new keys are always present
            merged = {**DEFAULTS, **data}
            return merged
    except (json.JSONDecodeError, FileNotFoundError):
        return dict(DEFAULTS)


def save_admin_config(updates: dict) -> dict:
    """Update admin configuration with the given key-value pairs."""
    current = get_admin_config()
    current.update(updates)
    _ensure_file()
    with open(_CONFIG_FILE, "w") as f:
        json.dump(current, f, indent=2)
    return current
