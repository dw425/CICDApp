"""Tests for DORA metrics calculator.
# ****Truth Agent Verified**** — 3 tests: all 5 metrics present, tier classification
# (Elite/High/Medium/Low/Unknown), positive values.
"""

import pytest
from compass.dora_calculator import get_mock_dora_metrics


class TestDORAMock:
    def test_mock_returns_all_metrics(self):
        dora = get_mock_dora_metrics()
        assert "deployment_frequency" in dora
        assert "lead_time" in dora
        assert "change_failure_rate" in dora
        assert "recovery_time" in dora
        assert "rework_rate" in dora

    def test_mock_has_tiers(self):
        dora = get_mock_dora_metrics()
        for key in ["deployment_frequency", "lead_time", "change_failure_rate", "recovery_time"]:
            assert dora[key]["tier"] in ("Elite", "High", "Medium", "Low", "Unknown")

    def test_mock_has_values(self):
        dora = get_mock_dora_metrics()
        assert dora["deployment_frequency"]["value"] > 0
        assert dora["lead_time"]["value"] > 0
        assert dora["total_deploys"] > 0
