"""Sync Pipeline — Orchestrates data sync from CI/CD platform connectors.

Handles: authentication, incremental fetch, normalization, hygiene scoring,
and result storage. Designed to be called from the nightly orchestrator notebook
or triggered manually via the Data Sources UI.
"""

import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Result of a single connector sync operation."""
    platform: str
    status: str  # success, partial, error
    records_fetched: int = 0
    records_normalized: int = 0
    hygiene_checks_run: int = 0
    duration_ms: int = 0
    error_message: str = ""
    timestamp: str = ""


@dataclass
class SyncReport:
    """Aggregated report across all connector syncs."""
    results: list = field(default_factory=list)
    total_records: int = 0
    total_duration_ms: int = 0
    started_at: str = ""
    completed_at: str = ""

    def add_result(self, result: SyncResult):
        self.results.append(result)
        self.total_records += result.records_fetched
        self.total_duration_ms += result.duration_ms


class SyncPipeline:
    """Orchestrates data sync from configured connectors to storage."""

    def __init__(self, storage_backend=None):
        self.storage = storage_backend
        self._sync_history = []

    def sync_all(self, connector_configs: list[dict]) -> SyncReport:
        """
        Run sync for all configured connectors.

        Each config dict:
            {
                "platform": "github",
                "credentials": {"token": "..."},
                "repos": ["owner/repo1", "owner/repo2"],
                "enabled": True,
            }
        """
        report = SyncReport(started_at=datetime.utcnow().isoformat())

        for config in connector_configs:
            if not config.get("enabled", True):
                continue

            platform = config.get("platform", "unknown")
            logger.info("Starting sync for platform: %s", platform)

            try:
                result = self._sync_single(config)
                report.add_result(result)
                logger.info(
                    "Sync complete: platform=%s records=%d duration=%dms",
                    platform, result.records_fetched, result.duration_ms,
                )
            except Exception as e:
                logger.error("Sync failed for %s: %s", platform, e)
                report.add_result(SyncResult(
                    platform=platform,
                    status="error",
                    error_message=str(e),
                    timestamp=datetime.utcnow().isoformat(),
                ))

        report.completed_at = datetime.utcnow().isoformat()
        self._sync_history.append(report)
        return report

    def sync_hygiene(self, connector_configs: list[dict]) -> dict:
        """
        Run hygiene scoring for all configured connectors.

        Returns dict keyed by platform with hygiene check results.
        """
        from compass.hygiene_scorer import run_all_checks

        connector_data = {}
        for config in connector_configs:
            if not config.get("enabled", True):
                continue

            platform = config.get("platform", "unknown")
            try:
                connector = self._get_connector(config)
                if hasattr(connector, "fetch_repo_hygiene"):
                    hygiene_data = connector.fetch_repo_hygiene()
                    connector_data[platform] = hygiene_data
                    logger.info("Fetched hygiene data for %s: %d keys", platform, len(hygiene_data))
            except Exception as e:
                logger.error("Hygiene fetch failed for %s: %s", platform, e)

        checks = run_all_checks(connector_data=connector_data)
        return checks

    def get_sync_history(self, limit: int = 20) -> list[dict]:
        """Return recent sync history."""
        history = []
        for report in self._sync_history[-limit:]:
            for result in report.results:
                history.append({
                    "platform": result.platform,
                    "status": result.status,
                    "records": result.records_fetched,
                    "duration_ms": result.duration_ms,
                    "error": result.error_message,
                    "timestamp": result.timestamp or report.started_at,
                })
        return history

    def health_check(self, connector_configs: list[dict]) -> list[dict]:
        """Check connectivity health for all configured connectors."""
        results = []
        for config in connector_configs:
            platform = config.get("platform", "unknown")
            start = time.time()
            try:
                connector = self._get_connector(config)
                auth_ok = connector.authenticate()
                latency = int((time.time() - start) * 1000)
                results.append({
                    "platform": platform,
                    "status": "healthy" if auth_ok else "auth_failed",
                    "latency_ms": latency,
                    "data_types": connector.get_data_types() if auth_ok else [],
                })
            except Exception as e:
                latency = int((time.time() - start) * 1000)
                results.append({
                    "platform": platform,
                    "status": "error",
                    "latency_ms": latency,
                    "error": str(e),
                })
        return results

    def _sync_single(self, config: dict) -> SyncResult:
        """Sync a single connector."""
        platform = config.get("platform", "unknown")
        start = time.time()

        connector = self._get_connector(config)
        auth_ok = connector.authenticate()
        if not auth_ok:
            return SyncResult(
                platform=platform,
                status="auth_failed",
                error_message="Authentication failed",
                timestamp=datetime.utcnow().isoformat(),
            )

        total_records = 0
        total_normalized = 0

        for data_type in connector.get_data_types():
            try:
                records = connector.fetch_records(data_type, limit=500)
                total_records += len(records)
                normalized = connector.normalize(records, data_type)
                total_normalized += len(normalized) if hasattr(normalized, '__len__') else 0
            except Exception as e:
                logger.warning("Failed to fetch %s/%s: %s", platform, data_type, e)

        duration_ms = int((time.time() - start) * 1000)

        return SyncResult(
            platform=platform,
            status="success",
            records_fetched=total_records,
            records_normalized=total_normalized,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow().isoformat(),
        )

    def _get_connector(self, config: dict):
        """Instantiate the appropriate connector for a platform."""
        platform = config.get("platform", "")
        credentials = config.get("credentials", {})
        use_mock = config.get("use_mock", False)

        if platform == "github":
            from ingestion.api_connectors.github import GitHubConnector
            return GitHubConnector(credentials, use_mock=use_mock)
        elif platform == "gitlab":
            from ingestion.api_connectors.gitlab import GitLabConnector
            return GitLabConnector(credentials, use_mock=use_mock)
        elif platform == "jenkins":
            from ingestion.api_connectors.jenkins import JenkinsConnector
            return JenkinsConnector(credentials, use_mock=use_mock)
        elif platform == "azure_devops":
            from ingestion.api_connectors.azure_devops import AzureDevOpsConnector
            return AzureDevOpsConnector(credentials, use_mock=use_mock)
        elif platform == "jira":
            from ingestion.api_connectors.jira import JiraConnector
            return JiraConnector(credentials, use_mock=use_mock)
        elif platform == "databricks":
            from ingestion.api_connectors.databricks_workspace import DatabricksWorkspaceConnector
            return DatabricksWorkspaceConnector(credentials, use_mock=use_mock)
        else:
            raise ValueError(f"Unknown platform: {platform}")
