"""Jira REST API connector.
Implementation: Phase 5
"""
from ingestion.api_connectors.base_connector import BaseConnector
import pandas as pd


class JiraConnector(BaseConnector):
    """Connector for Jira REST API."""

    def authenticate(self) -> bool:
        raise NotImplementedError("Jira connector not yet implemented")

    def fetch_records(self, **kwargs) -> list[dict]:
        raise NotImplementedError

    def normalize(self, records: list[dict]) -> pd.DataFrame:
        raise NotImplementedError
