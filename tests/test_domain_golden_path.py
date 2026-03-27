"""Focused tests for Golden Path domain scorer."""
import pytest
import pandas as pd
from scoring.domains.golden_path import compute_score


def test_perfect_score():
    df = pd.DataFrame({"is_golden_path": [True] * 10, "actor_type": ["sp"] * 10, "status": ["success"] * 10})
    result = compute_score(df)
    assert result["raw_score"] == 100.0
    assert result["details"]["golden_path_ratio"] == 1.0


def test_zero_score():
    df = pd.DataFrame({"is_golden_path": [False] * 5, "actor_type": ["human"] * 5, "status": ["success"] * 5})
    result = compute_score(df)
    assert result["raw_score"] == 0.0


def test_none_input():
    result = compute_score(None)
    assert result["raw_score"] is None
