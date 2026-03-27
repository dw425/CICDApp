"""Connector registry — maps source_type strings to connector classes."""

from ingestion.api_connectors.azure_devops import AzureDevOpsConnector
from ingestion.api_connectors.github import GitHubConnector


CONNECTOR_REGISTRY = {
    "azure_devops": AzureDevOpsConnector,
    "github": GitHubConnector,
}


def get_connector(source_type: str, config: dict):
    """Instantiate and return a connector for the given source type.

    Args:
        source_type: One of the keys in CONNECTOR_REGISTRY
        config: Connection configuration dict

    Returns:
        BaseConnector instance

    Raises:
        ValueError: If source_type is not registered
    """
    cls = CONNECTOR_REGISTRY.get(source_type)
    if cls is None:
        raise ValueError(f"Unknown source type: {source_type}. Available: {list(CONNECTOR_REGISTRY.keys())}")
    return cls(config)
