"""Tests for Leaderboard Engine."""

import pytest
from gamification.leaderboard import build_leaderboard, get_highlights


@pytest.fixture
def sample_teams():
    return [
        {"team_id": "t1", "team_name": "Alpha", "composite_score": 85, "maturity_tier": "Measured",
         "previous_score": 80, "badges_earned": [{"id": "speed_demon"}], "golden_path_adoption": 90},
        {"team_id": "t2", "team_name": "Beta", "composite_score": 65, "maturity_tier": "Defined",
         "previous_score": 70, "badges_earned": [], "golden_path_adoption": 75},
        {"team_id": "t3", "team_name": "Gamma", "composite_score": 35, "maturity_tier": "Ad Hoc",
         "previous_score": 30, "badges_earned": [], "golden_path_adoption": 20},
    ]


class TestBuildLeaderboard:
    def test_ranking_order(self, sample_teams):
        lb = build_leaderboard(sample_teams)
        assert lb[0]["rank"] == 1
        assert lb[0]["team_name"] == "Alpha"
        assert lb[1]["rank"] == 2
        assert lb[2]["rank"] == 3

    def test_movement_up(self, sample_teams):
        lb = build_leaderboard(sample_teams)
        alpha = lb[0]
        assert alpha["movement"] == "up"  # 85 - 80 = 5 > 2

    def test_movement_down(self, sample_teams):
        lb = build_leaderboard(sample_teams)
        beta = lb[1]
        assert beta["movement"] == "down"  # 65 - 70 = -5 < -2

    def test_movement_new(self):
        teams = [{"team_id": "t1", "team_name": "New Team", "composite_score": 50}]
        lb = build_leaderboard(teams)
        assert lb[0]["movement"] == "new"

    def test_empty_input(self):
        lb = build_leaderboard([])
        assert lb == []

    def test_badges_count(self, sample_teams):
        lb = build_leaderboard(sample_teams)
        assert lb[0]["badges_count"] == 1
        assert lb[1]["badges_count"] == 0


class TestGetHighlights:
    def test_top_team(self, sample_teams):
        lb = build_leaderboard(sample_teams)
        highlights = get_highlights(lb)
        assert highlights["top_team"]["team_name"] == "Alpha"

    def test_most_improved(self, sample_teams):
        lb = build_leaderboard(sample_teams)
        highlights = get_highlights(lb)
        assert highlights["most_improved"]["team_name"] in ("Alpha", "Gamma")

    def test_needs_attention(self, sample_teams):
        lb = build_leaderboard(sample_teams)
        highlights = get_highlights(lb)
        assert len(highlights["needs_attention"]) == 1
        assert highlights["needs_attention"][0]["team_name"] == "Gamma"

    def test_empty_leaderboard(self):
        highlights = get_highlights([])
        assert highlights["top_team"] is None
        assert highlights["most_improved"] is None
