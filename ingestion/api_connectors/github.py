"""GitHub API connector.
Implementation: Phase 5
"""
from ingestion.api_connectors.base_connector import BaseConnector
import pandas as pd


class GitHubConnector(BaseConnector):
    """Connector for GitHub REST/GraphQL API."""

    def authenticate(self) -> bool:
        raise NotImplementedError("GitHub connector not yet implemented")

    def fetch_records(self, **kwargs) -> list[dict]:
        raise NotImplementedError

    def normalize(self, records: list[dict]) -> pd.DataFrame:
        raise NotImplementedError
