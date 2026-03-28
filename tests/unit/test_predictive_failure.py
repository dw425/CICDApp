"""Tests for Predictive CI Failure Scoring."""

import pytest
from analytics.predictive_failure import compute_risk_score, build_historical_patterns


class TestComputeRiskScore:
    def test_low_risk_small_change(self):
        change = {
            "files_changed": 2,
            "lines_added": 10,
            "lines_removed": 5,
            "author": "experienced_dev",
            "hour_of_day": 10,
            "day_of_week": 2,  # Wednesday
        }
        patterns = {
            "author_failure_rates": {"experienced_dev": 0.05},
            "time_failure_rates": {},
            "overall_failure_rate": 0.1,
        }
        result = compute_risk_score(change, patterns)
        assert 0 <= result["risk_score"] <= 100
        assert result["risk_level"] in ("low", "medium")

    def test_high_risk_friday_deploy(self):
        change = {
            "files_changed": 50,
            "lines_added": 2000,
            "lines_removed": 500,
            "author": "new_dev",
            "hour_of_day": 17,
            "day_of_week": 4,  # Friday
        }
        patterns = {
            "author_failure_rates": {"new_dev": 0.4},
            "time_failure_rates": {},
            "overall_failure_rate": 0.1,
        }
        result = compute_risk_score(change, patterns)
        assert result["risk_score"] > 50
        assert result["risk_level"] in ("high", "critical")

    def test_unknown_author(self):
        change = {
            "files_changed": 5,
            "lines_added": 50,
            "lines_removed": 10,
            "author": "unknown_dev",
            "hour_of_day": 14,
            "day_of_week": 2,
        }
        patterns = {"author_failure_rates": {}, "time_failure_rates": {}, "overall_failure_rate": 0.1}
        result = compute_risk_score(change, patterns)
        assert 0 <= result["risk_score"] <= 100
        assert "risk_factors" in result

    def test_result_structure(self):
        change = {"files_changed": 1, "lines_added": 5, "lines_removed": 2,
                  "author": "dev", "hour_of_day": 10, "day_of_week": 1}
        patterns = {"author_failure_rates": {}, "time_failure_rates": {}, "overall_failure_rate": 0.1}
        result = compute_risk_score(change, patterns)
        assert "risk_score" in result
        assert "risk_level" in result
        assert "risk_factors" in result
        assert isinstance(result["risk_factors"], list)


class TestBuildHistoricalPatterns:
    def test_computes_rates(self):
        history = [
            {"author": "dev1", "result": "success", "timestamp": "2024-03-01T10:00:00"},
            {"author": "dev1", "result": "failure", "timestamp": "2024-03-01T10:30:00"},
            {"author": "dev1", "result": "success", "timestamp": "2024-03-01T14:00:00"},
            {"author": "dev1", "result": "success", "timestamp": "2024-03-02T10:00:00"},
            {"author": "dev1", "result": "success", "timestamp": "2024-03-03T10:00:00"},
            {"author": "dev2", "result": "success", "timestamp": "2024-03-01T10:00:00"},
            {"author": "dev2", "result": "success", "timestamp": "2024-03-02T10:00:00"},
            {"author": "dev2", "result": "success", "timestamp": "2024-03-03T10:00:00"},
            {"author": "dev2", "result": "success", "timestamp": "2024-03-04T10:00:00"},
            {"author": "dev2", "result": "success", "timestamp": "2024-03-05T10:00:00"},
        ]
        patterns = build_historical_patterns(history)
        assert "author_failure_rates" in patterns
        assert patterns["author_failure_rates"]["dev1"] == pytest.approx(1 / 5, abs=0.01)
        assert patterns["author_failure_rates"]["dev2"] == 0.0

    def test_empty_history(self):
        patterns = build_historical_patterns([])
        assert patterns["author_failure_rates"] == {}
