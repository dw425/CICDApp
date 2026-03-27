"""Coaching Alert Generation"""
from datetime import datetime

ALERT_RULES = [
    {
        "domain": "golden_path",
        "threshold": 50,
        "direction": "below",
        "severity": "critical",
        "alert_type": "low_golden_path",
        "message": "Golden path adoption below 50%",
        "recommendation": "Migrate manual deployments to service principal-driven CI/CD pipelines. Start with the most frequently deployed artifacts.",
    },
    {
        "domain": "golden_path",
        "threshold": 75,
        "direction": "below",
        "severity": "warning",
        "alert_type": "moderate_golden_path",
        "message": "Golden path adoption below 75%",
        "recommendation": "Review remaining human-initiated deployments and create automation templates for common patterns.",
    },
    {
        "domain": "pipeline_reliability",
        "threshold": 60,
        "direction": "below",
        "severity": "critical",
        "alert_type": "low_reliability",
        "message": "Pipeline reliability below 60%",
        "recommendation": "Investigate frequent pipeline failures. Add retry logic, improve error handling, and review resource allocation.",
    },
    {
        "domain": "pipeline_reliability",
        "threshold": 80,
        "direction": "below",
        "severity": "warning",
        "alert_type": "moderate_reliability",
        "message": "Pipeline reliability below 80%",
        "recommendation": "Review intermittent failures and consider adding data quality checks at pipeline entry points.",
    },
    {
        "domain": "security_governance",
        "threshold": 70,
        "direction": "below",
        "severity": "warning",
        "alert_type": "low_compliance",
        "message": "Cluster policy compliance below 70%",
        "recommendation": "Enforce cluster policies across all workspaces. Review non-compliant clusters and migrate to policy-compliant configurations.",
    },
    {
        "domain": "cost_efficiency",
        "threshold": 40,
        "direction": "below",
        "severity": "info",
        "alert_type": "high_interactive_usage",
        "message": "High interactive compute usage detected",
        "recommendation": "Shift interactive workloads to scheduled jobs where possible. Review notebook-based workflows for automation opportunities.",
    },
    {
        "domain": "data_quality",
        "threshold": 50,
        "direction": "below",
        "severity": "warning",
        "alert_type": "low_data_quality",
        "message": "Data quality score below 50%",
        "recommendation": "Add table constraints (NOT NULL, CHECK) and DLT expectations to improve data validation coverage.",
    },
]


def generate_alerts(team_id: str, team_name: str, domain_scores: dict) -> list:
    """Generate coaching alerts based on domain scores and threshold rules.

    Args:
        team_id: Team identifier
        team_name: Team display name
        domain_scores: {domain: {raw_score, ...}}

    Returns:
        List of alert dicts
    """
    alerts = []
    for rule in ALERT_RULES:
        domain = rule["domain"]
        score_data = domain_scores.get(domain, {})
        raw_score = score_data.get("raw_score")

        if raw_score is None:
            continue

        triggered = False
        if rule["direction"] == "below" and raw_score < rule["threshold"]:
            triggered = True
        elif rule["direction"] == "above" and raw_score > rule["threshold"]:
            triggered = True

        if triggered:
            alerts.append({
                "team_id": team_id,
                "team_name": team_name,
                "severity": rule["severity"],
                "alert_type": rule["alert_type"],
                "domain": domain,
                "message": f"{team_name}: {rule['message']} (current: {raw_score})",
                "recommendation": rule["recommendation"],
                "created_date": datetime.now().strftime("%Y-%m-%d"),
                "is_acknowledged": False,
            })

    return alerts
