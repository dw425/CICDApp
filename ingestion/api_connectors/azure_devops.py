"""Azure DevOps REST API connector.

Supports: pipelines (builds), releases, pull requests, work items.
Auth: Personal Access Token via Basic auth header.
"""

from __future__ import annotations

import base64
from datetime import datetime
from typing import Optional

import pandas as pd

from config.settings import USE_MOCK
from ingestion.api_connectors.base_connector import BaseConnector


class AzureDevOpsConnector(BaseConnector):
    """Connector for Azure DevOps REST API."""

    API_VERSION = "7.1"

    # Data type → API endpoint path mapping
    ENDPOINTS = {
        "pipelines": "_apis/build/builds",
        "releases": "_apis/release/releases",
        "pull_requests": "_apis/git/pullrequests",
        "work_items": "_apis/wit/wiql",
    }

    def __init__(self, config: dict):
        super().__init__(config)
        self.org_url = config.get("org_url", "").rstrip("/")
        self.project = config.get("project", "")
        self.pat = config.get("pat", "")
        self._session = None

    @classmethod
    def get_required_config_fields(cls) -> list[dict]:
        return [
            {"key": "org_url", "label": "Organization URL", "placeholder": "https://dev.azure.com/myorg", "type": "text"},
            {"key": "project", "label": "Project Name", "placeholder": "MyProject", "type": "text"},
            {"key": "pat", "label": "Personal Access Token", "placeholder": "Paste your PAT", "type": "password"},
        ]

    @classmethod
    def get_data_types(cls) -> list[dict]:
        return [
            {"value": "pipelines", "label": "Pipelines (Builds)", "suggested_slot": "pipeline_runs"},
            {"value": "releases", "label": "Releases", "suggested_slot": "deployment_events"},
            {"value": "pull_requests", "label": "Pull Requests", "suggested_slot": "pull_requests"},
            {"value": "work_items", "label": "Work Items", "suggested_slot": "work_items"},
        ]

    def authenticate(self) -> bool:
        """Authenticate using PAT via Basic auth."""
        if USE_MOCK:
            self._authenticated = bool(self.org_url and self.project and self.pat)
            return self._authenticated

        try:
            import requests
            token_bytes = base64.b64encode(f":{self.pat}".encode()).decode()
            self._session = requests.Session()
            self._session.headers.update({
                "Authorization": f"Basic {token_bytes}",
                "Content-Type": "application/json",
            })

            # Test with a simple API call
            url = f"{self.org_url}/{self.project}/_apis/projects?api-version={self.API_VERSION}"
            resp = self._session.get(url, timeout=10)
            self._authenticated = resp.status_code == 200
            return self._authenticated

        except Exception:
            self._authenticated = False
            return False

    def fetch_records(self, data_type: str = "pipelines", limit: int = 100, **kwargs) -> list[dict]:
        """Fetch records from Azure DevOps API.

        Args:
            data_type: One of pipelines, releases, pull_requests, work_items
            limit: Maximum records to fetch
        """
        if USE_MOCK:
            return self._mock_fetch(data_type, limit)

        if not self._authenticated:
            self.authenticate()

        endpoint = self.ENDPOINTS.get(data_type, self.ENDPOINTS["pipelines"])

        if data_type == "work_items":
            return self._fetch_work_items(limit)

        url = f"{self.org_url}/{self.project}/{endpoint}?api-version={self.API_VERSION}&$top={limit}"
        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("value", [])

    def _fetch_work_items(self, limit: int) -> list[dict]:
        """Work items require WIQL query then individual fetches."""
        if USE_MOCK:
            return self._mock_fetch("work_items", limit)

        wiql_url = f"{self.org_url}/{self.project}/_apis/wit/wiql?api-version={self.API_VERSION}"
        query = {"query": f"SELECT [System.Id] FROM WorkItems ORDER BY [System.CreatedDate] DESC"}
        resp = self._session.post(wiql_url, json=query, timeout=30)
        resp.raise_for_status()

        work_item_ids = [wi["id"] for wi in resp.json().get("workItems", [])[:limit]]
        if not work_item_ids:
            return []

        ids_str = ",".join(str(i) for i in work_item_ids)
        items_url = f"{self.org_url}/{self.project}/_apis/wit/workitems?ids={ids_str}&api-version={self.API_VERSION}"
        resp = self._session.get(items_url, timeout=30)
        resp.raise_for_status()
        return resp.json().get("value", [])

    def normalize(self, records: list[dict]) -> pd.DataFrame:
        """Normalize ADO records to a flat DataFrame."""
        if not records:
            return pd.DataFrame()

        rows = []
        for r in records:
            # Detect record type by available fields
            if "buildId" in r or "buildNumber" in r:
                rows.append(self._normalize_pipeline(r))
            elif "pullRequestId" in r:
                rows.append(self._normalize_pr(r))
            elif "fields" in r:
                rows.append(self._normalize_work_item(r))
            else:
                rows.append(self._normalize_release(r))

        return pd.DataFrame(rows)

    def _normalize_pipeline(self, r: dict) -> dict:
        return {
            "run_id": str(r.get("id", r.get("buildId", ""))),
            "pipeline_name": r.get("definition", {}).get("name", ""),
            "status": r.get("result", r.get("status", "")),
            "run_date": _parse_date(r.get("finishTime") or r.get("queueTime")),
            "duration_seconds": _duration_seconds(r.get("startTime"), r.get("finishTime")),
            "trigger_type": r.get("reason", ""),
            "source_system": "azure_devops",
        }

    def _normalize_pr(self, r: dict) -> dict:
        return {
            "pr_id": str(r.get("pullRequestId", "")),
            "title": r.get("title", ""),
            "status": r.get("status", ""),
            "event_date": _parse_date(r.get("creationDate")),
            "author": r.get("createdBy", {}).get("displayName", ""),
            "repo_name": r.get("repository", {}).get("name", ""),
            "reviewers_count": len(r.get("reviewers", [])),
            "source_system": "azure_devops",
        }

    def _normalize_work_item(self, r: dict) -> dict:
        fields = r.get("fields", {})
        return {
            "item_id": str(r.get("id", "")),
            "title": fields.get("System.Title", ""),
            "item_type": fields.get("System.WorkItemType", ""),
            "status": fields.get("System.State", ""),
            "event_date": _parse_date(fields.get("System.CreatedDate")),
            "priority": str(fields.get("System.Priority", "")),
            "source_system": "azure_devops",
        }

    def _normalize_release(self, r: dict) -> dict:
        return {
            "event_id": str(r.get("id", "")),
            "event_date": _parse_date(r.get("createdOn")),
            "environment": ",".join(
                e.get("name", "") for e in r.get("environments", [])
            ) if r.get("environments") else "",
            "status": r.get("status", ""),
            "source_system": "azure_devops",
        }

    # ── Mock data ─────────────────────────────────────────────────

    def _mock_fetch(self, data_type: str, limit: int) -> list[dict]:
        """Return mock ADO records for wizard preview."""
        import random
        records = []

        if data_type == "pipelines":
            for i in range(min(limit, 25)):
                records.append({
                    "buildId": 1000 + i,
                    "buildNumber": f"20260327.{i}",
                    "status": "completed",
                    "result": random.choice(["succeeded", "failed", "succeeded", "succeeded"]),
                    "queueTime": f"2026-03-{27 - i % 28:02d}T10:00:00Z",
                    "startTime": f"2026-03-{27 - i % 28:02d}T10:00:30Z",
                    "finishTime": f"2026-03-{27 - i % 28:02d}T10:{random.randint(2, 15):02d}:00Z",
                    "definition": {"name": random.choice(["build-main", "ci-test", "deploy-staging"])},
                    "requestedFor": {"displayName": f"dev{i % 5}@company.com"},
                    "reason": random.choice(["manual", "schedule", "individualCI"]),
                })

        elif data_type == "pull_requests":
            for i in range(min(limit, 25)):
                records.append({
                    "pullRequestId": 500 + i,
                    "title": f"Fix: update config for module {random.randint(1, 20)}",
                    "status": random.choice(["active", "completed", "abandoned", "completed"]),
                    "creationDate": f"2026-03-{27 - i % 28:02d}T09:00:00Z",
                    "closedDate": f"2026-03-{27 - i % 28:02d}T17:00:00Z" if i % 3 != 0 else None,
                    "createdBy": {"displayName": f"dev{i % 5}@company.com"},
                    "repository": {"name": random.choice(["api-service", "frontend", "data-pipeline"])},
                    "reviewers": [{"displayName": "reviewer"}] * random.randint(1, 3),
                })

        elif data_type == "work_items":
            for i in range(min(limit, 25)):
                records.append({
                    "id": 800 + i,
                    "fields": {
                        "System.Title": f"Implement feature {random.randint(100, 999)}",
                        "System.WorkItemType": random.choice(["Task", "User Story", "Bug"]),
                        "System.State": random.choice(["New", "Active", "Closed", "Resolved"]),
                        "System.CreatedDate": f"2026-03-{27 - i % 28:02d}T08:00:00Z",
                        "System.Priority": random.choice([1, 2, 3, 4]),
                        "System.AssignedTo": f"dev{i % 5}@company.com",
                    },
                })

        elif data_type == "releases":
            for i in range(min(limit, 25)):
                records.append({
                    "id": 300 + i,
                    "name": f"Release-{i + 1}",
                    "status": random.choice(["active", "abandoned", "active"]),
                    "createdOn": f"2026-03-{27 - i % 28:02d}T12:00:00Z",
                    "environments": [
                        {"name": "dev", "status": "succeeded"},
                        {"name": "staging", "status": random.choice(["succeeded", "inProgress"])},
                    ],
                    "releaseDefinition": {"name": "main-release"},
                })

        return records


# ── Utility functions ─────────────────────────────────────────────

def _parse_date(date_str: Optional[str]) -> Optional[str]:
    """Parse ISO date string to YYYY-MM-DD."""
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return date_str[:10] if date_str and len(date_str) >= 10 else None


def _duration_seconds(start: Optional[str], finish: Optional[str]) -> Optional[float]:
    """Calculate duration in seconds between two ISO timestamps."""
    if not start or not finish:
        return None
    try:
        s = datetime.fromisoformat(start.replace("Z", "+00:00"))
        f = datetime.fromisoformat(finish.replace("Z", "+00:00"))
        return (f - s).total_seconds()
    except (ValueError, TypeError):
        return None
