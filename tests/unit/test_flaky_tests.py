"""Tests for Flaky Test Detection."""

import pytest
from analytics.flaky_tests import detect_flaky_tests, cluster_flaky_tests


class TestDetectFlakyTests:
    def test_detects_flaky(self):
        # Need at least 5 results per test, with mixed pass/fail on same commit
        test_results = [
            {"test_name": "test_login", "commit_sha": "abc123", "result": "pass", "duration_seconds": 1.0},
            {"test_name": "test_login", "commit_sha": "abc123", "result": "fail", "duration_seconds": 5.1},
            {"test_name": "test_login", "commit_sha": "abc123", "result": "pass", "duration_seconds": 1.2},
            {"test_name": "test_login", "commit_sha": "def456", "result": "fail", "duration_seconds": 5.0},
            {"test_name": "test_login", "commit_sha": "def456", "result": "pass", "duration_seconds": 1.1},
            {"test_name": "test_login", "commit_sha": "ghi789", "result": "pass", "duration_seconds": 1.0},
            {"test_name": "test_stable", "commit_sha": "abc123", "result": "pass", "duration_seconds": 0.5},
            {"test_name": "test_stable", "commit_sha": "abc123", "result": "pass", "duration_seconds": 0.5},
            {"test_name": "test_stable", "commit_sha": "def456", "result": "pass", "duration_seconds": 0.5},
            {"test_name": "test_stable", "commit_sha": "def456", "result": "pass", "duration_seconds": 0.5},
            {"test_name": "test_stable", "commit_sha": "ghi789", "result": "pass", "duration_seconds": 0.5},
        ]
        flaky = detect_flaky_tests(test_results)
        flaky_names = [f["test_name"] for f in flaky]
        assert "test_login" in flaky_names
        assert "test_stable" not in flaky_names

    def test_empty_results(self):
        flaky = detect_flaky_tests([])
        assert flaky == []

    def test_all_passing(self):
        test_results = [
            {"test_name": "test_ok", "commit_sha": "abc", "result": "pass", "duration_seconds": 1.0}
            for _ in range(6)
        ]
        flaky = detect_flaky_tests(test_results)
        assert flaky == []


class TestClusterFlakyTests:
    def test_clusters_by_cause(self):
        flaky = [
            {"test_name": "test_timeout", "likely_cause": "timeout_sensitivity"},
            {"test_name": "test_db_conn", "likely_cause": "database_state"},
        ]
        clusters = cluster_flaky_tests(flaky)
        assert isinstance(clusters, dict)
        assert "timeout_sensitivity" in clusters
        assert "database_state" in clusters

    def test_empty_input(self):
        clusters = cluster_flaky_tests([])
        assert clusters == {}
