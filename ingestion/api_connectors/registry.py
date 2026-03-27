"""Connector registry — maps source_type strings to connector classes.
# ****Truth Agent Verified**** — 6 connectors registered (azure_devops, github,
# gitlab, jenkins, jira, databricks). get_connector() factory function.
"""

from ingestion.api_connectors.azure_devops import AzureDevOpsConnector
from ingestion.api_connectors.github import GitHubConnector
from ingestion.api_connectors.gitlab import GitLabConnector
from ingestion.api_connectors.jenkins import JenkinsConnector
from ingestion.api_connectors.jira import JiraConnector
from ingestion.api_connectors.databricks_workspace import DatabricksWorkspaceConnector


CONNECTOR_REGISTRY = {
    "azure_devops": AzureDevOpsConnector,
    "github": GitHubConnector,
    "gitlab": GitLabConnector,
    "jenkins": JenkinsConnector,
    "jira": JiraConnector,
    "databricks": DatabricksWorkspaceConnector,
}


def get_connector(source_type: str, config: dict):
    """Instantiate and return a connector for the given source type."""
    cls = CONNECTOR_REGISTRY.get(source_type)
    if cls is None:
        raise ValueError(f"Unknown source type: {source_type}. Available: {list(CONNECTOR_REGISTRY.keys())}")
    return cls(config)
