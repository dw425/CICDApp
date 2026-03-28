"""Sync State Tracker — Persists connector sync state for incremental fetches."""

import json
import os
from datetime import datetime
from pathlib import Path


STATE_FILE = os.environ.get("SYNC_STATE_FILE", "data/sync_state.json")


def _load_state() -> dict:
    """Load sync state from file."""
    path = Path(STATE_FILE)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def _save_state(state: dict):
    """Persist sync state to file."""
    path = Path(STATE_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2, default=str)


def get_last_sync(platform: str) -> dict | None:
    """Get last sync info for a platform.

    Returns: {"timestamp": str, "cursor": str, "records_fetched": int} or None
    """
    state = _load_state()
    return state.get(platform)


def update_sync_state(platform: str, cursor: str = "", records_fetched: int = 0,
                      status: str = "success", error: str = ""):
    """Record a sync completion for a platform."""
    state = _load_state()
    state[platform] = {
        "timestamp": datetime.utcnow().isoformat(),
        "cursor": cursor,
        "records_fetched": records_fetched,
        "status": status,
        "error": error,
    }
    _save_state(state)


def get_all_sync_states() -> dict:
    """Get sync state for all platforms."""
    return _load_state()


def clear_sync_state(platform: str):
    """Clear sync state for a platform (forces full re-sync)."""
    state = _load_state()
    state.pop(platform, None)
    _save_state(state)
