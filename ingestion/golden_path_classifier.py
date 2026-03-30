"""Golden Path Deployment Classification Engine.

Classifies deployment events as standard (golden-path) or non-standard
based on multiple signals: service principal identity, golden_path_token
presence, known CI runner IPs, and git-backed source detection.
"""

import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Databricks API actions that constitute deployment events
DEPLOYMENT_ACTIONS = frozenset({
    "createJob", "resetJob", "updateJob", "deleteJob",
    "import", "createNotebook", "updateNotebook",
    "createPipeline", "updatePipeline", "editPipeline",
    "createRepo", "updateRepo", "pull",
    "putSecretScope", "putSecret",
    "createCluster", "editCluster",
    "setPermissions", "updatePermissions",
})

# Patterns identifying service principals
SP_PATTERNS = [
    re.compile(r".*@.*\.iam\.databricks\.com"),
    re.compile(r".*@.*\.gcp\.databricks\.com"),
    re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
]

# Action → artifact type mapping
ARTIFACT_TYPE_MAP = {
    "createJob": "job", "resetJob": "job", "updateJob": "job", "deleteJob": "job",
    "import": "notebook", "createNotebook": "notebook", "updateNotebook": "notebook",
    "createPipeline": "pipeline", "updatePipeline": "pipeline", "editPipeline": "pipeline",
    "createRepo": "repo", "updateRepo": "repo", "pull": "repo",
    "putSecretScope": "secret", "putSecret": "secret",
    "createCluster": "cluster", "editCluster": "cluster",
    "setPermissions": "permission", "updatePermissions": "permission",
}


class GoldenPathClassifier:
    """Classifies deployment events as standard (golden path) or non-standard."""

    def __init__(self, known_ci_ips: list[str] = None, team_registry: dict = None):
        self.known_ci_ips = set(known_ci_ips or [])
        self.team_registry = team_registry or {}

    def classify(self, event: dict) -> dict:
        """
        Classify a single deployment event.

        Args:
            event: Dict with keys matching Databricks audit log schema:
                - user_identity.email (or actor_email)
                - action_name
                - source_ip_address
                - request_params (dict or JSON string)
                - is_golden_path (optional pre-classification flag)

        Returns:
            {
                "classification": "standard" | "non_standard" | "unknown",
                "confidence": float (0-1),
                "signals": list[str],
                "artifact_type": str,
                "team_id": str | None,
                "actor_email": str,
                "action_name": str,
                "timestamp": str,
            }
        """
        signals = []

        # Extract actor email
        actor = self._extract_actor(event)
        action = event.get("action_name", "")

        # Signal 0: Pre-classified is_golden_path flag (from data source)
        pre_flag = event.get("is_golden_path")
        has_pre_flag = pre_flag is not None and str(pre_flag).lower() not in ("", "nan", "none")
        if has_pre_flag and str(pre_flag).lower() in ("true", "1", "yes"):
            signals.append("pre_classified_golden_path")

        # Signal 1: Service principal actor
        is_sp = self._is_service_principal(actor)
        if is_sp:
            signals.append("service_principal_actor")

        # Signal 2: Golden path token in metadata
        has_token = self._has_golden_path_token(event)
        if has_token:
            signals.append("golden_path_token_present")

        # Signal 3: Known CI runner IP
        source_ip = event.get("source_ip_address", "")
        is_known_ci = source_ip in self.known_ci_ips
        if is_known_ci:
            signals.append("known_ci_runner_ip")

        # Signal 4: Git-backed source
        is_git = self._is_git_backed(event)
        if is_git:
            signals.append("git_backed_source")

        # Signal 5: API-triggered (not UI)
        is_api = self._is_api_triggered(event)
        if is_api:
            signals.append("api_triggered")

        # Classification logic — weighted signal evaluation
        score = 0
        if "pre_classified_golden_path" in signals:
            score += 50
        if has_token:
            score += 40
        if is_sp:
            score += 30
        if is_git:
            score += 15
        if is_known_ci:
            score += 10
        if is_api:
            score += 5

        if score >= 40:
            classification = "standard"
            confidence = min(0.99, 0.50 + score / 100)
        elif score == 0:
            classification = "non_standard"
            confidence = 0.90
        else:
            classification = "unknown"
            confidence = 0.50

        # Use team_id from event if team resolution fails
        resolved_team = self._resolve_team(actor)
        if not resolved_team:
            resolved_team = event.get("team_id")

        return {
            "classification": classification,
            "confidence": round(confidence, 2),
            "signals": signals,
            "artifact_type": event.get("artifact_type") or ARTIFACT_TYPE_MAP.get(action, "other"),
            "team_id": resolved_team,
            "actor_email": actor,
            "action_name": action,
            "timestamp": event.get("event_date", event.get("event_time", event.get("timestamp", datetime.utcnow().isoformat()))),
        }

    def classify_batch(self, events: list[dict]) -> list[dict]:
        """Classify a batch of deployment events."""
        return [self.classify(e) for e in events]

    def compute_adoption_metrics(self, classified_events: list[dict]) -> dict:
        """
        Compute golden path adoption metrics from classified events.

        Returns:
            {
                "total_deployments": int,
                "standard_count": int,
                "non_standard_count": int,
                "unknown_count": int,
                "adoption_pct": float,
                "by_artifact_type": {artifact_type: {"standard": int, "non_standard": int}},
                "by_team": {team_id: {"standard": int, "non_standard": int, "adoption_pct": float}},
                "trend": [{"date": str, "adoption_pct": float}],
            }
        """
        total = len(classified_events)
        standard = sum(1 for e in classified_events if e["classification"] == "standard")
        non_standard = sum(1 for e in classified_events if e["classification"] == "non_standard")
        unknown = total - standard - non_standard

        # By artifact type
        by_artifact = {}
        for e in classified_events:
            at = e.get("artifact_type", "other")
            if at not in by_artifact:
                by_artifact[at] = {"standard": 0, "non_standard": 0}
            if e["classification"] == "standard":
                by_artifact[at]["standard"] += 1
            else:
                by_artifact[at]["non_standard"] += 1

        # By team
        by_team = {}
        for e in classified_events:
            tid = e.get("team_id") or "unassigned"
            if tid not in by_team:
                by_team[tid] = {"standard": 0, "non_standard": 0}
            if e["classification"] == "standard":
                by_team[tid]["standard"] += 1
            else:
                by_team[tid]["non_standard"] += 1
        for tid, counts in by_team.items():
            t = counts["standard"] + counts["non_standard"]
            counts["adoption_pct"] = round(counts["standard"] / t * 100, 1) if t > 0 else 0

        # Daily trend
        daily = {}
        for e in classified_events:
            day = str(e.get("timestamp", ""))[:10]
            if day not in daily:
                daily[day] = {"standard": 0, "total": 0}
            daily[day]["total"] += 1
            if e["classification"] == "standard":
                daily[day]["standard"] += 1
        trend = [
            {"date": d, "adoption_pct": round(v["standard"] / v["total"] * 100, 1) if v["total"] > 0 else 0}
            for d, v in sorted(daily.items())
        ]

        return {
            "total_deployments": total,
            "standard_count": standard,
            "non_standard_count": non_standard,
            "unknown_count": unknown,
            "adoption_pct": round(standard / total * 100, 1) if total > 0 else 0,
            "by_artifact_type": by_artifact,
            "by_team": by_team,
            "trend": trend,
        }

    def _extract_actor(self, event: dict) -> str:
        """Extract actor email from various event formats."""
        if "user_identity" in event and isinstance(event["user_identity"], dict):
            return event["user_identity"].get("email", "")
        return event.get("actor_email", event.get("deployed_by", ""))

    def _is_service_principal(self, actor: str) -> bool:
        """Check if actor email matches service principal patterns."""
        if not actor:
            return False
        actor_lower = actor.lower()
        if any(kw in actor_lower for kw in ("service", "spn", "svc", "bot", "automation", "cicd", "ci-cd", "deploy")):
            return True
        return any(p.match(actor) for p in SP_PATTERNS)

    def _has_golden_path_token(self, event: dict) -> bool:
        """Check if event has a golden_path_token in metadata."""
        params = event.get("request_params", {})
        if isinstance(params, str):
            return "golden_path" in params.lower()
        if isinstance(params, dict):
            if params.get("golden_path_tag") or params.get("golden_path_token"):
                return True
            metadata = params.get("metadata", "")
            if isinstance(metadata, str) and "golden_path" in metadata.lower():
                return True
        return event.get("golden_path_tag", False)

    def _is_git_backed(self, event: dict) -> bool:
        """Check if the deployment source is git-backed."""
        params = event.get("request_params", {})
        if isinstance(params, dict):
            settings = str(params.get("settings", ""))
            if '"source":"GIT"' in settings or '"git_source"' in settings:
                return True
            if params.get("source_type") == "git_backed":
                return True
        return event.get("source_type") == "git_backed"

    def _is_api_triggered(self, event: dict) -> bool:
        """Check if the action was triggered via API (not UI)."""
        source = event.get("source_ip_address", "")
        if source and source not in ("127.0.0.1", "::1"):
            return True
        return False

    def _resolve_team(self, actor: str) -> str | None:
        """Resolve actor email to team_id using team registry."""
        if not actor:
            return None
        for team_id, members in self.team_registry.items():
            if actor in members:
                return team_id
        return None
