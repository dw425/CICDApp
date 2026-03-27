"""Abstract base class for external API connectors.
Implementation: Phase 5
"""
from abc import ABC, abstractmethod
import pandas as pd


class BaseConnector(ABC):
    """Base class for all API connectors."""

    def __init__(self, config: dict):
        self.config = config
        self._authenticated = False

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the external API."""
        pass

    @abstractmethod
    def fetch_records(self, **kwargs) -> list[dict]:
        """Fetch records from the external API."""
        pass

    @abstractmethod
    def normalize(self, records: list[dict]) -> pd.DataFrame:
        """Normalize fetched records to canonical schema."""
        pass

    def run(self, **kwargs) -> pd.DataFrame:
        """Authenticate, fetch, and normalize in one step."""
        self.authenticate()
        records = self.fetch_records(**kwargs)
        return self.normalize(records)
