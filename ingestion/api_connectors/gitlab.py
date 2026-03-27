"""GitLab API connector.
Implementation: Phase 5
"""
from ingestion.api_connectors.base_connector import BaseConnector
import pandas as pd


class GitLabConnector(BaseConnector):
    """Connector for GitLab REST API."""

    def authenticate(self) -> bool:
        raise NotImplementedError("GitLab connector not yet implemented")

    def fetch_records(self, **kwargs) -> list[dict]:
        raise NotImplementedError

    def normalize(self, records: list[dict]) -> pd.DataFrame:
        raise NotImplementedError
