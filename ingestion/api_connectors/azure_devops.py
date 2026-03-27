"""Azure DevOps REST API connector.
Implementation: Phase 5
"""
from ingestion.api_connectors.base_connector import BaseConnector
import pandas as pd


class AzureDevOpsConnector(BaseConnector):
    """Connector for Azure DevOps REST API."""

    def authenticate(self) -> bool:
        # TODO: Implement PAT-based authentication
        raise NotImplementedError("Azure DevOps connector not yet implemented")

    def fetch_records(self, **kwargs) -> list[dict]:
        raise NotImplementedError

    def normalize(self, records: list[dict]) -> pd.DataFrame:
        raise NotImplementedError
