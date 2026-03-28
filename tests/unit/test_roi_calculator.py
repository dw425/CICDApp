"""Tests for ROI Calculator."""

import pytest
from analytics.roi_calculator import compute_roi


class TestComputeROI:
    def test_basic_calculation(self):
        before = {"build_integration": 30, "pipeline_reliability": 40, "observability": 35,
                  "deployment_release": 30, "security_compliance": 25, "developer_experience": 30}
        after = {"build_integration": 60, "pipeline_reliability": 70, "observability": 65,
                 "deployment_release": 60, "security_compliance": 55, "developer_experience": 60}
        org = {"engineer_count": 50, "avg_salary": 150000, "deploy_frequency_per_week": 20,
               "incidents_per_month": 5, "avg_build_time_minutes": 15, "avg_mttr_hours": 4,
               "builds_per_day": 10}
        result = compute_roi(before, after, org)
        assert "total_annual_value" in result
        assert "breakdown" in result
        assert result["total_annual_value"] > 0

    def test_breakdown_categories(self):
        before = {"build_integration": 30, "pipeline_reliability": 40}
        after = {"build_integration": 60, "pipeline_reliability": 70}
        org = {"engineer_count": 10, "avg_salary": 100000}
        result = compute_roi(before, after, org)
        categories = [b["category"] for b in result["breakdown"]]
        assert "Build Time Savings" in categories
        assert "Incident Cost Reduction" in categories

    def test_no_improvement(self):
        scores = {"build_integration": 50, "pipeline_reliability": 50}
        org = {"engineer_count": 50, "avg_salary": 150000}
        result = compute_roi(scores, scores, org)
        assert result["total_annual_value"] == 0
        assert result["improvement_pct"] == 0

    def test_more_engineers_more_savings(self):
        before = {"build_integration": 30}
        after = {"build_integration": 70}
        r1 = compute_roi(before, after, {"engineer_count": 10, "avg_salary": 150000})
        r2 = compute_roi(before, after, {"engineer_count": 100, "avg_salary": 150000})
        assert r2["total_annual_value"] >= r1["total_annual_value"]
