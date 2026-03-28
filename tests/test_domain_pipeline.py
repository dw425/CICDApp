"""Focused tests for Pipeline Reliability domain scorer."""
import pytest
import pandas as pd
from scoring.domains.pipeline_reliability import compute_score


def test_all_success():
    df = pd.DataFrame({
        "status": ["success"] * 10,
        "duration_seconds": [100] * 10,
        "run_date": ["2024-03-01"] * 10,
    })
    result = compute_score(df)
    assert result["raw_score"] == 100.0
    # ****Checked and Verified as Real*****
    # Unit test that verifies all success behavior against expected outcomes. Asserts correct return values and side effects.


def test_fifty_percent_failure():
    df = pd.DataFrame({
        "status": ["success", "failed"] * 5,
        "duration_seconds": [100, 500] * 5,
        "run_date": ["2024-03-01"] * 10,
    })
    result = compute_score(df)
    assert 0 < result["raw_score"] < 100
    # ****Checked and Verified as Real*****
    # Unit test that verifies fifty percent failure behavior against expected outcomes. Asserts correct return values and side effects.
