"""GitHub REST API connector.
# ****Truth Agent Verified**** — 15 endpoint types. Bearer token auth.
# BaseConnector subclass. Mock fetch implemented.
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

    ENDPOINTS = {
        "workflows":             "/repos/{owner}/{repo}/actions/runs",
        "pull_requests":         "/repos/{owner}/{repo}/pulls",
        "issues":                "/repos/{owner}/{repo}/issues",
        "deployments":           "/repos/{owner}/{repo}/deployments",
        "branch_protection":     "/repos/{owner}/{repo}/branches/{branch}/protection",
        "code_scanning":         "/repos/{owner}/{repo}/code-scanning/alerts",
        "secret_scanning":       "/repos/{owner}/{repo}/secret-scanning/alerts",
        "dependabot":            "/repos/{owner}/{repo}/dependabot/alerts",
        "environments":          "/repos/{owner}/{repo}/environments",
        "workflow_files":        "/repos/{owner}/{repo}/actions/workflows",
        "commits":               "/repos/{owner}/{repo}/commits",
        "pr_reviews":            "/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
        "codeowners":            "/repos/{owner}/{repo}/contents/CODEOWNERS",
        "stats_commit_activity": "/repos/{owner}/{repo}/stats/commit_activity",
        "stats_contributors":    "/repos/{owner}/{repo}/stats/contributors",
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
            {"value": "workflows",       "label": "Workflow Runs",    "suggested_slot": "pipeline_runs"},
            {"value": "pull_requests",    "label": "Pull Requests",   "suggested_slot": "pull_requests"},
            {"value": "issues",           "label": "Issues",          "suggested_slot": "work_items"},
            {"value": "deployments",      "label": "Deployments",     "suggested_slot": "deployment_events"},
            {"value": "repo_hygiene",     "label": "Repo Hygiene",    "suggested_slot": "hygiene_metrics"},
            {"value": "security_alerts",  "label": "Security Alerts", "suggested_slot": "security_events"},
            {"value": "repo_stats",       "label": "Repo Stats",      "suggested_slot": "repo_statistics"},
        ]

    # ── Authentication ────────────────────────────────────────────

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

    # ── Safe HTTP helpers ─────────────────────────────────────────

    def _safe_get(self, endpoint: str, **kwargs) -> Optional[dict]:
        """GET a single JSON object; return None on 404/403 instead of raising."""
        if not self._session:
            return None
        try:
            resp = self._session.get(f"{self.BASE_URL}{endpoint}", timeout=30, **kwargs)
            if resp.status_code in (403, 404):
                return None
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def _safe_get_list(self, endpoint: str, **kwargs) -> list[dict]:
        """GET a JSON list; return [] on 404/403 instead of raising."""
        if not self._session:
            return []
        try:
            resp = self._session.get(f"{self.BASE_URL}{endpoint}", timeout=30, **kwargs)
            if resp.status_code in (403, 404):
                return []
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return data
            for key in ("items", "alerts", "workflow_runs", "environments", "workflows"):
                if key in data:
                    return data[key]
            return []
        except Exception:
            return []

    # ── Core fetch ────────────────────────────────────────────────

    def fetch_records(self, data_type: str = "workflows", limit: int = 100, **kwargs) -> list[dict]:
        """Fetch records from GitHub API."""
        if USE_MOCK:
            return self._mock_fetch(data_type, limit)
        if not self._authenticated:
            self.authenticate()
        if data_type == "repo_hygiene":
            return [self.fetch_repo_hygiene(**kwargs)]
        if data_type == "security_alerts":
            return self._fetch_security_alerts(limit)
        if data_type == "repo_stats":
            return [self.fetch_repo_stats()]

        endpoint_template = self.ENDPOINTS.get(data_type, self.ENDPOINTS["workflows"])
        endpoint = endpoint_template.format(owner=self.owner, repo=self.repo)
        url = f"{self.BASE_URL}{endpoint}"
        params = {"per_page": min(limit, 100), "state": "all"}

        all_records: list[dict] = []
        page = 1
        while len(all_records) < limit:
            params["page"] = page
            resp = self._session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
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

    def _fetch_security_alerts(self, limit: int = 100) -> list[dict]:
        """Aggregate code-scanning, secret-scanning, and dependabot alerts."""
        alerts: list[dict] = []
        for key in ("code_scanning", "secret_scanning", "dependabot"):
            ep = self.ENDPOINTS[key].format(owner=self.owner, repo=self.repo)
            items = self._safe_get_list(ep, params={"per_page": min(limit, 100)})
            for item in items:
                item["_alert_source"] = key
            alerts.extend(items)
        return alerts[:limit]

    # ── Repo hygiene composite ────────────────────────────────────

    def fetch_repo_hygiene(self, branch: str = "main", **kwargs) -> dict:
        """Call 8+ endpoints and assemble a flat hygiene metrics dict with 22 keys."""
        if USE_MOCK:
            return self._mock_repo_hygiene()
        if not self._authenticated:
            self.authenticate()

        # 1. Branch protection
        bp_ep = self.ENDPOINTS["branch_protection"].format(
            owner=self.owner, repo=self.repo, branch=branch)
        bp = self._safe_get(bp_ep)
        has_protection = bp is not None
        required_reviewers = 0
        status_checks_required = False
        if bp:
            pr_rules = bp.get("required_pull_request_reviews") or {}
            required_reviewers = pr_rules.get("required_approving_review_count", 0)
            status_checks_required = bp.get("required_status_checks") is not None

        # 2. Secret scanning
        secrets_ep = self.ENDPOINTS["secret_scanning"].format(owner=self.owner, repo=self.repo)
        open_secrets = len(self._safe_get_list(secrets_ep, params={"state": "open", "per_page": 100}))

        # 3. Code scanning
        code_ep = self.ENDPOINTS["code_scanning"].format(owner=self.owner, repo=self.repo)
        code_alerts = self._safe_get_list(code_ep, params={"state": "open", "per_page": 100})
        critical_vulns = sum(1 for a in code_alerts if a.get("rule", {}).get("severity") == "critical")
        code_scanning_score = max(0, 100 - len(code_alerts) * 5)

        # 4. Dependabot
        dep_ep = self.ENDPOINTS["dependabot"].format(owner=self.owner, repo=self.repo)
        dep_alerts = self._safe_get_list(dep_ep, params={"state": "open", "per_page": 100})
        dependabot_score = max(0, 100 - len(dep_alerts) * 3)

        # 5. Environments
        env_ep = self.ENDPOINTS["environments"].format(owner=self.owner, repo=self.repo)
        env_data = self._safe_get(env_ep)
        environment_count = len(env_data.get("environments", [])) if env_data else 0

        # 6. Workflow files / CI analysis
        wf_ep = self.ENDPOINTS["workflow_files"].format(owner=self.owner, repo=self.repo)
        wf_list = self._safe_get_list(wf_ep)
        has_ci_yaml = len(wf_list) > 0
        test_wf = security_wf = 0
        for wf in wf_list:
            combined = f"{(wf.get('path') or '')} {(wf.get('name') or '')}".lower()
            if any(t in combined for t in ("test", "ci", "build", "check")):
                test_wf += 1
            if any(s in combined for s in ("security", "codeql", "scan", "sast")):
                security_wf += 1
        total_wf = max(len(wf_list), 1)
        test_workflow_pct = round(test_wf / total_wf * 100, 1)
        security_workflow_pct = round(security_wf / total_wf * 100, 1)

        # 7. Recent workflow runs — trigger + success analysis
        runs_ep = self.ENDPOINTS["workflows"].format(owner=self.owner, repo=self.repo)
        runs = self._safe_get_list(runs_ep, params={"per_page": 100})
        if not runs:
            raw = self._safe_get(runs_ep, params={"per_page": 100})
            runs = (raw or {}).get("workflow_runs", []) if isinstance(raw, dict) else []
        ci_triggered = sum(1 for r in runs if r.get("event") in ("push", "pull_request"))
        successes = sum(1 for r in runs if r.get("conclusion") == "success")
        total_runs = max(len(runs), 1)
        ci_trigger_pct = round(ci_triggered / total_runs * 100, 1)
        build_success_pct = round(successes / total_runs * 100, 1)
        durations = [d for d in (
            _duration_seconds(r.get("created_at"), r.get("updated_at"))
            for r in runs if r.get("conclusion") == "success"
        ) if d and d > 0]
        build_speed_secs = round(sum(durations) / max(len(durations), 1), 1) if durations else 0

        # 8. Commits — weekly frequency
        commits_ep = self.ENDPOINTS["stats_commit_activity"].format(owner=self.owner, repo=self.repo)
        commit_activity = self._safe_get_list(commits_ep)
        if commit_activity:
            recent_weeks = commit_activity[-4:] if len(commit_activity) >= 4 else commit_activity
            commits_per_week = round(
                sum(w.get("total", 0) for w in recent_weeks) / max(len(recent_weeks), 1), 1)
        else:
            commits_per_week = 0

        # 9. Pull requests — lead time, merge frequency, review pct, PR size
        pr_ep = self.ENDPOINTS["pull_requests"].format(owner=self.owner, repo=self.repo)
        prs = self._safe_get_list(pr_ep, params={"state": "all", "per_page": 50})
        lead_times: list[float] = []
        merged_count = reviewed_count = 0
        pr_sizes: list[int] = []
        review_comment_counts: list[int] = []
        for pr in prs:
            if pr.get("merged_at") and pr.get("created_at"):
                merged_count += 1
                lt = _duration_seconds(pr.get("created_at"), pr.get("merged_at"))
                if lt and lt > 0:
                    lead_times.append(lt / 3600)
            if pr.get("requested_reviewers") or pr.get("review_comments", 0) > 0:
                reviewed_count += 1
            adds = pr.get("additions", 0)
            dels = pr.get("deletions", 0)
            if adds or dels:
                pr_sizes.append(adds + dels)
            review_comment_counts.append(pr.get("review_comments", 0))

        pr_lead_time_hours = round(sum(lead_times) / max(len(lead_times), 1), 1) if lead_times else 0
        pr_merge_per_week = round(merged_count / 4, 1)
        pr_review_pct = round(reviewed_count / max(len(prs), 1) * 100, 1) if prs else 0
        median_pr_size = sorted(pr_sizes)[len(pr_sizes) // 2] if pr_sizes else 0
        avg_review_comments = (round(sum(review_comment_counts) / max(len(review_comment_counts), 1), 1)
                               if review_comment_counts else 0)

        # 10. Deployments — weekly frequency + tracking
        dep_list_ep = self.ENDPOINTS["deployments"].format(owner=self.owner, repo=self.repo)
        deps = self._safe_get_list(dep_list_ep, params={"per_page": 100})
        deploys_per_week = round(len(deps) / 4, 1) if deps else 0
        tracked = sum(1 for d in deps if d.get("environment"))
        deploy_tracking_pct = round(tracked / max(len(deps), 1) * 100, 1) if deps else 0

        return {
            "ci_trigger_pct": ci_trigger_pct, "build_success_pct": build_success_pct,
            "build_speed_secs": build_speed_secs, "branch_protection": has_protection,
            "open_secrets": open_secrets, "required_reviewers": required_reviewers,
            "test_workflow_pct": test_workflow_pct, "security_workflow_pct": security_workflow_pct,
            "environment_count": environment_count, "has_ci_yaml": has_ci_yaml,
            "commits_per_week": commits_per_week, "deploys_per_week": deploys_per_week,
            "pr_lead_time_hours": pr_lead_time_hours, "pr_merge_per_week": pr_merge_per_week,
            "code_scanning_score": code_scanning_score, "dependabot_score": dependabot_score,
            "critical_vulns": critical_vulns, "median_pr_size": median_pr_size,
            "avg_review_comments": avg_review_comments, "status_checks_required": status_checks_required,
            "deploy_tracking_pct": deploy_tracking_pct, "pr_review_pct": pr_review_pct,
        }

    # ── Workflow YAML parsing ─────────────────────────────────────

    def _parse_workflow_yaml(self, yaml_content: str) -> dict:
        """Detect CI step categories from a workflow YAML string."""
        lower = yaml_content.lower()
        test_patterns = [
            "pytest", "jest", "npm test", "npm run test", "go test",
            "cargo test", "dotnet test", "mvn test", "gradle test",
            "phpunit", "rspec", "unittest", "nox", "tox", "vitest", "mocha",
        ]
        security_patterns = [
            "codeql", "trivy", "snyk", "gitleaks", "checkov", "tfsec",
            "grype", "anchore", "semgrep", "sast", "dependency-check",
            "bandit", "sonarqube", "sonar-scanner",
        ]
        lint_patterns = [
            "eslint", "pylint", "flake8", "black", "prettier", "rubocop",
            "golangci-lint", "shellcheck", "yamllint", "hadolint", "mypy",
            "ruff", "clippy",
        ]
        deploy_patterns = [
            "deploy", "aws-actions", "azure/", "google-github-actions",
            "environment:", "kubectl apply", "helm upgrade", "terraform apply",
        ]
        return {
            "has_test_step":     any(p in lower for p in test_patterns),
            "has_security_step": any(p in lower for p in security_patterns),
            "has_lint_step":     any(p in lower for p in lint_patterns),
            "has_deploy_step":   any(p in lower for p in deploy_patterns),
        }

    # ── PR details batch ──────────────────────────────────────────

    def fetch_pr_details_batch(self, pr_numbers: list[int]) -> list[dict]:
        """Fetch detailed PR data (including reviews) for a batch of PR numbers."""
        if USE_MOCK:
            return self._mock_pr_details_batch(pr_numbers)
        if not self._authenticated:
            self.authenticate()
        results: list[dict] = []
        for pr_num in pr_numbers:
            pr_data = self._safe_get(f"/repos/{self.owner}/{self.repo}/pulls/{pr_num}")
            if not pr_data:
                continue
            review_ep = self.ENDPOINTS["pr_reviews"].format(
                owner=self.owner, repo=self.repo, pr_number=pr_num)
            reviews = self._safe_get_list(review_ep)
            results.append({**pr_data, "_reviews": reviews, "_review_count": len(reviews)})
        return results

    # ── Repo stats ────────────────────────────────────────────────

    def fetch_repo_stats(self) -> dict:
        """Call statistics endpoints and return a summary dict."""
        if USE_MOCK:
            return self._mock_repo_stats()
        if not self._authenticated:
            self.authenticate()
        commit_ep = self.ENDPOINTS["stats_commit_activity"].format(owner=self.owner, repo=self.repo)
        contrib_ep = self.ENDPOINTS["stats_contributors"].format(owner=self.owner, repo=self.repo)
        commit_activity = self._safe_get_list(commit_ep)
        contributors = self._safe_get_list(contrib_ep)

        total_commits_52w = sum(w.get("total", 0) for w in commit_activity) if commit_activity else 0
        recent_4w = commit_activity[-4:] if commit_activity and len(commit_activity) >= 4 else commit_activity
        avg_commits_per_week = (round(sum(w.get("total", 0) for w in recent_4w)
                                / max(len(recent_4w), 1), 1) if recent_4w else 0)
        active_contributors = 0
        for c in contributors:
            weeks = c.get("weeks", [])
            recent = weeks[-4:] if len(weeks) >= 4 else weeks
            if any(w.get("c", 0) > 0 for w in recent):
                active_contributors += 1
        return {
            "total_commits_52_weeks": total_commits_52w,
            "avg_commits_per_week": avg_commits_per_week,
            "total_contributors": len(contributors),
            "active_contributors_4w": active_contributors,
            "weeks_of_data": len(commit_activity) if commit_activity else 0,
        }

    # ── Normalization ─────────────────────────────────────────────

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
            elif "ci_trigger_pct" in r:
                rows.append(r)  # repo_hygiene — already flat
            elif "total_commits_52_weeks" in r:
                rows.append(r)  # repo_stats — already flat
            elif "_alert_source" in r:
                rows.append(self._normalize_alert(r))
            else:
                rows.append(self._normalize_pr(r) if "pull_request" in r else self._normalize_issue(r))
        return pd.DataFrame(rows)

    def _normalize_workflow(self, r: dict) -> dict:
        return {
            "run_id": str(r.get("id", "")),
            "pipeline_name": r.get("name", ""),
            "status": r.get("conclusion", r.get("status", "")),
            "run_date": _parse_date(r.get("created_at")),
            "duration_seconds": _duration_seconds(r.get("created_at"), r.get("updated_at")),
            "trigger_type": r.get("event", ""),
            "branch": r.get("head_branch", ""),
            "commit_sha": r.get("head_sha", ""),
            "is_pr_triggered": r.get("event") == "pull_request",
            "source_system": "github",
        }

    def _normalize_pr(self, r: dict) -> dict:
        lead_time = None
        if r.get("merged_at") and r.get("created_at"):
            lt_secs = _duration_seconds(r.get("created_at"), r.get("merged_at"))
            lead_time = round(lt_secs / 3600, 2) if lt_secs else None
        head = r.get("head") or {}
        base = r.get("base") or {}
        return {
            "pr_id": str(r.get("number", r.get("id", ""))),
            "title": r.get("title", ""),
            "status": "merged" if r.get("merged_at") else r.get("state", ""),
            "event_date": _parse_date(r.get("created_at")),
            "author": r.get("user", {}).get("login", ""),
            "repo_name": head.get("repo", {}).get("name", self.repo) if head.get("repo") else self.repo,
            "reviewers_count": len(r.get("requested_reviewers", [])),
            "lead_time_hours": lead_time,
            "additions": r.get("additions", 0),
            "deletions": r.get("deletions", 0),
            "changed_files": r.get("changed_files", 0),
            "review_comments": r.get("review_comments", 0),
            "is_draft": r.get("draft", False),
            "target_branch": base.get("ref", ""),
            "source_branch": head.get("ref", ""),
            "source_system": "github",
        }

    def _normalize_issue(self, r: dict) -> dict:
        return {
            "item_id": str(r.get("number", r.get("id", ""))),
            "title": r.get("title", ""),
            "item_type": "issue",
            "status": r.get("state", ""),
            "event_date": _parse_date(r.get("created_at")),
            "priority": ",".join(lbl.get("name", "") for lbl in r.get("labels", [])),
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

    def _normalize_alert(self, r: dict) -> dict:
        rule = r.get("rule") or r.get("security_advisory") or {}
        return {
            "alert_id": str(r.get("number", r.get("id", ""))),
            "alert_source": r.get("_alert_source", "unknown"),
            "state": r.get("state", ""),
            "severity": rule.get("severity", r.get("severity", "")),
            "summary": rule.get("description", r.get("summary", "")),
            "created_at": _parse_date(r.get("created_at")),
            "source_system": "github",
        }

    # ── Mock data ─────────────────────────────────────────────────

    def _mock_fetch(self, data_type: str, limit: int) -> list[dict]:
        """Return mock GitHub records for wizard preview."""
        import random
        records: list[dict] = []

        if data_type == "workflows":
            for i in range(min(limit, 25)):
                records.append({
                    "id": 2000 + i,
                    "name": random.choice(["CI Build", "Deploy", "Tests", "Lint"]),
                    "status": "completed",
                    "conclusion": random.choice(["success", "failure", "success", "success"]),
                    "created_at": f"2026-03-{27 - i % 28:02d}T08:00:00Z",
                    "updated_at": f"2026-03-{27 - i % 28:02d}T08:{random.randint(2, 20):02d}:00Z",
                    "run_number": 100 + i, "workflow_id": 10,
                    "head_branch": random.choice(["main", "develop", "feature/x"]),
                    "head_sha": f"abc{i:04d}",
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
                    "head": {"ref": f"feature/ticket-{100 + i}",
                             "repo": {"name": random.choice(["api-service", "frontend"])}},
                    "base": {"ref": "main"},
                    "requested_reviewers": [{"login": "reviewer"}] * random.randint(0, 3),
                    "commits_url": "...",
                    "additions": random.randint(5, 500),
                    "deletions": random.randint(1, 200),
                    "changed_files": random.randint(1, 30),
                    "review_comments": random.randint(0, 8),
                    "draft": random.choice([False, False, False, True]),
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
                    "id": 3000 + i, "ref": "main",
                    "environment": random.choice(["production", "staging", "development"]),
                    "created_at": f"2026-03-{27 - i % 28:02d}T14:00:00Z",
                    "updated_at": f"2026-03-{27 - i % 28:02d}T14:05:00Z",
                    "creator": {"login": f"deployer{i % 3}"},
                    "description": f"Deploy #{i + 1}", "task": "deploy",
                })
        elif data_type == "repo_hygiene":
            records.append(self._mock_repo_hygiene())
        elif data_type == "security_alerts":
            records.extend(self._mock_security_alerts(limit))
        elif data_type == "repo_stats":
            records.append(self._mock_repo_stats())
        return records

    def _mock_repo_hygiene(self) -> dict:
        """Return realistic mock repo-hygiene metrics."""
        import random
        return {
            "ci_trigger_pct": round(random.uniform(70, 98), 1),
            "build_success_pct": round(random.uniform(78, 96), 1),
            "build_speed_secs": round(random.uniform(120, 600), 1),
            "branch_protection": True,
            "open_secrets": random.randint(0, 3),
            "required_reviewers": random.choice([1, 2, 2]),
            "test_workflow_pct": round(random.uniform(50, 100), 1),
            "security_workflow_pct": round(random.uniform(20, 80), 1),
            "environment_count": random.choice([2, 3, 4]),
            "has_ci_yaml": True,
            "commits_per_week": round(random.uniform(10, 45), 1),
            "deploys_per_week": round(random.uniform(2, 12), 1),
            "pr_lead_time_hours": round(random.uniform(4, 36), 1),
            "pr_merge_per_week": round(random.uniform(5, 20), 1),
            "code_scanning_score": random.choice([80, 85, 90, 95, 100]),
            "dependabot_score": random.choice([75, 80, 85, 90, 95, 100]),
            "critical_vulns": random.randint(0, 2),
            "median_pr_size": random.randint(50, 350),
            "avg_review_comments": round(random.uniform(1.0, 5.0), 1),
            "status_checks_required": True,
            "deploy_tracking_pct": round(random.uniform(60, 100), 1),
            "pr_review_pct": round(random.uniform(65, 98), 1),
        }

    def _mock_security_alerts(self, limit: int) -> list[dict]:
        """Return mock security alerts across scanners."""
        import random
        srcs = ["code_scanning", "secret_scanning", "dependabot"]
        sevs = ["critical", "high", "medium", "low"]
        return [{
            "number": 500 + i, "state": random.choice(["open", "open", "fixed", "dismissed"]),
            "_alert_source": (s := random.choice(srcs)),
            "rule": {"severity": random.choice(sevs), "description": f"Mock {s} finding #{i+1}"},
            "created_at": f"2026-03-{27 - i % 28:02d}T12:00:00Z",
        } for i in range(min(limit, 15))]

    def _mock_repo_stats(self) -> dict:
        """Return mock repository statistics."""
        import random
        return {
            "total_commits_52_weeks": random.randint(400, 1200),
            "avg_commits_per_week": round(random.uniform(10, 40), 1),
            "total_contributors": random.randint(5, 25),
            "active_contributors_4w": random.randint(3, 12),
            "weeks_of_data": 52,
        }

    def _mock_pr_details_batch(self, pr_numbers: list[int]) -> list[dict]:
        """Return mock enriched PR data for a batch of PR numbers."""
        import random
        return [{
            "number": n, "title": f"feat: batch PR #{n}",
            "state": "closed" if (m := random.choice([True, True, False])) else "open",
            "created_at": "2026-03-20T09:00:00Z",
            "merged_at": "2026-03-20T16:00:00Z" if m else None,
            "user": {"login": f"dev{n % 5}"},
            "head": {"ref": f"feature/pr-{n}", "repo": {"name": "api-service"}},
            "base": {"ref": "main"}, "requested_reviewers": [{"login": "reviewer1"}],
            "commits_url": "...", "additions": random.randint(10, 400),
            "deletions": random.randint(5, 150), "changed_files": random.randint(1, 20),
            "review_comments": random.randint(0, 6), "draft": False,
            "_reviews": [{"user": {"login": "reviewer1"}, "state": "APPROVED"}],
            "_review_count": 1,
        } for n in pr_numbers]


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
