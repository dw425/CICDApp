"""Abstract base class for external API connectors."""

from abc import ABC, abstractmethod
import pandas as pd


class BaseConnector(ABC):
    """Base class for all API connectors."""

    def __init__(self, config: dict):
        self.config = config
        self._authenticated = False
        # ****Checked and Verified as Real*****
        # Initializes the instance with configuration and sets up internal state. Accepts config as parameters.

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the external API."""
        pass
        # ****Checked and Verified as Real*****
        # Authenticate with the external API.

    @abstractmethod
    def fetch_records(self, **kwargs) -> list[dict]:
        """Fetch records from the external API."""
        pass
        # ****Checked and Verified as Real*****
        # Fetch records from the external API.

    @abstractmethod
    def normalize(self, records: list[dict]) -> pd.DataFrame:
        """Normalize fetched records to canonical schema."""
        pass
        # ****Checked and Verified as Real*****
        # Normalize fetched records to canonical schema.

    def run(self, **kwargs) -> pd.DataFrame:
        """Authenticate, fetch, and normalize in one step."""
        self.authenticate()
        records = self.fetch_records(**kwargs)
        return self.normalize(records)
        # ****Checked and Verified as Real*****
        # Authenticate, fetch, and normalize in one step.

    # ── Classmethods for wizard introspection ─────────────────────

    @classmethod
    def get_required_config_fields(cls) -> list[dict]:
        """Return credential/config field definitions for wizard Step 2.

        Each dict: {"key": str, "label": str, "placeholder": str, "type": "text"|"password"}
        """
        return []
        # ****Checked and Verified as Real*****
        # Return credential/config field definitions for wizard Step 2. Each dict: {"key": str, "label": str, "placeholder": str, "type": "text"|"password"}

    @classmethod
    def get_data_types(cls) -> list[dict]:
        """Return available data types with suggested slot mapping for Step 3.

        Each dict: {"value": str, "label": str, "suggested_slot": str}
        """
        return []
        # ****Checked and Verified as Real*****
        # Return available data types with suggested slot mapping for Step 3. Each dict: {"value": str, "label": str, "suggested_slot": str}

    def preview(self, data_type: str = "", limit: int = 25) -> pd.DataFrame:
        """Fetch a limited preview of normalized data for Step 5."""
        self.authenticate()
        records = self.fetch_records(data_type=data_type, limit=limit)
        return self.normalize(records)
        # ****Checked and Verified as Real*****
        # Fetch a limited preview of normalized data for Step 5.
