"""GitHub REST API connector.

Supports: workflow runs, pull requests, issues, deployments.
Auth: Personal Access Token via Bearer header.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd

from config.settings import USE_MOCK
from ingestion.api_connectors.base_connector import BaseConnector


class GitHubConnector(BaseConnector):
    """Connector for GitHub REST API."""

    BASE_URL = "https://api.github.com"

    # Data type → endpoint template mapping
    ENDPOINTS = {
        "workflows": "/repos/{owner}/{repo}/actions/runs",
        "pull_requests": "/repos/{owner}/{repo}/pulls",
        "issues": "/repos/{owner}/{repo}/issues",
        "deployments": "/repos/{owner}/{repo}/deployments",
    }

    def __init__(self, config: dict):
        super().__init__(config)
        self.owner = config.get("owner", "")
        self.repo = config.get("repo", "")
        self.token = config.get("token", "")
        self._session = None

    @classmethod
    def get_required_config_fields(cls) -> list[dict]:
        return [
            {"key": "owner", "label": "Owner / Organization", "placeholder": "my-org", "type": "text"},
            {"key": "repo", "label": "Repository (optional)", "placeholder": "my-repo", "type": "text"},
            {"key": "token", "label": "Personal Access Token", "placeholder": "ghp_...", "type": "password"},
        ]

    @classmethod
    def get_data_types(cls) -> list[dict]:
        return [
            {"value": "workflows", "label": "Workflow Runs", "suggested_slot": "pipeline_runs"},
            {"value": "pull_requests", "label": "Pull Requests", "suggested_slot": "pull_requests"},
            {"value": "issues", "label": "Issues", "suggested_slot": "work_items"},
            {"value": "deployments", "label": "Deployments", "suggested_slot": "deployment_events"},
        ]

    def authenticate(self) -> bool:
        """Authenticate using Bearer token."""
        if USE_MOCK:
            self._authenticated = bool(self.owner and self.token)
            return self._authenticated

        try:
            import requests
            self._session = requests.Session()
            self._session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            })

            resp = self._session.get(f"{self.BASE_URL}/user", timeout=10)
            self._authenticated = resp.status_code == 200
            return self._authenticated

        except Exception:
            self._authenticated = False
            return False

    def fetch_records(self, data_type: str = "workflows", limit: int = 100, **kwargs) -> list[dict]:
        """Fetch records from GitHub API.

        Args:
            data_type: One of workflows, pull_requests, issues, deployments
            limit: Maximum records to fetch
        """
        if USE_MOCK:
            return self._mock_fetch(data_type, limit)

        if not self._authenticated:
            self.authenticate()

        endpoint_template = self.ENDPOINTS.get(data_type, self.ENDPOINTS["workflows"])
        endpoint = endpoint_template.format(owner=self.owner, repo=self.repo)
        url = f"{self.BASE_URL}{endpoint}"

        params = {"per_page": min(limit, 100), "state": "all"}
        if data_type == "pull_requests":
            params["state"] = "all"

        all_records = []
        page = 1
        while len(all_records) < limit:
            params["page"] = page
            resp = self._session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            # Workflows returns nested structure
            if data_type == "workflows" and isinstance(data, dict):
                records = data.get("workflow_runs", [])
            else:
                records = data if isinstance(data, list) else data.get("items", [])

            if not records:
                break

            all_records.extend(records)
            page += 1

            if len(records) < params["per_page"]:
                break

        return all_records[:limit]

    def normalize(self, records: list[dict]) -> pd.DataFrame:
        """Normalize GitHub records to a flat DataFrame."""
        if not records:
            return pd.DataFrame()

        rows = []
        for r in records:
            if "workflow_id" in r or "run_number" in r:
                rows.append(self._normalize_workflow(r))
            elif "pull_request" in r or ("number" in r and "merged_at" not in r and "commits_url" not in r):
                rows.append(self._normalize_issue(r))
            elif "merged_at" in r or "commits_url" in r:
                rows.append(self._normalize_pr(r))
            elif "environment" in r and "creator" in r:
                rows.append(self._normalize_deployment(r))
            else:
                # Fallback: try as PR first, then issue
                if "pull_request" in r:
                    rows.append(self._normalize_pr(r))
                else:
                    rows.append(self._normalize_issue(r))

        return pd.DataFrame(rows)

    def _normalize_workflow(self, r: dict) -> dict:
        return {
            "run_id": str(r.get("id", "")),
            "pipeline_name": r.get("name", ""),
            "status": r.get("conclusion", r.get("status", "")),
            "run_date": _parse_date(r.get("created_at")),
            "duration_seconds": _duration_seconds(r.get("created_at"), r.get("updated_at")),
            "trigger_type": r.get("event", ""),
            "source_system": "github",
        }

    def _normalize_pr(self, r: dict) -> dict:
        return {
            "pr_id": str(r.get("number", r.get("id", ""))),
            "title": r.get("title", ""),
            "status": "merged" if r.get("merged_at") else r.get("state", ""),
            "event_date": _parse_date(r.get("created_at")),
            "author": r.get("user", {}).get("login", ""),
            "repo_name": r.get("head", {}).get("repo", {}).get("name", self.repo),
            "reviewers_count": len(r.get("requested_reviewers", [])),
            "source_system": "github",
        }

    def _normalize_issue(self, r: dict) -> dict:
        return {
            "item_id": str(r.get("number", r.get("id", ""))),
            "title": r.get("title", ""),
            "item_type": "issue",
            "status": r.get("state", ""),
            "event_date": _parse_date(r.get("created_at")),
            "priority": ",".join(l.get("name", "") for l in r.get("labels", [])),
            "source_system": "github",
        }

    def _normalize_deployment(self, r: dict) -> dict:
        return {
            "event_id": str(r.get("id", "")),
            "event_date": _parse_date(r.get("created_at")),
            "environment": r.get("environment", ""),
            "status": r.get("task", ""),
            "actor_type": "human",
            "source_system": "github",
        }

    # ── Mock data ─────────────────────────────────────────────────

    def _mock_fetch(self, data_type: str, limit: int) -> list[dict]:
        """Return mock GitHub records for wizard preview."""
        import random
        records = []

        if data_type == "workflows":
            for i in range(min(limit, 25)):
                records.append({
                    "id": 2000 + i,
                    "name": random.choice(["CI Build", "Deploy", "Tests", "Lint"]),
                    "status": "completed",
                    "conclusion": random.choice(["success", "failure", "success", "success"]),
                    "created_at": f"2026-03-{27 - i % 28:02d}T08:00:00Z",
                    "updated_at": f"2026-03-{27 - i % 28:02d}T08:{random.randint(2, 20):02d}:00Z",
                    "run_number": 100 + i,
                    "workflow_id": 10,
                    "head_branch": random.choice(["main", "develop", "feature/x"]),
                    "event": random.choice(["push", "pull_request", "schedule"]),
                })

        elif data_type == "pull_requests":
            for i in range(min(limit, 25)):
                merged = random.choice([True, True, False])
                records.append({
                    "number": 100 + i,
                    "title": f"feat: implement feature {random.randint(1, 50)}",
                    "state": "closed" if merged or random.random() < 0.2 else "open",
                    "created_at": f"2026-03-{27 - i % 28:02d}T09:00:00Z",
                    "merged_at": f"2026-03-{27 - i % 28:02d}T16:00:00Z" if merged else None,
                    "closed_at": f"2026-03-{27 - i % 28:02d}T17:00:00Z" if merged else None,
                    "user": {"login": f"dev{i % 5}"},
                    "head": {"repo": {"name": random.choice(["api-service", "frontend"])}},
                    "requested_reviewers": [{"login": "reviewer"}] * random.randint(0, 3),
                    "commits_url": "...",
                })

        elif data_type == "issues":
            for i in range(min(limit, 25)):
                records.append({
                    "number": 200 + i,
                    "title": f"Bug: unexpected behavior in {random.choice(['auth', 'api', 'ui', 'data'])} module",
                    "state": random.choice(["open", "closed", "open", "closed"]),
                    "created_at": f"2026-03-{27 - i % 28:02d}T10:00:00Z",
                    "closed_at": f"2026-03-{27 - i % 28:02d}T15:00:00Z" if i % 2 == 0 else None,
                    "user": {"login": f"dev{i % 5}"},
                    "labels": [{"name": random.choice(["bug", "enhancement", "p1", "p2"])}],
                    "assignees": [{"login": f"dev{(i + 1) % 5}"}],
                })

        elif data_type == "deployments":
            for i in range(min(limit, 25)):
                records.append({
                    "id": 3000 + i,
                    "ref": "main",
                    "environment": random.choice(["production", "staging", "development"]),
                    "created_at": f"2026-03-{27 - i % 28:02d}T14:00:00Z",
                    "updated_at": f"2026-03-{27 - i % 28:02d}T14:05:00Z",
                    "creator": {"login": f"deployer{i % 3}"},
                    "description": f"Deploy #{i + 1}",
                    "task": "deploy",
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
