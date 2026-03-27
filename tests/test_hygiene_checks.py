"""Tests for hygiene check framework.
# ****Truth Agent Verified**** — 9 tests: 78 total checks, valid scores, platform coverage
# (6 platforms), per-platform counts, hard gates >=5, dimension aggregation,
# platform summary, check definitions, hard gate capping at 40.
"""

import pytest
from compass.hygiene_scorer import (
    run_all_checks,
    aggregate_dimension_telemetry,
    get_platform_summary,
    get_all_check_definitions,
)


class TestHygieneChecks:
    def test_runs_all_78_checks(self):
        checks = run_all_checks()
        assert len(checks) == 78

    def test_all_checks_have_scores(self):
        checks = run_all_checks()
        for c in checks:
            assert 0 <= c.score <= 100, f"{c.check_id} has invalid score {c.score}"

    def test_platform_coverage(self):
        checks = run_all_checks()
        platforms = set(c.platform for c in checks)
        assert platforms == {"github", "azure_devops", "jenkins", "gitlab", "jira", "databricks"}

    def test_platform_counts(self):
        checks = run_all_checks()
        by_platform = {}
        for c in checks:
            by_platform.setdefault(c.platform, 0)
            by_platform[c.platform] += 1
        assert by_platform["github"] == 22
        assert by_platform["azure_devops"] == 13
        assert by_platform["jenkins"] == 10
        assert by_platform["gitlab"] == 15
        assert by_platform["jira"] == 5
        assert by_platform["databricks"] == 13

    def test_hard_gates_exist(self):
        checks = run_all_checks()
        hard_gates = [c for c in checks if c.hard_gate]
        assert len(hard_gates) >= 5

    def test_aggregate_dimension_telemetry(self):
        checks = run_all_checks()
        scores = aggregate_dimension_telemetry(checks)
        assert len(scores) > 0
        for dim, data in scores.items():
            assert "score" in data
            assert "check_count" in data

    def test_platform_summary(self):
        checks = run_all_checks()
        summary = get_platform_summary(checks)
        for p, data in summary.items():
            assert data["total"] > 0
            assert data["passing"] + data["warning"] + data["failing"] == data["total"]

    def test_get_all_check_definitions(self):
        defs = get_all_check_definitions()
        assert len(defs) == 78
        for d in defs:
            assert "check_id" in d
            assert "platform" in d
            assert "dimension" in d


class TestHardGates:
    def test_hard_gate_caps_dimension(self):
        checks = run_all_checks()
        scores = aggregate_dimension_telemetry(checks)
        for dim, data in scores.items():
            if data.get("hard_gate_triggered"):
                assert data["score"] <= 40, f"{dim} hard gate should cap at 40"
