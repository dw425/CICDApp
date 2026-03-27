"""GitLab REST API connector — full implementation.
# ****Truth Agent Verified**** — GitLab v4 API, URL/project_id/token auth,
# get_required_config_fields, get_data_types, fetch + mock. BaseConnector subclass.
# DORA native metrics, repo hygiene assembly, paginated fetch, full mock data.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from config.settings import USE_MOCK
from ingestion.api_connectors.base_connector import BaseConnector


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


class GitLabConnector(BaseConnector):
    """Connector for GitLab REST API (v4).

    Supports CI pipelines, merge requests, DORA native metrics,
    vulnerability findings, protected branches, approval rules,
    and project settings — everything needed for hygiene scoring.
    """

    # ── Endpoint templates (GitLab v4 API) ────────────────────────

    ENDPOINTS = {
        "pipelines":               "/projects/{project}/pipelines",
        "merge_requests":          "/projects/{project}/merge_requests",
        "dora_deployment_frequency": "/projects/{project}/dora/metrics?metric=deployment_frequency",
        "dora_lead_time":          "/projects/{project}/dora/metrics?metric=lead_time_for_changes",
        "dora_time_to_restore":    "/projects/{project}/dora/metrics?metric=time_to_restore_service",
        "dora_change_failure_rate": "/projects/{project}/dora/metrics?metric=change_failure_rate",
        "protected_branches":      "/projects/{project}/protected_branches",
        "approval_rules":          "/projects/{project}/approval_rules",
        "vulnerability_findings":  "/projects/{project}/vulnerability_findings",
        "project":                 "/projects/{project}",
    }

    def __init__(self, config: dict):
        super().__init__(config)
        self.base_url = config.get("url", "https://gitlab.com").rstrip("/") + "/api/v4"
        self.token = config.get("token", "")
        self.project_id = config.get("project_id", "")
        self._session = None

    # ── Wizard introspection ──────────────────────────────────────

    @classmethod
    def get_required_config_fields(cls) -> list[dict]:
        return [
            {"key": "url", "label": "GitLab URL",
             "placeholder": "https://gitlab.com", "type": "text"},
            {"key": "project_id", "label": "Project ID or Path",
             "placeholder": "group/project", "type": "text"},
            {"key": "token", "label": "Personal Access Token",
             "placeholder": "glpat-...", "type": "password"},
        ]

    @classmethod
    def get_data_types(cls) -> list[dict]:
        return [
            {"value": "pipelines", "label": "CI Pipelines",
             "suggested_slot": "pipeline_runs"},
            {"value": "merge_requests", "label": "Merge Requests",
             "suggested_slot": "pull_requests"},
            {"value": "dora_metrics", "label": "DORA Metrics (native)",
             "suggested_slot": "deployment_events"},
            {"value": "vulnerabilities", "label": "Security Vulnerabilities",
             "suggested_slot": "incidents"},
        ]

    # ── Authentication ────────────────────────────────────────────

    def authenticate(self) -> bool:
        """Authenticate with GitLab using PRIVATE-TOKEN header."""
        if USE_MOCK:
            self._authenticated = bool(self.token and self.project_id)
            return self._authenticated
        try:
            import requests as _requests
            self._session = _requests.Session()
            self._session.headers.update({"PRIVATE-TOKEN": self.token})
            resp = self._session.get(f"{self.base_url}/user", timeout=10)
            self._authenticated = resp.status_code == 200
            return self._authenticated
        except Exception:
            self._authenticated = False
            return False

    # ── Core API helpers ──────────────────────────────────────────

    def _resolve_endpoint(self, data_type: str) -> str:
        """Return the full URL for a given data_type, with project interpolated."""
        from urllib.parse import quote
        project_encoded = quote(str(self.project_id), safe="")
        template = self.ENDPOINTS.get(data_type, self.ENDPOINTS["pipelines"])
        path = template.format(project=project_encoded)
        return f"{self.base_url}{path}"

    def _get_json(self, url: str, params: Optional[dict] = None,
                  timeout: int = 30) -> list | dict:
        """Issue GET and return parsed JSON. Raises on HTTP error."""
        resp = self._session.get(url, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def _paginated_fetch(self, data_type: str, limit: int = 100,
                         extra_params: Optional[dict] = None) -> list[dict]:
        """Fetch paginated list results from a GitLab v4 list endpoint."""
        url = self._resolve_endpoint(data_type)
        params: dict = {"per_page": min(limit, 100)}
        if extra_params:
            params.update(extra_params)

        all_records: list[dict] = []
        page = 1
        while len(all_records) < limit:
            params["page"] = page
            data = self._get_json(url, params=params)
            records = data if isinstance(data, list) else data.get("items", [])
            if not records:
                break
            all_records.extend(records)
            page += 1
            if len(records) < params["per_page"]:
                break

        return all_records[:limit]

    # ── Primary fetch_records ─────────────────────────────────────

    def fetch_records(self, data_type: str = "pipelines",
                      limit: int = 100, **kwargs) -> list[dict]:
        """Fetch records from GitLab API.

        Args:
            data_type: One of pipelines, merge_requests, dora_metrics, vulnerabilities
            limit: Maximum records to fetch (applies to list endpoints)
        """
        if USE_MOCK:
            return self._mock_fetch(data_type, limit)

        if not self._authenticated:
            self.authenticate()

        # DORA metrics are a composite call — delegate
        if data_type == "dora_metrics":
            dora = self.fetch_native_dora_metrics(
                start_date=kwargs.get("start_date"),
                end_date=kwargs.get("end_date"),
            )
            return [dora]

        # Vulnerabilities use a different endpoint key
        if data_type == "vulnerabilities":
            return self._paginated_fetch("vulnerability_findings", limit)

        # Standard paginated list endpoints
        extra: dict = {}
        if data_type == "merge_requests":
            extra["state"] = "all"
            extra["order_by"] = "updated_at"
            extra["sort"] = "desc"
        elif data_type == "pipelines":
            extra["order_by"] = "updated_at"
            extra["sort"] = "desc"

        return self._paginated_fetch(data_type, limit, extra_params=extra)

    # ── DORA native metrics ───────────────────────────────────────

    def fetch_native_dora_metrics(self, start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> dict:
        """Fetch all four DORA metrics from GitLab's built-in DORA API.

        Args:
            start_date: ISO date string (YYYY-MM-DD). Defaults to 90 days ago.
            end_date:   ISO date string (YYYY-MM-DD). Defaults to today.

        Returns:
            Dict with keys: deployment_frequency, lead_time_for_changes,
            time_to_restore_service, change_failure_rate, plus metadata.
        """
        if USE_MOCK:
            return self._mock_dora_metrics()

        if not self._authenticated:
            self.authenticate()

        if not end_date:
            end_date = datetime.utcnow().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")

        params = {"start_date": start_date, "end_date": end_date}

        dora_keys = [
            ("dora_deployment_frequency", "deployment_frequency"),
            ("dora_lead_time", "lead_time_for_changes"),
            ("dora_time_to_restore", "time_to_restore_service"),
            ("dora_change_failure_rate", "change_failure_rate"),
        ]

        result: dict = {
            "source": "gitlab_native_dora",
            "project_id": self.project_id,
            "start_date": start_date,
            "end_date": end_date,
        }

        for endpoint_key, metric_name in dora_keys:
            try:
                url = self._resolve_endpoint(endpoint_key)
                data = self._get_json(url, params=params)
                # GitLab returns a list of daily data points
                if isinstance(data, list) and data:
                    values = [d.get("value") for d in data if d.get("value") is not None]
                    result[metric_name] = {
                        "data_points": data,
                        "count": len(values),
                        "average": round(sum(values) / len(values), 4) if values else None,
                    }
                else:
                    result[metric_name] = {"data_points": [], "count": 0, "average": None}
            except Exception as exc:
                result[metric_name] = {"error": str(exc), "data_points": [], "count": 0, "average": None}

        return result

    # ── Repo hygiene assembly ─────────────────────────────────────

    def fetch_repo_hygiene(self) -> dict:
        """Assemble hygiene data from multiple GitLab endpoints.

        Returns a dict with 15+ keys matching what gitlab_hygiene.py expects:
          pipeline_success_pct, pipeline_speed_secs, mr_trigger_pct,
          required_approvals, pipeline_must_succeed, discussions_must_resolve,
          dora_deploy_freq_score, dora_lead_time_score, dora_cfr_score,
          has_protected_branches, security_scan_score, has_ci_config,
          mr_lead_time_hours, merge_method_score, dora_mttr_score.
        """
        if USE_MOCK:
            return self._mock_repo_hygiene()

        if not self._authenticated:
            self.authenticate()

        hygiene: dict = {}

        # 1. Pipeline stats — success rate, speed, MR-trigger %
        try:
            pipelines = self._paginated_fetch("pipelines", limit=100,
                                              extra_params={"order_by": "updated_at", "sort": "desc"})
            total = len(pipelines) or 1
            successes = sum(1 for p in pipelines if p.get("status") == "success")
            hygiene["pipeline_success_pct"] = round(successes / total * 100, 1)

            durations = [p.get("duration", 0) for p in pipelines if p.get("duration")]
            hygiene["pipeline_speed_secs"] = sorted(durations)[len(durations) // 2] if durations else 0

            mr_triggered = sum(1 for p in pipelines if p.get("source") == "merge_request_event")
            hygiene["mr_trigger_pct"] = round(mr_triggered / total * 100, 1)
        except Exception:
            hygiene.update({"pipeline_success_pct": 0, "pipeline_speed_secs": 0, "mr_trigger_pct": 0})

        # 2. Approval rules — required approvals count
        try:
            rules = self._paginated_fetch("approval_rules", limit=50)
            max_approvals = max((r.get("approvals_required", 0) for r in rules), default=0)
            hygiene["required_approvals"] = max_approvals
        except Exception:
            hygiene["required_approvals"] = 0

        # 3. Project settings — merge method, CI config, pipeline-must-succeed
        try:
            url = self._resolve_endpoint("project")
            project = self._get_json(url)
            hygiene["pipeline_must_succeed"] = project.get(
                "only_allow_merge_if_pipeline_succeeds", False)
            hygiene["discussions_must_resolve"] = project.get(
                "only_allow_merge_if_all_discussions_are_resolved", False)
            hygiene["has_ci_config"] = bool(project.get("ci_config_path") or
                                            project.get("ci_config_source"))

            merge_method = project.get("merge_method", "merge")
            if merge_method == "ff":
                hygiene["merge_method_score"] = 100
            elif merge_method == "rebase_merge":
                hygiene["merge_method_score"] = 80
            else:
                hygiene["merge_method_score"] = 40
        except Exception:
            hygiene.update({
                "pipeline_must_succeed": False,
                "discussions_must_resolve": False,
                "has_ci_config": False,
                "merge_method_score": 40,
            })

        # 4. Protected branches
        try:
            branches = self._paginated_fetch("protected_branches", limit=50)
            hygiene["has_protected_branches"] = len(branches) > 0
        except Exception:
            hygiene["has_protected_branches"] = False

        # 5. Vulnerability findings — security scan score
        try:
            vulns = self._paginated_fetch("vulnerability_findings", limit=200)
            if not vulns:
                hygiene["security_scan_score"] = 0  # No scanning configured
            else:
                open_critical = sum(
                    1 for v in vulns
                    if v.get("severity") == "critical" and v.get("state") in ("detected", "confirmed")
                )
                if open_critical == 0:
                    hygiene["security_scan_score"] = 100
                else:
                    hygiene["security_scan_score"] = 30
        except Exception:
            hygiene["security_scan_score"] = 0

        # 6. MR lead time (median hours from created_at to merged_at)
        try:
            mrs = self._paginated_fetch("merge_requests", limit=50,
                                        extra_params={"state": "merged", "order_by": "updated_at",
                                                      "sort": "desc"})
            lead_times: list[float] = []
            for mr in mrs:
                created = mr.get("created_at")
                merged = mr.get("merged_at")
                if created and merged:
                    secs = _duration_seconds(created, merged)
                    if secs and secs > 0:
                        lead_times.append(secs / 3600)
            if lead_times:
                lead_times.sort()
                hygiene["mr_lead_time_hours"] = round(lead_times[len(lead_times) // 2], 1)
            else:
                hygiene["mr_lead_time_hours"] = 0
        except Exception:
            hygiene["mr_lead_time_hours"] = 0

        # 7. DORA metric scores
        try:
            dora = self.fetch_native_dora_metrics()
            # Deployment frequency scoring (deploys per day)
            df_avg = (dora.get("deployment_frequency") or {}).get("average")
            if df_avg is not None:
                if df_avg >= 1.0:
                    hygiene["dora_deploy_freq_score"] = 100
                elif df_avg >= 0.14:  # ~weekly
                    hygiene["dora_deploy_freq_score"] = 80
                elif df_avg >= 0.033:  # ~monthly
                    hygiene["dora_deploy_freq_score"] = 60
                else:
                    hygiene["dora_deploy_freq_score"] = 30
            else:
                hygiene["dora_deploy_freq_score"] = 0

            # Lead time scoring (seconds to hours)
            lt_avg = (dora.get("lead_time_for_changes") or {}).get("average")
            if lt_avg is not None:
                lt_hours = lt_avg / 3600 if lt_avg > 100 else lt_avg  # API may return seconds or hours
                if lt_hours < 1:
                    hygiene["dora_lead_time_score"] = 100
                elif lt_hours < 24:
                    hygiene["dora_lead_time_score"] = 80
                elif lt_hours < 168:
                    hygiene["dora_lead_time_score"] = 60
                else:
                    hygiene["dora_lead_time_score"] = 30
            else:
                hygiene["dora_lead_time_score"] = 0

            # Change failure rate scoring (percentage)
            cfr_avg = (dora.get("change_failure_rate") or {}).get("average")
            if cfr_avg is not None:
                cfr_pct = cfr_avg * 100 if cfr_avg <= 1 else cfr_avg
                if cfr_pct < 5:
                    hygiene["dora_cfr_score"] = 100
                elif cfr_pct < 10:
                    hygiene["dora_cfr_score"] = 80
                elif cfr_pct < 15:
                    hygiene["dora_cfr_score"] = 60
                elif cfr_pct < 30:
                    hygiene["dora_cfr_score"] = 40
                else:
                    hygiene["dora_cfr_score"] = 20
            else:
                hygiene["dora_cfr_score"] = 0

            # Time to restore scoring (seconds to hours)
            ttr_avg = (dora.get("time_to_restore_service") or {}).get("average")
            if ttr_avg is not None:
                ttr_hours = ttr_avg / 3600 if ttr_avg > 100 else ttr_avg
                if ttr_hours < 1:
                    hygiene["dora_mttr_score"] = 100
                elif ttr_hours < 24:
                    hygiene["dora_mttr_score"] = 80
                elif ttr_hours < 168:
                    hygiene["dora_mttr_score"] = 50
                else:
                    hygiene["dora_mttr_score"] = 20
            else:
                hygiene["dora_mttr_score"] = 0
        except Exception:
            hygiene.update({
                "dora_deploy_freq_score": 0,
                "dora_lead_time_score": 0,
                "dora_cfr_score": 0,
                "dora_mttr_score": 0,
            })

        return hygiene

    # ── Normalization ─────────────────────────────────────────────

    def normalize(self, records: list[dict]) -> pd.DataFrame:
        """Normalize GitLab records to a flat DataFrame."""
        if not records:
            return pd.DataFrame()

        rows: list[dict] = []
        for r in records:
            # DORA composite record
            if r.get("source") == "gitlab_native_dora":
                rows.append(self._normalize_dora(r))
            # Pipeline record
            elif "pipeline_id" in r or ("status" in r and "duration" in r and "ref" in r):
                rows.append(self._normalize_pipeline(r))
            # Merge request record
            elif "source_branch" in r:
                rows.append(self._normalize_mr(r))
            # Vulnerability record
            elif "report_type" in r or "vulnerability_id" in r:
                rows.append(self._normalize_vulnerability(r))
            else:
                # Best-effort fallback for pipeline-like records
                rows.append(self._normalize_pipeline(r))

        return pd.DataFrame(rows)

    def _normalize_pipeline(self, r: dict) -> dict:
        return {
            "run_id": str(r.get("id", "")),
            "pipeline_name": r.get("ref", ""),
            "status": r.get("status", ""),
            "run_date": _parse_date(r.get("created_at")),
            "duration_seconds": r.get("duration", 0),
            "trigger_type": r.get("source", ""),
            "coverage": r.get("coverage"),
            "source_system": "gitlab",
        }

    def _normalize_mr(self, r: dict) -> dict:
        return {
            "pr_id": str(r.get("iid", "")),
            "title": r.get("title", ""),
            "status": r.get("state", ""),
            "event_date": _parse_date(r.get("created_at")),
            "merged_date": _parse_date(r.get("merged_at")),
            "author": r.get("author", {}).get("username", r.get("author_username", "")),
            "source_branch": r.get("source_branch", ""),
            "target_branch": r.get("target_branch", ""),
            "source_system": "gitlab",
        }

    def _normalize_vulnerability(self, r: dict) -> dict:
        return {
            "vuln_id": str(r.get("id", "")),
            "name": r.get("name", r.get("title", "")),
            "severity": r.get("severity", ""),
            "state": r.get("state", ""),
            "report_type": r.get("report_type", ""),
            "source_system": "gitlab",
        }

    def _normalize_dora(self, r: dict) -> dict:
        return {
            "source": "gitlab_native_dora",
            "project_id": r.get("project_id", self.project_id),
            "start_date": r.get("start_date"),
            "end_date": r.get("end_date"),
            "deployment_frequency": (r.get("deployment_frequency") or {}).get("average"),
            "lead_time_for_changes": (r.get("lead_time_for_changes") or {}).get("average"),
            "time_to_restore_service": (r.get("time_to_restore_service") or {}).get("average"),
            "change_failure_rate": (r.get("change_failure_rate") or {}).get("average"),
            "source_system": "gitlab",
        }

    # ── Mock data generators ──────────────────────────────────────

    def _mock_fetch(self, data_type: str, limit: int) -> list[dict]:
        """Return realistic mock GitLab records for wizard preview / tests."""
        if data_type == "pipelines":
            return self._mock_pipelines(limit)
        elif data_type == "merge_requests":
            return self._mock_merge_requests(limit)
        elif data_type == "dora_metrics":
            return [self._mock_dora_metrics()]
        elif data_type == "vulnerabilities":
            return self._mock_vulnerabilities(limit)
        return []

    def _mock_pipelines(self, limit: int) -> list[dict]:
        records: list[dict] = []
        for i in range(min(limit, 25)):
            status = random.choice(["success", "failed", "success", "success", "canceled"])
            records.append({
                "id": 4000 + i,
                "iid": 100 + i,
                "ref": random.choice(["main", "develop", "feature/x", "release/v2"]),
                "status": status,
                "source": random.choice(["push", "merge_request_event", "schedule", "web"]),
                "created_at": f"2026-03-{27 - i % 28:02d}T08:00:00Z",
                "updated_at": f"2026-03-{27 - i % 28:02d}T08:{random.randint(3, 20):02d}:00Z",
                "duration": random.randint(60, 900),
                "queued_duration": random.randint(5, 60),
                "coverage": round(random.uniform(60, 95), 1) if status == "success" else None,
                "tag": False,
                "yaml_errors": None,
                "web_url": f"https://gitlab.com/my-group/my-project/-/pipelines/{4000 + i}",
            })
        return records

    def _mock_merge_requests(self, limit: int) -> list[dict]:
        records: list[dict] = []
        for i in range(min(limit, 25)):
            state = random.choice(["merged", "opened", "closed", "merged", "merged"])
            day = 27 - i % 28
            records.append({
                "id": 8000 + i,
                "iid": 300 + i,
                "title": f"feat: GL feature {i}",
                "state": state,
                "author": {"username": f"dev{i % 4}", "id": 100 + i % 4},
                "author_username": f"dev{i % 4}",
                "created_at": f"2026-03-{day:02d}T09:00:00Z",
                "merged_at": f"2026-03-{day:02d}T14:00:00Z" if state == "merged" else None,
                "closed_at": f"2026-03-{day:02d}T15:00:00Z" if state in ("merged", "closed") else None,
                "source_branch": f"feature/gl-{i}",
                "target_branch": "main",
                "user_notes_count": random.randint(0, 12),
                "upvotes": random.randint(0, 5),
                "downvotes": random.randint(0, 1),
                "reviewers": [{"username": f"reviewer{j}"} for j in range(random.randint(0, 3))],
                "draft": random.random() < 0.1,
                "work_in_progress": False,
                "web_url": f"https://gitlab.com/my-group/my-project/-/merge_requests/{300 + i}",
            })
        return records

    def _mock_vulnerabilities(self, limit: int) -> list[dict]:
        records: list[dict] = []
        for i in range(min(limit, 15)):
            records.append({
                "id": 6000 + i,
                "report_type": random.choice(["sast", "dependency_scanning", "secret_detection",
                                               "container_scanning", "dast"]),
                "severity": random.choice(["critical", "high", "medium", "low", "info"]),
                "state": random.choice(["detected", "confirmed", "resolved", "dismissed"]),
                "name": f"Vulnerability {i}: {random.choice(['SQL Injection', 'XSS', 'Insecure Dependency', 'Hardcoded Secret', 'Path Traversal'])}",
                "confidence": random.choice(["high", "medium", "low"]),
                "scanner": {"name": random.choice(["semgrep", "gemnasium", "trivy"])},
                "identifiers": [{"type": "cve", "name": f"CVE-2026-{1000 + i}"}],
                "location": {"file": f"src/module_{i % 5}.py", "start_line": random.randint(10, 200)},
                "created_at": f"2026-03-{27 - i % 28:02d}T12:00:00Z",
            })
        return records

    def _mock_dora_metrics(self) -> dict:
        """Generate realistic mock DORA metric data."""
        today = datetime(2026, 3, 27)
        start = today - timedelta(days=90)

        def _daily_points(base_value: float, jitter: float = 0.2) -> list[dict]:
            points = []
            for d in range(90):
                date = (start + timedelta(days=d)).strftime("%Y-%m-%d")
                val = max(0, base_value + random.uniform(-jitter * base_value,
                                                          jitter * base_value))
                points.append({"date": date, "value": round(val, 4)})
            return points

        df_points = _daily_points(0.85, 0.4)   # ~0.85 deploys/day
        lt_points = _daily_points(14400, 0.5)   # ~4 hours in seconds
        ttr_points = _daily_points(7200, 0.6)   # ~2 hours in seconds
        cfr_points = _daily_points(0.08, 0.5)   # ~8% failure rate

        def _summarise(points: list[dict]) -> dict:
            values = [p["value"] for p in points if p.get("value") is not None]
            return {
                "data_points": points,
                "count": len(values),
                "average": round(sum(values) / len(values), 4) if values else None,
            }

        return {
            "source": "gitlab_native_dora",
            "project_id": self.project_id or "mock-project",
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "deployment_frequency": _summarise(df_points),
            "lead_time_for_changes": _summarise(lt_points),
            "time_to_restore_service": _summarise(ttr_points),
            "change_failure_rate": _summarise(cfr_points),
        }

    def _mock_repo_hygiene(self) -> dict:
        """Return mock hygiene data matching all 15 keys gitlab_hygiene.py expects."""
        return {
            "pipeline_success_pct": random.randint(70, 95),
            "pipeline_speed_secs": random.choice([240, 360, 540, 720, 900]),
            "mr_trigger_pct": random.randint(50, 85),
            "required_approvals": random.choice([0, 1, 2, 2]),
            "pipeline_must_succeed": random.choice([True, True, False]),
            "discussions_must_resolve": random.choice([True, False]),
            "dora_deploy_freq_score": random.choice([30, 60, 80, 100]),
            "dora_lead_time_score": random.choice([30, 60, 80, 100]),
            "dora_cfr_score": random.choice([20, 40, 60, 80, 100]),
            "has_protected_branches": random.choice([True, True, True, False]),
            "security_scan_score": random.choice([0, 30, 70, 100]),
            "has_ci_config": random.choice([True, True, False]),
            "mr_lead_time_hours": round(random.uniform(4, 72), 1),
            "merge_method_score": random.choice([40, 80, 100]),
            "dora_mttr_score": random.choice([20, 50, 80, 100]),
        }
