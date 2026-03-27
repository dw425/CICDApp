"""Tests for hard-gate scoring logic in hygiene scoring."""

import pytest

from ingestion.hygiene_extractors.base_extractor import HygieneCheck
from compass.hygiene_scorer import _apply_hard_gates, aggregate_dimension_telemetry


def _make_check(check_id, score, hard_gate=False, dimension="build_integration", weight=3):
    """Helper to create a HygieneCheck for testing."""
    return HygieneCheck(
        check_id=check_id,
        check_name=f"Test {check_id}",
        platform="github",
        dimension=dimension,
        weight=weight,
        data_source="test",
        scoring_rule="test",
        hard_gate=hard_gate,
        raw_value=score,
        score=score,
    )


def test_hard_gate_failure_caps_at_40():
    """Test: failing a hard-gate check caps dimension score at 40."""
    checks = [
        _make_check("hg_01", score=0, hard_gate=True),     # Hard gate FAILS (score < 50)
        _make_check("hg_02", score=95, hard_gate=False),    # Regular pass
        _make_check("hg_03", score=90, hard_gate=False),    # Regular pass
        _make_check("hg_04", score=85, hard_gate=False),    # Regular pass
    ]

    # Without hard gate, weighted avg would be (0*3 + 95*3 + 90*3 + 85*3) / 12 = 67.5
    # With hard gate, should be capped at 40
    raw_score = sum(c.score * c.weight for c in checks) / sum(c.weight for c in checks)
    assert raw_score > 40, f"Raw score should be above 40 without gate: {raw_score}"

    capped = _apply_hard_gates(raw_score, checks)
    assert capped == 40, f"Expected 40 (capped), got {capped}"


def test_passing_hard_gates_allows_full_score():
    """Test: passing all hard gates allows full score range."""
    checks = [
        _make_check("hg_01", score=80, hard_gate=True),     # Hard gate PASSES (score >= 50)
        _make_check("hg_02", score=95, hard_gate=False),
        _make_check("hg_03", score=90, hard_gate=False),
        _make_check("hg_04", score=85, hard_gate=False),
    ]

    raw_score = sum(c.score * c.weight for c in checks) / sum(c.weight for c in checks)
    result = _apply_hard_gates(raw_score, checks)

    # Should not be capped — full score range
    assert result == raw_score, f"Expected {raw_score}, got {result}"
    assert result > 40, f"Score should be above 40: {result}"


def test_hard_gate_borderline_pass():
    """Test: hard gate at exactly 50 should pass (not trigger cap)."""
    checks = [
        _make_check("hg_01", score=50, hard_gate=True),     # Exactly 50 = pass
        _make_check("hg_02", score=90, hard_gate=False),
    ]

    raw_score = sum(c.score * c.weight for c in checks) / sum(c.weight for c in checks)
    result = _apply_hard_gates(raw_score, checks)
    assert result == raw_score, "Score=50 hard gate should not trigger cap"


def test_hard_gate_borderline_fail():
    """Test: hard gate at 49 should fail and cap at 40."""
    checks = [
        _make_check("hg_01", score=49, hard_gate=True),     # 49 < 50 = fail
        _make_check("hg_02", score=90, hard_gate=False),
    ]

    raw_score = sum(c.score * c.weight for c in checks) / sum(c.weight for c in checks)
    result = _apply_hard_gates(raw_score, checks)
    assert result == 40, f"Score=49 hard gate should cap at 40, got {result}"


def test_aggregate_telemetry_tracks_hard_gate():
    """Test: aggregate_dimension_telemetry correctly flags hard_gate_triggered."""
    checks_failing = [
        _make_check("hg_01", score=10, hard_gate=True, dimension="security_compliance"),
        _make_check("hg_02", score=90, hard_gate=False, dimension="security_compliance"),
    ]

    checks_passing = [
        _make_check("hg_03", score=80, hard_gate=True, dimension="build_integration"),
        _make_check("hg_04", score=85, hard_gate=False, dimension="build_integration"),
    ]

    result = aggregate_dimension_telemetry(checks_failing + checks_passing)

    assert result["security_compliance"]["hard_gate_triggered"] is True
    assert result["security_compliance"]["score"] <= 40

    assert result["build_integration"]["hard_gate_triggered"] is False
    assert result["build_integration"]["score"] > 40


def test_mock_data_produces_valid_scores():
    """Test: mock data from all extractors produces scores in valid 0-100 range."""
    from compass.hygiene_scorer import run_all_checks

    all_checks = run_all_checks()  # Uses mock data
    assert len(all_checks) > 0, "Should have checks from mock data"

    for check in all_checks:
        assert 0 <= check.score <= 100, f"Check {check.check_id} score {check.score} out of range"
        assert check.platform in ("github", "azure_devops", "jenkins", "gitlab", "jira", "databricks"), \
            f"Unexpected platform: {check.platform}"
        assert check.dimension, f"Check {check.check_id} has no dimension"
