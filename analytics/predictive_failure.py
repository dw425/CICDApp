"""Predictive CI Failure — Identifies high-risk commits using historical patterns."""

import math
from collections import defaultdict
from datetime import datetime


def compute_risk_score(commit_context: dict, historical_patterns: dict) -> dict:
    """
    Compute failure risk score for a commit/PR based on historical patterns.

    Args:
        commit_context: {
            "files_changed": int,
            "lines_added": int,
            "lines_removed": int,
            "author": str,
            "hour_of_day": int (0-23),
            "day_of_week": int (0=Mon, 6=Sun),
            "branch": str,
            "is_merge": bool,
            "commit_message": str,
        }
        historical_patterns: {
            "author_failure_rates": {author: float},
            "path_failure_rates": {path_prefix: float},
            "time_failure_rates": {hour: float},
            "size_failure_rates": [(threshold, rate)],
            "overall_failure_rate": float,
        }

    Returns: {
        "risk_score": float (0-100),
        "risk_level": "low" | "medium" | "high" | "critical",
        "risk_factors": [{"factor": str, "contribution": float, "description": str}],
    }
    """
    factors = []

    # Factor 1: Change size
    total_changes = commit_context.get("lines_added", 0) + commit_context.get("lines_removed", 0)
    files_changed = commit_context.get("files_changed", 0)
    size_risk = _size_risk(total_changes, files_changed)
    factors.append({
        "factor": "change_size",
        "contribution": size_risk,
        "description": f"{total_changes} lines across {files_changed} files",
    })

    # Factor 2: Author historical failure rate
    author = commit_context.get("author", "")
    author_rates = historical_patterns.get("author_failure_rates", {})
    author_rate = author_rates.get(author, historical_patterns.get("overall_failure_rate", 0.1))
    author_risk = min(author_rate * 100, 100)
    factors.append({
        "factor": "author_history",
        "contribution": author_risk,
        "description": f"Author failure rate: {author_rate:.1%}",
    })

    # Factor 3: Time of day risk
    hour = commit_context.get("hour_of_day", 12)
    day = commit_context.get("day_of_week", 2)
    time_risk = _time_risk(hour, day)
    factors.append({
        "factor": "timing",
        "contribution": time_risk,
        "description": f"{'High-risk' if time_risk > 50 else 'Normal'} deployment window",
    })

    # Factor 4: Friday deploy penalty
    if day == 4 and hour >= 14:  # Friday afternoon
        friday_risk = 30
        factors.append({
            "factor": "friday_deploy",
            "contribution": friday_risk,
            "description": "Friday afternoon deployment",
        })
    else:
        friday_risk = 0

    # Weighted composite
    weights = {"change_size": 0.35, "author_history": 0.30, "timing": 0.15, "friday_deploy": 0.20}
    risk_score = (
        size_risk * weights["change_size"]
        + author_risk * weights["author_history"]
        + time_risk * weights["timing"]
        + friday_risk * weights["friday_deploy"]
    )
    risk_score = min(100, max(0, risk_score))

    if risk_score >= 75:
        risk_level = "critical"
    elif risk_score >= 50:
        risk_level = "high"
    elif risk_score >= 25:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "risk_score": round(risk_score, 1),
        "risk_level": risk_level,
        "risk_factors": sorted(factors, key=lambda x: x["contribution"], reverse=True),
    }


def build_historical_patterns(pipeline_history: list[dict]) -> dict:
    """
    Build historical pattern data from pipeline execution history.

    Args:
        pipeline_history: List of dicts with keys:
            author, result (success/failure), timestamp, files_changed, lines_changed

    Returns: Pattern dict for compute_risk_score()
    """
    if not pipeline_history:
        return {
            "author_failure_rates": {},
            "time_failure_rates": {},
            "overall_failure_rate": 0.1,
        }

    total = len(pipeline_history)
    failures = sum(1 for p in pipeline_history if p.get("result") == "failure")

    # Author failure rates
    author_stats = defaultdict(lambda: {"total": 0, "failures": 0})
    for p in pipeline_history:
        author = p.get("author", "unknown")
        author_stats[author]["total"] += 1
        if p.get("result") == "failure":
            author_stats[author]["failures"] += 1

    author_rates = {
        author: stats["failures"] / stats["total"]
        for author, stats in author_stats.items()
        if stats["total"] >= 5
    }

    # Time-based failure rates
    time_stats = defaultdict(lambda: {"total": 0, "failures": 0})
    for p in pipeline_history:
        ts = p.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts) if isinstance(ts, str) else ts
            hour = dt.hour
            time_stats[hour]["total"] += 1
            if p.get("result") == "failure":
                time_stats[hour]["failures"] += 1
        except (ValueError, AttributeError):
            pass

    time_rates = {
        hour: stats["failures"] / stats["total"]
        for hour, stats in time_stats.items()
        if stats["total"] >= 3
    }

    return {
        "author_failure_rates": author_rates,
        "time_failure_rates": time_rates,
        "overall_failure_rate": failures / total if total > 0 else 0.1,
    }


def _size_risk(total_lines: int, files: int) -> float:
    """Calculate risk based on change size. Larger changes = higher risk."""
    if total_lines > 1000 or files > 20:
        return 90
    elif total_lines > 500 or files > 10:
        return 70
    elif total_lines > 200 or files > 5:
        return 45
    elif total_lines > 50:
        return 25
    return 10


def _time_risk(hour: int, day: int) -> float:
    """Calculate risk based on time of deployment."""
    # High risk: late evening, weekends
    if day >= 5:  # Saturday/Sunday
        return 60
    if hour < 6 or hour > 20:  # Before 6am or after 8pm
        return 50
    if hour >= 16:  # After 4pm
        return 30
    return 10
