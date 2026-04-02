"""Precomputed data loader — reads JSON files exported from Databricks.

Eliminates the need for a running SQL warehouse at page-load time.
"""

import json
import os
from pathlib import Path

import pandas as pd

_DIR = Path(__file__).parent


def _load(filename: str) -> pd.DataFrame:
    """Load a precomputed JSON file as a DataFrame."""
    path = _DIR / filename
    if not path.exists():
        return pd.DataFrame()
    with open(path) as f:
        data = json.load(f)
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def get_teams(**kwargs) -> pd.DataFrame:
    return _load("team_registry.json")


def get_deployment_events(**kwargs) -> pd.DataFrame:
    return _load("deployment_events.json")


def get_pipeline_runs(**kwargs) -> pd.DataFrame:
    return _load("pipeline_runs.json")


def get_maturity_scores(team_id=None, latest=False) -> pd.DataFrame:
    df = _load("maturity_scores.json")
    if df.empty:
        return df
    if team_id:
        df = df[df["team_id"] == team_id]
    if latest and "score_date" in df.columns:
        df = df.sort_values("score_date", ascending=False)
        df = df.groupby("team_id").head(9)  # 9 domains per team
    return df


def get_maturity_trends(team_id=None, period_type="weekly") -> pd.DataFrame:
    df = _load("maturity_trends.json")
    if df.empty:
        return df
    if "period_type" in df.columns:
        df = df[df["period_type"] == period_type]
    if team_id:
        df = df[df["team_id"] == team_id]
    return df


def get_coaching_alerts(**kwargs) -> pd.DataFrame:
    return pd.DataFrame()  # No coaching alerts precomputed


def get_external_metrics(**kwargs) -> pd.DataFrame:
    return _load("external_quality_metrics.json")


def get_staged_dora() -> dict:
    """Load staged DORA metrics as a dict matching the DORA calculator output."""
    df = _load("staged_dora_metrics.json")
    if df.empty:
        return {}
    dora = {}
    total_deploys = 0
    period_days = 90
    for _, row in df.iterrows():
        name = row.get("metric_name", "")
        val = row.get("metric_value")
        try:
            val = round(float(val), 3) if val is not None and str(val) != "None" else None
        except (ValueError, TypeError):
            val = None
        dora[name] = {
            "value": val,
            "unit": row.get("unit", ""),
            "tier": row.get("tier", "Unknown"),
            "color": row.get("color", "#6B7280"),
        }
        if row.get("total_deploys"):
            try:
                total_deploys = int(row["total_deploys"])
            except (ValueError, TypeError):
                pass
        if row.get("period_days"):
            try:
                period_days = int(row["period_days"])
            except (ValueError, TypeError):
                pass
    dora["total_deploys"] = total_deploys
    dora["period_days"] = period_days
    return dora


def get_clusters(**kwargs) -> pd.DataFrame:
    return _load("clusters.json")


def get_jobs(**kwargs) -> pd.DataFrame:
    return _load("jobs.json")
