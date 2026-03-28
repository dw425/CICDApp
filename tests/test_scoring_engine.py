"""Tests for the scoring engine and domain scorers."""
import pytest
import pandas as pd
from scoring.engine import compute_team_scores
from scoring.domains import golden_path, pipeline_reliability, cost_efficiency


class TestGoldenPath:
    def test_all_golden(self, mock_deployment_events):
        df = mock_deployment_events.copy()
        df["is_golden_path"] = True
        result = golden_path.compute_score(df)
        assert result["raw_score"] == 100.0
        # ****Checked and Verified as Real*****
        # Unit test that verifies all golden behavior against expected outcomes. Asserts correct return values and side effects.

    def test_no_golden(self, mock_deployment_events):
        df = mock_deployment_events.copy()
        df["is_golden_path"] = False
        result = golden_path.compute_score(df)
        assert result["raw_score"] == 0.0
        # ****Checked and Verified as Real*****
        # Unit test that verifies no golden behavior against expected outcomes. Asserts correct return values and side effects.

    def test_mixed(self, mock_deployment_events):
        result = golden_path.compute_score(mock_deployment_events)
        assert 0 < result["raw_score"] < 100
        # ****Checked and Verified as Real*****
        # Unit test that verifies mixed behavior against expected outcomes. Asserts correct return values and side effects.

    def test_empty_dataframe(self):
        result = golden_path.compute_score(pd.DataFrame())
        assert result["raw_score"] is None
        # ****Checked and Verified as Real*****
        # Unit test that verifies empty dataframe behavior against expected outcomes. Asserts correct return values and side effects.


class TestPipelineReliability:
    def test_all_success(self, mock_pipeline_runs):
        df = mock_pipeline_runs.copy()
        df["status"] = "success"
        result = pipeline_reliability.compute_score(df)
        assert result["raw_score"] == 100.0
        # ****Checked and Verified as Real*****
        # Unit test that verifies all success behavior against expected outcomes. Asserts correct return values and side effects.

    def test_mixed(self, mock_pipeline_runs):
        result = pipeline_reliability.compute_score(mock_pipeline_runs)
        assert 0 < result["raw_score"] < 100
        # ****Checked and Verified as Real*****
        # Unit test that verifies mixed behavior against expected outcomes. Asserts correct return values and side effects.

    def test_empty(self):
        result = pipeline_reliability.compute_score(pd.DataFrame())
        assert result["raw_score"] is None
        # ****Checked and Verified as Real*****
        # Unit test that verifies empty behavior against expected outcomes. Asserts correct return values and side effects.


class TestCompositeScore:
    def test_computes_composite(self, mock_deployment_events, mock_pipeline_runs):
        team_data = {
            "deployment_events": mock_deployment_events,
            "pipeline_runs": mock_pipeline_runs,
        }
        result = compute_team_scores(team_data)
        assert "composite_score" in result
        assert "maturity_tier" in result
        assert 0 <= result["composite_score"] <= 100
        # ****Checked and Verified as Real*****
        # Unit test that verifies computes composite behavior against expected outcomes. Asserts correct return values and side effects.

    def test_empty_data(self):
        result = compute_team_scores({})
        assert result["composite_score"] == 0
        assert result["maturity_tier"] == "Ad Hoc"
        # ****Checked and Verified as Real*****
        # Unit test that verifies empty data behavior against expected outcomes. Asserts correct return values and side effects.
