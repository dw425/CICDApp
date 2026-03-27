"""Azure DevOps REST API connector.

Supports: pipelines (builds), releases, pull requests, work items,
          build definitions, branch policies, test runs, repositories.
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

    # Data type -> API endpoint path mapping
    ENDPOINTS = {
        "pipelines":         "_apis/build/builds",
        "releases":          "_apis/release/releases",
        "pull_requests":     "_apis/git/pullrequests",
        "work_items":        "_apis/wit/wiql",
        "build_definitions": "_apis/build/definitions",
        "branch_policies":   "_apis/policy/configurations",
        "test_runs":         "_apis/test/runs",
        "repositories":      "_apis/git/repositories",
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
            {"key": "org_url", "label": "Organization URL",
             "placeholder": "https://dev.azure.com/myorg", "type": "text"},
            {"key": "project", "label": "Project Name",
             "placeholder": "MyProject", "type": "text"},
            {"key": "pat", "label": "Personal Access Token",
             "placeholder": "Paste your PAT", "type": "password"},
        ]

    @classmethod
    def get_data_types(cls) -> list[dict]:
        return [
            {"value": "pipelines",         "label": "Pipelines (Builds)",  "suggested_slot": "pipeline_runs"},
            {"value": "releases",          "label": "Releases",            "suggested_slot": "deployment_events"},
            {"value": "pull_requests",     "label": "Pull Requests",       "suggested_slot": "pull_requests"},
            {"value": "work_items",        "label": "Work Items",          "suggested_slot": "work_items"},
            {"value": "build_definitions", "label": "Build Definitions",   "suggested_slot": "build_definitions"},
            {"value": "branch_policies",   "label": "Branch Policies",     "suggested_slot": "branch_policies"},
            {"value": "test_runs",         "label": "Test Runs",           "suggested_slot": "test_runs"},
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
            url = f"{self.org_url}/{self.project}/_apis/projects?api-version={self.API_VERSION}"
            resp = self._session.get(url, timeout=10)
            self._authenticated = resp.status_code == 200
            return self._authenticated
        except Exception:
            self._authenticated = False
            return False

    # ── Core fetch ────────────────────────────────────────────────

    def fetch_records(self, data_type: str = "pipelines", limit: int = 100, **kwargs) -> list[dict]:
        """Fetch records from Azure DevOps API."""
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
        return resp.json().get("value", [])

    def _fetch_work_items(self, limit: int) -> list[dict]:
        """Work items require WIQL query then individual fetches."""
        if USE_MOCK:
            return self._mock_fetch("work_items", limit)
        wiql_url = f"{self.org_url}/{self.project}/_apis/wit/wiql?api-version={self.API_VERSION}"
        query = {"query": "SELECT [System.Id] FROM WorkItems ORDER BY [System.CreatedDate] DESC"}
        resp = self._session.post(wiql_url, json=query, timeout=30)
        resp.raise_for_status()
        work_item_ids = [wi["id"] for wi in resp.json().get("workItems", [])[:limit]]
        if not work_item_ids:
            return []
        ids_str = ",".join(str(i) for i in work_item_ids)
        items_url = (f"{self.org_url}/{self.project}/_apis/wit/workitems"
                     f"?ids={ids_str}&api-version={self.API_VERSION}")
        resp = self._session.get(items_url, timeout=30)
        resp.raise_for_status()
        return resp.json().get("value", [])

    # ── Specialized fetch methods ─────────────────────────────────

    def fetch_branch_policies(self) -> list[dict]:
        """Fetch branch policy configurations.

        Detects: MinimumApproverCount, Build validation,
        RequiredReviewers, WorkItemLinking.
        """
        if USE_MOCK:
            return self._mock_branch_policies()
        if not self._authenticated:
            self.authenticate()
        endpoint = self.ENDPOINTS["branch_policies"]
        url = f"{self.org_url}/{self.project}/{endpoint}?api-version={self.API_VERSION}"
        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        policies = resp.json().get("value", [])
        results = []
        for p in policies:
            policy_type = p.get("type", {}).get("displayName", "Unknown")
            settings = p.get("settings", {})
            results.append({
                "id": p.get("id"),
                "policy_type": policy_type,
                "is_enabled": p.get("isEnabled", False),
                "is_blocking": p.get("isBlocking", False),
                "minimum_approver_count": settings.get("minimumApproverCount"),
                "creator_vote_counts": settings.get("creatorVoteCounts", False),
                "scope": settings.get("scope", []),
                "settings_raw": settings,
            })
        return results

    def fetch_test_runs(self, build_id: Optional[int] = None) -> list[dict]:
        """Fetch test run results with total/passed/failed counts.

        Args:
            build_id: If provided, filter test runs for a specific build.
        """
        if USE_MOCK:
            return self._mock_test_runs(build_id)
        if not self._authenticated:
            self.authenticate()
        endpoint = self.ENDPOINTS["test_runs"]
        url = f"{self.org_url}/{self.project}/{endpoint}?api-version={self.API_VERSION}"
        if build_id is not None:
            url += f"&buildUri=vstfs:///Build/Build/{build_id}"
        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        runs = resp.json().get("value", [])
        results = []
        for run in runs:
            total = run.get("totalTests", 0)
            passed = run.get("passedTests", 0)
            failed = total - passed
            for stat in run.get("runStatistics", []):
                if stat.get("outcome") == "Failed":
                    failed = stat.get("count", failed)
                elif stat.get("outcome") == "Passed":
                    passed = stat.get("count", passed)
            results.append({
                "run_id": run.get("id"),
                "name": run.get("name", ""),
                "state": run.get("state", ""),
                "total_tests": total,
                "passed_tests": passed,
                "failed_tests": failed,
                "started_date": run.get("startedDate"),
                "completed_date": run.get("completedDate"),
                "build_id": run.get("build", {}).get("id"),
                "build_number": run.get("build", {}).get("number"),
                "is_automated": run.get("isAutomated", False),
            })
        return results

    def fetch_build_definitions(self) -> list[dict]:
        """Fetch build/pipeline definitions.

        Detects YAML vs classic pipelines: process.type 1=classic, 2=YAML.
        """
        if USE_MOCK:
            return self._mock_build_definitions()
        if not self._authenticated:
            self.authenticate()
        endpoint = self.ENDPOINTS["build_definitions"]
        url = f"{self.org_url}/{self.project}/{endpoint}?api-version={self.API_VERSION}"
        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        definitions = resp.json().get("value", [])
        results = []
        for d in definitions:
            process = d.get("process", {})
            process_type = process.get("type", 0)
            results.append({
                "id": d.get("id"),
                "name": d.get("name", ""),
                "path": d.get("path", "\\"),
                "process_type": process_type,
                "pipeline_type": "yaml" if process_type == 2 else "classic",
                "yaml_filename": process.get("yamlFilename", ""),
                "queue_status": d.get("queueStatus", ""),
                "created_date": d.get("createdDate"),
                "revision": d.get("revision", 0),
                "triggers": [t.get("triggerType", "") for t in d.get("triggers", [])],
            })
        return results

    def fetch_repo_hygiene(self) -> dict:
        """Assemble flat dict for ADO hygiene extractor.

        Combines branch policies + build definitions + builds + test data.
        Returns 16 keys matching what ado_hygiene.py expects.
        """
        if USE_MOCK:
            return self._mock_repo_hygiene()

        builds = self.fetch_records(data_type="pipelines", limit=200)
        policies = self.fetch_branch_policies()
        definitions = self.fetch_build_definitions()
        test_runs = self.fetch_test_runs()
        releases = self.fetch_records(data_type="releases", limit=200)
        total_builds = len(builds)

        # Build success rate
        succeeded = sum(1 for b in builds if b.get("result") == "succeeded")
        build_success_pct = round(succeeded / total_builds * 100) if total_builds else 0

        # Build speed (median duration in seconds)
        durations = sorted(
            dur for b in builds
            if (dur := _duration_seconds(b.get("startTime"), b.get("finishTime")))
            and dur > 0
        )
        build_speed_secs = durations[len(durations) // 2] if durations else 0

        # CI-triggered ratio
        ci_triggers = sum(1 for b in builds
                          if b.get("reason") in ("individualCI", "batchedCI"))
        ci_trigger_pct = round(ci_triggers / total_builds * 100) if total_builds else 0

        # Trigger discipline score
        if ci_trigger_pct >= 80:
            trigger_discipline_score = 100
        elif ci_trigger_pct >= 50:
            trigger_discipline_score = 60
        else:
            trigger_discipline_score = 20

        # Work item linking ratio
        linked = sum(1 for b in builds
                     if b.get("triggerInfo", {}).get("ci.sourceBranch"))
        work_item_link_pct = round(linked / total_builds * 100) if total_builds else 0

        # Branch policy flags
        branch_policies_enforced = any(
            p.get("is_enabled") and p.get("is_blocking") for p in policies)
        build_validation_on_pr = any(
            p.get("policy_type") in ("Build", "Build validation")
            and p.get("is_enabled") and p.get("is_blocking") for p in policies)
        reviewer_policies = [
            p for p in policies
            if p.get("policy_type") in ("Minimum number of reviewers", "MinimumApproverCount")
            and p.get("is_enabled")]
        required_reviewers = max(
            (p.get("minimum_approver_count", 0) or 0 for p in reviewer_policies),
            default=0)

        # Build definitions: YAML vs classic
        total_defs = len(definitions)
        yaml_defs = sum(1 for d in definitions if d.get("pipeline_type") == "yaml")
        yaml_pipeline_pct = round(yaml_defs / total_defs * 100) if total_defs else 0

        # Test metrics
        total_test_runs = len(test_runs)
        builds_with_tests = len({t["build_id"] for t in test_runs if t.get("build_id")})
        test_run_pct = round(builds_with_tests / total_builds * 100) if total_builds else 0
        all_passed = sum(t.get("passed_tests", 0) for t in test_runs)
        all_total = sum(t.get("total_tests", 0) for t in test_runs)
        test_pass_rate = round(all_passed / all_total * 100) if all_total else 0

        # Deployment metrics
        deploys_per_week = round(len(releases) / 4, 1) if releases else 0
        envs_with_gates = total_envs = 0
        for rel in releases:
            for env in rel.get("environments", []):
                total_envs += 1
                if env.get("preDeployApprovals", {}).get("approvals"):
                    envs_with_gates += 1
        release_gate_pct = round(envs_with_gates / total_envs * 100) if total_envs else 0

        return {
            "build_success_pct": build_success_pct,
            "build_speed_secs": build_speed_secs,
            "ci_trigger_pct": ci_trigger_pct,
            "branch_policies_enforced": branch_policies_enforced,
            "test_run_pct": test_run_pct,
            "test_pass_rate": test_pass_rate,
            "deploys_per_week": deploys_per_week,
            "release_gate_pct": release_gate_pct,
            "yaml_pipeline_pct": yaml_pipeline_pct,
            "build_validation_on_pr": build_validation_on_pr,
            "trigger_discipline_score": trigger_discipline_score,
            "work_item_link_pct": work_item_link_pct,
            "required_reviewers": required_reviewers,
            "total_builds": total_builds,
            "total_definitions": total_defs,
            "total_test_runs": total_test_runs,
        }

    # ── Normalize ─────────────────────────────────────────────────

    def normalize(self, records: list[dict]) -> pd.DataFrame:
        """Normalize ADO records to a flat DataFrame."""
        if not records:
            return pd.DataFrame()
        rows = []
        for r in records:
            if "buildId" in r or "buildNumber" in r:
                rows.append(self._normalize_pipeline(r))
            elif "pullRequestId" in r:
                rows.append(self._normalize_pr(r))
            elif "fields" in r:
                rows.append(self._normalize_work_item(r))
            elif "policy_type" in r:
                rows.append(self._normalize_branch_policy(r))
            elif "pipeline_type" in r:
                rows.append(self._normalize_build_definition(r))
            elif "total_tests" in r:
                rows.append(self._normalize_test_run(r))
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

    def _normalize_branch_policy(self, r: dict) -> dict:
        return {
            "policy_id": str(r.get("id", "")),
            "policy_type": r.get("policy_type", ""),
            "is_enabled": r.get("is_enabled", False),
            "is_blocking": r.get("is_blocking", False),
            "minimum_approver_count": r.get("minimum_approver_count"),
            "source_system": "azure_devops",
        }

    def _normalize_build_definition(self, r: dict) -> dict:
        return {
            "definition_id": str(r.get("id", "")),
            "name": r.get("name", ""),
            "pipeline_type": r.get("pipeline_type", ""),
            "yaml_filename": r.get("yaml_filename", ""),
            "queue_status": r.get("queue_status", ""),
            "created_date": _parse_date(r.get("created_date")),
            "source_system": "azure_devops",
        }

    def _normalize_test_run(self, r: dict) -> dict:
        return {
            "run_id": str(r.get("run_id", "")),
            "name": r.get("name", ""),
            "state": r.get("state", ""),
            "total_tests": r.get("total_tests", 0),
            "passed_tests": r.get("passed_tests", 0),
            "failed_tests": r.get("failed_tests", 0),
            "is_automated": r.get("is_automated", False),
            "build_id": str(r.get("build_id", "")),
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
        elif data_type == "build_definitions":
            records = self._mock_build_definitions()[:limit]
        elif data_type == "branch_policies":
            records = self._mock_branch_policies()[:limit]
        elif data_type == "test_runs":
            records = self._mock_test_runs()[:limit]

        return records

    def _mock_branch_policies(self) -> list[dict]:
        """Return mock branch policy configs (4 policy types)."""
        return [
            {"id": 1, "policy_type": "Minimum number of reviewers",
             "is_enabled": True, "is_blocking": True,
             "minimum_approver_count": 2, "creator_vote_counts": False,
             "scope": [{"refName": "refs/heads/main", "matchKind": "exact"}],
             "settings_raw": {"minimumApproverCount": 2, "creatorVoteCounts": False}},
            {"id": 2, "policy_type": "Build",
             "is_enabled": True, "is_blocking": True,
             "minimum_approver_count": None, "creator_vote_counts": False,
             "scope": [{"refName": "refs/heads/main", "matchKind": "exact"}],
             "settings_raw": {"buildDefinitionId": 10, "displayName": "CI Build"}},
            {"id": 3, "policy_type": "Required reviewers",
             "is_enabled": True, "is_blocking": True,
             "minimum_approver_count": None, "creator_vote_counts": False,
             "scope": [{"refName": "refs/heads/main", "matchKind": "exact"}],
             "settings_raw": {"requiredReviewerIds": ["user-guid-1"]}},
            {"id": 4, "policy_type": "Work item linking",
             "is_enabled": True, "is_blocking": False,
             "minimum_approver_count": None, "creator_vote_counts": False,
             "scope": [{"refName": "refs/heads/main", "matchKind": "exact"}],
             "settings_raw": {}},
        ]

    def _mock_test_runs(self, build_id: Optional[int] = None) -> list[dict]:
        """Return mock test run results (12 runs)."""
        import random
        runs = []
        for i in range(12):
            bid = build_id if build_id else 1000 + i
            total = random.randint(20, 150)
            passed = int(total * random.uniform(0.78, 0.98))
            runs.append({
                "run_id": 5000 + i,
                "name": f"Test Run {i + 1} - {'Unit' if i % 2 == 0 else 'Integration'} Tests",
                "state": "Completed",
                "total_tests": total, "passed_tests": passed,
                "failed_tests": total - passed,
                "started_date": f"2026-03-{27 - i % 28:02d}T11:00:00Z",
                "completed_date": f"2026-03-{27 - i % 28:02d}T11:{random.randint(5, 25):02d}:00Z",
                "build_id": bid,
                "build_number": f"20260327.{i}",
                "is_automated": random.choice([True, True, True, False]),
            })
        if build_id is not None:
            runs = [r for r in runs if r["build_id"] == build_id]
        return runs

    def _mock_build_definitions(self) -> list[dict]:
        """Return mock build/pipeline definitions (8 definitions)."""
        import random
        names = ["ci-main", "ci-feature-branches", "nightly-build", "deploy-staging",
                 "deploy-prod", "pr-validation", "integration-tests", "release-pipeline"]
        definitions = []
        for i, name in enumerate(names):
            is_yaml = i < 5  # First 5 YAML, last 3 classic
            definitions.append({
                "id": 10 + i, "name": name, "path": "\\",
                "process_type": 2 if is_yaml else 1,
                "pipeline_type": "yaml" if is_yaml else "classic",
                "yaml_filename": f"azure-pipelines-{name}.yml" if is_yaml else "",
                "queue_status": "enabled",
                "created_date": f"2025-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}T10:00:00Z",
                "revision": random.randint(1, 30),
                "triggers": random.choice([
                    ["continuousIntegration"], ["manual"],
                    ["continuousIntegration", "schedule"]]),
            })
        return definitions

    def _mock_repo_hygiene(self) -> dict:
        """Return mock hygiene data matching all 16 keys expected by ado_hygiene.py."""
        import random
        return {
            "build_success_pct": random.randint(70, 92),
            "build_speed_secs": random.choice([300, 600, 900]),
            "ci_trigger_pct": random.randint(50, 85),
            "branch_policies_enforced": random.choice([True, True, False]),
            "test_run_pct": random.randint(30, 70),
            "test_pass_rate": random.randint(80, 96),
            "deploys_per_week": round(random.uniform(0.5, 5.0), 1),
            "release_gate_pct": random.randint(30, 80),
            "yaml_pipeline_pct": random.randint(20, 70),
            "build_validation_on_pr": True,
            "trigger_discipline_score": random.choice([40, 60, 80]),
            "work_item_link_pct": random.randint(20, 60),
            "required_reviewers": random.choice([1, 2, 2]),
            "total_builds": random.randint(80, 200),
            "total_definitions": 8,
            "total_test_runs": random.randint(10, 50),
        }


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
