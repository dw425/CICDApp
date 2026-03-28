"""Anomaly Detection — Detects sudden drops in maturity scores and unusual patterns."""

import numpy as np
from datetime import datetime


def detect_score_anomalies(trends: list[dict], z_threshold: float = 2.0) -> list[dict]:
    """
    Detect anomalous score changes using Z-score method.

    Args:
        trends: List of dicts with keys: team_id, period_start, avg_score, delta
        z_threshold: Number of standard deviations to flag as anomaly

    Returns:
        List of anomaly alerts: [{team_id, period, score, expected_range, severity, description}]
    """
    if not trends:
        return []

    # Group by team
    by_team = {}
    for t in trends:
        tid = t.get("team_id", "unknown")
        if tid not in by_team:
            by_team[tid] = []
        by_team[tid].append(t)

    anomalies = []
    for team_id, team_trends in by_team.items():
        if len(team_trends) < 3:
            continue

        sorted_trends = sorted(team_trends, key=lambda x: x.get("period_start", ""))
        scores = [t.get("avg_score", 0) for t in sorted_trends]
        deltas = [t.get("delta", 0) for t in sorted_trends]

        # Z-score on deltas
        if len(deltas) < 3:
            continue

        mean_delta = np.mean(deltas)
        std_delta = np.std(deltas)
        if std_delta == 0:
            continue

        latest = sorted_trends[-1]
        latest_delta = latest.get("delta", 0)
        z_score = (latest_delta - mean_delta) / std_delta

        if abs(z_score) >= z_threshold:
            severity = "critical" if abs(z_score) >= 3 else "warning"
            direction = "drop" if latest_delta < 0 else "spike"

            anomalies.append({
                "team_id": team_id,
                "period": latest.get("period_start", ""),
                "score": latest.get("avg_score", 0),
                "delta": round(latest_delta, 1),
                "z_score": round(z_score, 2),
                "expected_range": (
                    round(mean_delta - z_threshold * std_delta, 1),
                    round(mean_delta + z_threshold * std_delta, 1),
                ),
                "severity": severity,
                "description": (
                    f"Score {direction} of {abs(latest_delta):.1f} points "
                    f"(z={z_score:.1f}, expected delta: {mean_delta:.1f} +/- {std_delta:.1f})"
                ),
                "detected_at": datetime.utcnow().isoformat(),
            })

    return anomalies


def detect_stale_connectors(sync_history: list[dict], stale_hours: int = 24) -> list[dict]:
    """Detect connectors that haven't synced within threshold."""
    alerts = []
    now = datetime.utcnow()

    platform_last_sync = {}
    for entry in sync_history:
        platform = entry.get("platform", "")
        ts = entry.get("timestamp", "")
        if ts and (platform not in platform_last_sync or ts > platform_last_sync[platform]):
            platform_last_sync[platform] = ts

    for platform, last_ts in platform_last_sync.items():
        try:
            last_sync = datetime.fromisoformat(last_ts.replace("Z", "+00:00").replace("+00:00", ""))
            hours_ago = (now - last_sync).total_seconds() / 3600
            if hours_ago > stale_hours:
                alerts.append({
                    "platform": platform,
                    "last_sync": last_ts,
                    "hours_since_sync": round(hours_ago, 1),
                    "severity": "critical" if hours_ago > 72 else "warning",
                    "description": f"{platform} hasn't synced in {hours_ago:.0f} hours",
                })
        except (ValueError, TypeError):
            pass

    return alerts
