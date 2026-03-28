"""Tests for Badge Engine."""

import pytest
from gamification.badges import evaluate_badges, get_all_badges, BADGE_DEFINITIONS


class TestEvaluateBadges:
    def test_speed_demon_earned(self):
        team_data = {
            "team_id": "t1",
            "metrics": {"avg_build_minutes": 3.5},
            "score_history": [],
            "dora_tiers": {},
            "dimension_scores": {},
            "previous_tier": None,
            "current_tier": "Managed",
        }
        earned = evaluate_badges(team_data)
        badge_ids = [b["id"] for b in earned]
        assert "speed_demon" in badge_ids

    def test_speed_demon_not_earned(self):
        team_data = {
            "team_id": "t1",
            "metrics": {"avg_build_minutes": 10},
            "score_history": [],
            "dora_tiers": {},
            "dimension_scores": {},
            "previous_tier": None,
            "current_tier": "Managed",
        }
        earned = evaluate_badges(team_data)
        badge_ids = [b["id"] for b in earned]
        assert "speed_demon" not in badge_ids

    def test_zero_incidents_earned(self):
        team_data = {
            "team_id": "t1",
            "metrics": {"incidents_30d": 0},
            "score_history": [],
            "dora_tiers": {},
            "dimension_scores": {},
            "previous_tier": None,
            "current_tier": "Managed",
        }
        earned = evaluate_badges(team_data)
        badge_ids = [b["id"] for b in earned]
        assert "zero_incidents" in badge_ids

    def test_dora_elite_earned(self):
        team_data = {
            "team_id": "t1",
            "metrics": {},
            "score_history": [],
            "dora_tiers": {
                "deploy_freq": "Elite",
                "lead_time": "Elite",
                "cfr": "Elite",
                "mttr": "Elite",
            },
            "dimension_scores": {},
            "previous_tier": None,
            "current_tier": "Optimized",
        }
        earned = evaluate_badges(team_data)
        badge_ids = [b["id"] for b in earned]
        assert "dora_elite" in badge_ids

    def test_tier_up_earned(self):
        team_data = {
            "team_id": "t1",
            "metrics": {},
            "score_history": [],
            "dora_tiers": {},
            "dimension_scores": {},
            "previous_tier": "Managed",
            "current_tier": "Defined",
        }
        earned = evaluate_badges(team_data)
        badge_ids = [b["id"] for b in earned]
        assert "tier_up" in badge_ids

    def test_tier_down_not_earned(self):
        team_data = {
            "team_id": "t1",
            "metrics": {},
            "score_history": [],
            "dora_tiers": {},
            "dimension_scores": {},
            "previous_tier": "Defined",
            "current_tier": "Managed",
        }
        earned = evaluate_badges(team_data)
        badge_ids = [b["id"] for b in earned]
        assert "tier_up" not in badge_ids

    def test_consistency_king_streak(self):
        team_data = {
            "team_id": "t1",
            "metrics": {},
            "score_history": [
                {"period": "2024-W01", "score": 50},
                {"period": "2024-W02", "score": 55},
                {"period": "2024-W03", "score": 60},
            ],
            "dora_tiers": {},
            "dimension_scores": {},
            "previous_tier": None,
            "current_tier": "Managed",
        }
        earned = evaluate_badges(team_data)
        badge_ids = [b["id"] for b in earned]
        assert "consistency_king" in badge_ids

    def test_empty_team_data(self):
        team_data = {
            "team_id": "t1",
            "metrics": {},
            "score_history": [],
            "dora_tiers": {},
            "dimension_scores": {},
            "previous_tier": None,
            "current_tier": "Ad Hoc",
        }
        earned = evaluate_badges(team_data)
        assert isinstance(earned, list)


class TestGetAllBadges:
    def test_returns_all(self):
        badges = get_all_badges()
        assert len(badges) == len(BADGE_DEFINITIONS)

    def test_no_criteria_type_exposed(self):
        badges = get_all_badges()
        for b in badges:
            assert "criteria_type" not in b
