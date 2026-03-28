"""Tests for Anomaly Detection."""

import pytest
from analytics.anomaly_detection import detect_score_anomalies, detect_stale_connectors


class TestScoreAnomalies:
    def test_detects_spike(self):
        # Lots of consistent deltas followed by a massive spike
        history = [
            {"team_id": "t1", "period_start": "2024-W01", "avg_score": 50, "delta": 1},
            {"team_id": "t1", "period_start": "2024-W02", "avg_score": 51, "delta": 1},
            {"team_id": "t1", "period_start": "2024-W03", "avg_score": 52, "delta": 1},
            {"team_id": "t1", "period_start": "2024-W04", "avg_score": 53, "delta": 1},
            {"team_id": "t1", "period_start": "2024-W05", "avg_score": 54, "delta": 1},
            {"team_id": "t1", "period_start": "2024-W06", "avg_score": 55, "delta": 1},
            {"team_id": "t1", "period_start": "2024-W07", "avg_score": 56, "delta": 1},
            {"team_id": "t1", "period_start": "2024-W08", "avg_score": 96, "delta": 40},
        ]
        anomalies = detect_score_anomalies(history, z_threshold=2.0)
        assert len(anomalies) > 0
        assert anomalies[0]["team_id"] == "t1"

    def test_no_anomalies_stable(self):
        history = [
            {"team_id": "t1", "period_start": f"2024-W{i:02d}", "avg_score": 50 + i, "delta": 1}
            for i in range(10)
        ]
        anomalies = detect_score_anomalies(history, z_threshold=3.0)
        assert len(anomalies) == 0

    def test_empty_history(self):
        anomalies = detect_score_anomalies([])
        assert anomalies == []


class TestStaleConnectors:
    def test_detects_stale(self):
        sync_history = [
            {"platform": "github", "timestamp": "2024-01-01T00:00:00"},
            {"platform": "jenkins", "timestamp": "2099-01-01T00:00:00"},
        ]
        stale = detect_stale_connectors(sync_history, stale_hours=24)
        stale_names = [s["platform"] for s in stale]
        assert "github" in stale_names
        assert "jenkins" not in stale_names

    def test_empty_history(self):
        stale = detect_stale_connectors([])
        assert stale == []
