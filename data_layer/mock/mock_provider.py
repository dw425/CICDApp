"""
Mock data provider that reads CSV files from the sample_data/ directory and
returns filtered pandas DataFrames.

Used when ``CICD_APP_USE_MOCK=true`` so the application can run locally
without a Databricks SQL connection.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

# Resolve the sample_data directory relative to this module
_SAMPLE_DATA_DIR = Path(__file__).resolve().parent / "sample_data"

# Date columns that should be parsed per CSV
_DATE_COLUMNS: dict[str, list[str]] = {
    "teams.csv": ["created_date"],
    "deployment_events.csv": ["event_date"],
    "maturity_scores.csv": ["score_date"],
    "maturity_trends.csv": ["period_start", "period_end"],
    "coaching_alerts.csv": ["created_date"],
    "external_quality_metrics.csv": ["event_date"],
    "pipeline_runs.csv": ["run_date"],
    "cluster_policies.csv": ["last_checked"],
    "dlt_expectations.csv": ["check_date"],
    "billing_usage.csv": ["usage_date"],
    "service_principals.csv": ["created_date"],
}


class MockDataProvider:
    """Reads CSV files from disk and returns DataFrames with optional filters."""

    def __init__(self) -> None:
        self._cache: dict[str, pd.DataFrame] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self, filename: str) -> pd.DataFrame:
        """Load a CSV file from sample_data/, caching the result."""
        if filename not in self._cache:
            path = _SAMPLE_DATA_DIR / filename
            parse_dates = _DATE_COLUMNS.get(filename, False) or False
            df = pd.read_csv(path, parse_dates=parse_dates)
            self._cache[filename] = df
        return self._cache[filename].copy()

    @staticmethod
    def _filter_team(df: pd.DataFrame, team_id: Optional[str]) -> pd.DataFrame:
        if team_id is not None:
            return df[df["team_id"] == team_id]
        return df

    @staticmethod
    def _filter_date_range(
        df: pd.DataFrame,
        col: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        if start_date is not None:
            df = df[df[col] >= pd.Timestamp(start_date)]
        if end_date is not None:
            df = df[df[col] <= pd.Timestamp(end_date)]
        return df

    # ------------------------------------------------------------------
    # Public query methods
    # ------------------------------------------------------------------

    def get_teams(self) -> pd.DataFrame:
        """Return all teams."""
        return self._load("teams.csv")

    def get_deployment_events(
        self,
        team_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return deployment events, optionally filtered by team and date range."""
        df = self._load("deployment_events.csv")
        df = self._filter_team(df, team_id)
        df = self._filter_date_range(df, "event_date", start_date, end_date)
        return df

    def get_maturity_scores(
        self,
        team_id: Optional[str] = None,
        latest: bool = False,
    ) -> pd.DataFrame:
        """Return maturity scores.

        If *latest* is ``True``, only the most recent ``score_date`` per team
        is returned.
        """
        df = self._load("maturity_scores.csv")
        df = self._filter_team(df, team_id)
        if latest:
            max_dates = df.groupby("team_id")["score_date"].transform("max")
            df = df[df["score_date"] == max_dates]
        return df

    def get_maturity_trends(
        self,
        team_id: Optional[str] = None,
        period_type: str = "weekly",
    ) -> pd.DataFrame:
        """Return maturity trend rollups filtered by period type."""
        df = self._load("maturity_trends.csv")
        df = self._filter_team(df, team_id)
        df = df[df["period_type"] == period_type]
        return df

    def get_coaching_alerts(
        self,
        team_id: Optional[str] = None,
        acknowledged: Optional[bool] = None,
    ) -> pd.DataFrame:
        """Return coaching alerts, optionally filtered by acknowledgement status."""
        df = self._load("coaching_alerts.csv")
        df = self._filter_team(df, team_id)
        if acknowledged is not None:
            df = df[df["is_acknowledged"] == acknowledged]
        return df

    def get_external_metrics(
        self,
        team_id: Optional[str] = None,
        source_system: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return external quality metrics (Jira / Azure DevOps)."""
        df = self._load("external_quality_metrics.csv")
        df = self._filter_team(df, team_id)
        if source_system is not None:
            df = df[df["source_system"] == source_system]
        return df

    def get_pipeline_runs(
        self,
        team_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return pipeline run records."""
        df = self._load("pipeline_runs.csv")
        return self._filter_team(df, team_id)

    def get_cluster_policies(
        self,
        team_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return cluster policy compliance records."""
        df = self._load("cluster_policies.csv")
        return self._filter_team(df, team_id)

    def get_dlt_expectations(
        self,
        team_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return DLT expectation results."""
        df = self._load("dlt_expectations.csv")
        return self._filter_team(df, team_id)

    def get_billing_usage(
        self,
        team_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return billing / DBU usage records."""
        df = self._load("billing_usage.csv")
        return self._filter_team(df, team_id)

    def get_table_constraints(
        self,
        team_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return table constraint metadata."""
        df = self._load("table_constraints.csv")
        return self._filter_team(df, team_id)

    def get_service_principals(
        self,
        team_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return service principal records."""
        df = self._load("service_principals.csv")
        return self._filter_team(df, team_id)
