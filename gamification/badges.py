"""Badge Engine — Defines and evaluates achievement badges for teams."""

from datetime import datetime

BADGE_DEFINITIONS = [
    {
        "id": "golden_path_champion",
        "name": "Golden Path Champion",
        "icon": "fas fa-road",
        "color": "#22C55E",
        "description": "Maintained 90%+ golden path adoption for 4 consecutive weeks",
        "criteria_type": "streak",
        "criteria": {"metric": "golden_path_adoption", "threshold": 90, "periods": 4},
    },
    {
        "id": "security_first",
        "name": "Security First",
        "icon": "fas fa-shield-alt",
        "color": "#3B82F6",
        "description": "All security hygiene checks passing",
        "criteria_type": "all_passing",
        "criteria": {"dimension": "security_compliance", "min_score": 80},
    },
    {
        "id": "speed_demon",
        "name": "Speed Demon",
        "icon": "fas fa-bolt",
        "color": "#FBBF24",
        "description": "Average build time under 5 minutes",
        "criteria_type": "threshold",
        "criteria": {"metric": "avg_build_minutes", "threshold": 5, "direction": "below"},
    },
    {
        "id": "test_master",
        "name": "Test Master",
        "icon": "fas fa-vial",
        "color": "#8B5CF6",
        "description": "Test coverage above 80% with zero flaky tests",
        "criteria_type": "threshold",
        "criteria": {"metric": "test_coverage_pct", "threshold": 80, "direction": "above"},
    },
    {
        "id": "consistency_king",
        "name": "Consistency King",
        "icon": "fas fa-chart-line",
        "color": "#EC4899",
        "description": "Score improved for 3 consecutive assessment periods",
        "criteria_type": "streak",
        "criteria": {"metric": "composite_score", "threshold": 0, "periods": 3, "direction": "improving"},
    },
    {
        "id": "dora_elite",
        "name": "DORA Elite",
        "icon": "fas fa-trophy",
        "color": "#F59E0B",
        "description": "All 4 DORA metrics at Elite tier",
        "criteria_type": "dora_tier",
        "criteria": {"required_tier": "Elite", "metrics_required": 4},
    },
    {
        "id": "zero_incidents",
        "name": "Zero Incidents",
        "icon": "fas fa-check-circle",
        "color": "#10B981",
        "description": "No production incidents for 30 consecutive days",
        "criteria_type": "threshold",
        "criteria": {"metric": "incidents_30d", "threshold": 0, "direction": "equal"},
    },
    {
        "id": "rapid_recovery",
        "name": "Rapid Recovery",
        "icon": "fas fa-heartbeat",
        "color": "#EF4444",
        "description": "MTTR under 1 hour for all incidents",
        "criteria_type": "threshold",
        "criteria": {"metric": "mttr_hours", "threshold": 1, "direction": "below"},
    },
    {
        "id": "full_coverage",
        "name": "Full Coverage",
        "icon": "fas fa-umbrella",
        "color": "#06B6D4",
        "description": "Connected all CI/CD platforms with active data sync",
        "criteria_type": "threshold",
        "criteria": {"metric": "connected_platforms", "threshold": 3, "direction": "above"},
    },
    {
        "id": "tier_up",
        "name": "Level Up!",
        "icon": "fas fa-arrow-up",
        "color": "#7C3AED",
        "description": "Moved up a maturity tier (e.g., Managed → Defined)",
        "criteria_type": "tier_change",
        "criteria": {"direction": "up"},
    },
]


def evaluate_badges(team_data: dict) -> list[dict]:
    """
    Evaluate which badges a team has earned.

    Args:
        team_data: {
            "team_id": str,
            "metrics": {
                "golden_path_adoption": float (0-100),
                "composite_score": float (0-100),
                "avg_build_minutes": float,
                "test_coverage_pct": float,
                "incidents_30d": int,
                "mttr_hours": float,
                "connected_platforms": int,
            },
            "score_history": [{"period": str, "score": float}],
            "dora_tiers": {"deploy_freq": str, "lead_time": str, "cfr": str, "mttr": str},
            "dimension_scores": {dimension: float},
            "previous_tier": str | None,
            "current_tier": str,
        }

    Returns: List of earned badge dicts with earned_at timestamp
    """
    earned = []
    metrics = team_data.get("metrics", {})
    history = team_data.get("score_history", [])

    for badge in BADGE_DEFINITIONS:
        criteria = badge.get("criteria", {})
        ctype = badge.get("criteria_type", "")

        if ctype == "threshold":
            metric_val = metrics.get(criteria.get("metric", ""), None)
            if metric_val is None:
                continue
            threshold = criteria.get("threshold", 0)
            direction = criteria.get("direction", "above")
            if direction == "above" and metric_val >= threshold:
                earned.append(_earn(badge))
            elif direction == "below" and metric_val <= threshold:
                earned.append(_earn(badge))
            elif direction == "equal" and metric_val == threshold:
                earned.append(_earn(badge))

        elif ctype == "streak":
            periods_needed = criteria.get("periods", 3)
            metric_key = criteria.get("metric", "composite_score")
            threshold = criteria.get("threshold", 0)
            direction = criteria.get("direction", "above")

            if len(history) >= periods_needed:
                recent = history[-periods_needed:]
                if direction == "improving":
                    if all(recent[i].get("score", 0) > recent[i - 1].get("score", 0) for i in range(1, len(recent))):
                        earned.append(_earn(badge))
                else:
                    vals = [h.get(metric_key, h.get("score", 0)) for h in recent]
                    if all(v >= threshold for v in vals):
                        earned.append(_earn(badge))

        elif ctype == "all_passing":
            dim = criteria.get("dimension", "")
            dim_scores = team_data.get("dimension_scores", {})
            score = dim_scores.get(dim, 0)
            if score >= criteria.get("min_score", 80):
                earned.append(_earn(badge))

        elif ctype == "dora_tier":
            dora = team_data.get("dora_tiers", {})
            required = criteria.get("required_tier", "Elite")
            needed = criteria.get("metrics_required", 4)
            at_tier = sum(1 for t in dora.values() if t == required)
            if at_tier >= needed:
                earned.append(_earn(badge))

        elif ctype == "tier_change":
            prev = team_data.get("previous_tier")
            curr = team_data.get("current_tier")
            tier_order = ["Ad Hoc", "Managed", "Defined", "Measured", "Optimized"]
            if prev and curr and prev in tier_order and curr in tier_order:
                if tier_order.index(curr) > tier_order.index(prev):
                    earned.append(_earn(badge))

    return earned


def _earn(badge: dict) -> dict:
    """Create an earned badge record."""
    return {
        "id": badge["id"],
        "name": badge["name"],
        "icon": badge["icon"],
        "color": badge["color"],
        "description": badge["description"],
        "earned_at": datetime.utcnow().isoformat(),
    }


def get_all_badges() -> list[dict]:
    """Return all badge definitions."""
    return [
        {k: v for k, v in b.items() if k != "criteria_type"}
        for b in BADGE_DEFINITIONS
    ]
