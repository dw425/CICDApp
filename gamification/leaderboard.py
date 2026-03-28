"""Leaderboard Engine — Ranks teams by maturity scores and badges."""

from datetime import datetime


def build_leaderboard(teams_data: list[dict]) -> list[dict]:
    """
    Build a ranked leaderboard from team maturity data.

    Args:
        teams_data: List of dicts with:
            team_id, team_name, composite_score, maturity_tier,
            previous_score, badges_earned, golden_path_adoption

    Returns: Sorted list with rank, movement indicators, and streaks.
    """
    # Sort by composite score descending
    sorted_teams = sorted(teams_data, key=lambda t: t.get("composite_score", 0), reverse=True)

    leaderboard = []
    for rank, team in enumerate(sorted_teams, 1):
        prev_score = team.get("previous_score")
        curr_score = team.get("composite_score", 0)

        if prev_score is not None:
            delta = curr_score - prev_score
            if delta > 2:
                movement = "up"
            elif delta < -2:
                movement = "down"
            else:
                movement = "stable"
        else:
            delta = 0
            movement = "new"

        leaderboard.append({
            "rank": rank,
            "team_id": team.get("team_id", ""),
            "team_name": team.get("team_name", ""),
            "composite_score": round(curr_score, 1),
            "maturity_tier": team.get("maturity_tier", ""),
            "delta": round(delta, 1),
            "movement": movement,
            "badges_count": len(team.get("badges_earned", [])),
            "badges": team.get("badges_earned", []),
            "golden_path_pct": team.get("golden_path_adoption", 0),
            "streak_weeks": team.get("improvement_streak", 0),
        })

    return leaderboard


def get_highlights(leaderboard: list[dict]) -> dict:
    """
    Extract leaderboard highlights for the executive summary.

    Returns: {
        "top_team": dict,
        "most_improved": dict,
        "needs_attention": list[dict],
        "new_badges": list[dict],
    }
    """
    if not leaderboard:
        return {"top_team": None, "most_improved": None, "needs_attention": [], "new_badges": []}

    top_team = leaderboard[0] if leaderboard else None

    most_improved = max(leaderboard, key=lambda t: t.get("delta", 0)) if leaderboard else None
    if most_improved and most_improved.get("delta", 0) <= 0:
        most_improved = None

    needs_attention = [t for t in leaderboard if t.get("composite_score", 100) < 40]

    new_badges = [t for t in leaderboard if t.get("badges_count", 0) > 0]

    return {
        "top_team": top_team,
        "most_improved": most_improved,
        "needs_attention": needs_attention[:5],
        "new_badges": new_badges[:5],
    }
