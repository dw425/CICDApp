"""Tests for Remediation Engine."""

import pytest
from analytics.remediation_engine import get_remediation, get_top_remediations, REMEDIATION_TEMPLATES


class TestGetRemediation:
    def test_known_check(self):
        result = get_remediation("gh_branch_protection")
        assert result is not None
        assert "title" in result
        assert "steps" in result
        assert "impact" in result
        assert "effort" in result

    def test_unknown_check_gets_generic(self):
        result = get_remediation("nonexistent_check_id_xyz")
        # Falls back to generic
        assert result is not None
        assert "title" in result

    def test_all_templates_valid(self):
        for check_id, template in REMEDIATION_TEMPLATES.items():
            assert "title" in template, f"Missing title for {check_id}"
            assert "steps" in template, f"Missing steps for {check_id}"
            assert isinstance(template["steps"], list), f"Steps not a list for {check_id}"
            assert len(template["steps"]) > 0, f"Empty steps for {check_id}"


class TestGetTopRemediations:
    def test_returns_limited(self):
        failing_checks = [
            {"check_id": "gh_branch_protection", "score": 0, "weight": 10},
            {"check_id": "gh_secret_scanning", "score": 20, "weight": 8},
            {"check_id": "gh_ci_test_step", "score": 30, "weight": 7},
            {"check_id": "jk_pipeline_as_code", "score": 10, "weight": 9},
        ]
        top = get_top_remediations(failing_checks, limit=3)
        assert len(top) <= 3

    def test_empty_checks(self):
        top = get_top_remediations([])
        assert top == []

    def test_all_passing(self):
        checks = [{"check_id": "gh_branch_protection", "score": 100, "weight": 10}]
        top = get_top_remediations(checks)
        assert top == []
