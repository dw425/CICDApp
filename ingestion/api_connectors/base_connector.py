"""Abstract base class for external API connectors."""

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

    # ── Classmethods for wizard introspection ─────────────────────

    @classmethod
    def get_required_config_fields(cls) -> list[dict]:
        """Return credential/config field definitions for wizard Step 2.

        Each dict: {"key": str, "label": str, "placeholder": str, "type": "text"|"password"}
        """
        return []

    @classmethod
    def get_data_types(cls) -> list[dict]:
        """Return available data types with suggested slot mapping for Step 3.

        Each dict: {"value": str, "label": str, "suggested_slot": str}
        """
        return []

    def preview(self, data_type: str = "", limit: int = 25) -> pd.DataFrame:
        """Fetch a limited preview of normalized data for Step 5."""
        self.authenticate()
        records = self.fetch_records(data_type=data_type, limit=limit)
        return self.normalize(records)
