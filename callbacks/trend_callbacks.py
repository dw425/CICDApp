"""Trend Analysis Callbacks - Multi-line trends, deltas, tier distribution,
and domain small multiples."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import html, Input, Output, no_update

from ui.theme import (
    SURFACE, TEXT, TEXT2, TEXT3, BORDER, ACCENT, GREEN, YELLOW, RED,
    PURPLE, CYAN, CHART_COLORS, TIER_COLORS, get_tier,
)


# Domain display labels
def _hex_to_rgba(hex_color, alpha=0.6):
    """Convert a hex color like '#F87171' to 'rgba(248,113,113,0.6)'."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


DOMAIN_LABELS = {
    "golden_path": "Golden Path",
    "environment_promotion": "Env Promotion",
    "pipeline_reliability": "Pipeline Reliability",
    "data_quality": "Data Quality",
    "security_governance": "Security & Gov",
    "cost_efficiency": "Cost Efficiency",
}


def _empty_figure(message="No data available", height=300):
    """Return an empty themed figure with a centered message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=14, color=TEXT2),
    )
    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=height,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig


def _build_multi_line(trends, team_lookup):
    """Build multi-line chart of composite avg_score per team over time."""
    if trends.empty:
        return _empty_figure("No trend data available")

    fig = go.Figure()
    team_ids = sorted(trends["team_id"].unique())

    for i, team_id in enumerate(team_ids):
        team_data = trends[trends["team_id"] == team_id].sort_values("period_start")
        team_name = team_lookup.get(team_id, team_id)
        color = CHART_COLORS[i % len(CHART_COLORS)]

        fig.add_trace(go.Scatter(
            x=team_data["period_start"],
            y=team_data["avg_score"],
            mode="lines+markers",
            name=team_name,
            line=dict(color=color, width=2.5),
            marker=dict(color=color, size=7, line=dict(color=SURFACE, width=1)),
            hovertemplate=(
                f"<b>{team_name}</b><br>"
                "Week of %{{x}}<br>"
                "Score: %{{y:.1f}}<br>"
                "Range: %{{customdata[0]:.0f}}-%{{customdata[1]:.0f}}"
                "<extra></extra>"
            ),
            customdata=team_data[["min_score", "max_score"]].values,
        ))

    # Add tier boundary reference lines
    tier_boundaries = [(20, "Ad Hoc / Managed"), (40, "Managed / Defined"),
                       (60, "Defined / Measured"), (80, "Measured / Optimized")]
    for boundary, label in tier_boundaries:
        fig.add_hline(
            y=boundary,
            line_dash="dot",
            line_color=TEXT3,
            line_width=1,
            annotation_text=label,
            annotation_position="top right",
            annotation_font=dict(color=TEXT3, size=9),
        )

    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="DM Sans, Inter, system-ui, sans-serif", color=TEXT2),
        xaxis=dict(
            title=dict(text="Week", font=dict(color=TEXT2)),
            gridcolor=BORDER,
            tickfont=dict(color=TEXT2),
        ),
        yaxis=dict(
            title=dict(text="Composite Score", font=dict(color=TEXT2)),
            gridcolor=BORDER,
            tickfont=dict(color=TEXT2),
            range=[0, 100],
        ),
        legend=dict(
            font=dict(color=TEXT2, size=11),
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
        height=380,
        margin=dict(l=50, r=20, t=50, b=50),
        hovermode="x unified",
    )
    return fig


def _build_delta_bars(trends, team_lookup):
    """Build grouped bar chart of week-over-week deltas per team."""
    if trends.empty:
        return _empty_figure("No trend data available")

    # Use the latest period's delta for each team
    latest = trends.sort_values("period_start").groupby("team_id").last().reset_index()

    team_names = [team_lookup.get(tid, tid) for tid in latest["team_id"]]
    deltas = latest["delta"].values

    # Color bars: green for positive, red for negative
    colors = [GREEN if d >= 0 else RED for d in deltas]

    fig = go.Figure(go.Bar(
        x=team_names,
        y=deltas,
        marker=dict(
            color=colors,
            line=dict(color=[GREEN if d >= 0 else RED for d in deltas], width=1),
            opacity=0.85,
        ),
        text=[f"{d:+.1f}" for d in deltas],
        textposition="outside",
        textfont=dict(color=TEXT2, size=12),
        hovertemplate="<b>%{x}</b><br>Delta: %{y:+.1f}<extra></extra>",
    ))

    fig.add_hline(y=0, line_color=TEXT3, line_width=1)

    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="DM Sans, Inter, system-ui, sans-serif", color=TEXT2),
        xaxis=dict(
            tickfont=dict(color=TEXT2, size=11),
            gridcolor=BORDER,
        ),
        yaxis=dict(
            title=dict(text="Score Delta", font=dict(color=TEXT2)),
            gridcolor=BORDER,
            tickfont=dict(color=TEXT2),
        ),
        height=300,
        margin=dict(l=50, r=20, t=20, b=60),
        bargap=0.3,
    )
    return fig


def _build_tier_stacked(trends, team_lookup):
    """Build stacked area chart showing tier distribution over time."""
    if trends.empty:
        return _empty_figure("No trend data available")

    # For each period, classify each team's avg_score into a tier
    periods = sorted(trends["period_start"].unique())
    tier_names = ["Ad Hoc", "Managed", "Defined", "Measured", "Optimized"]

    tier_counts = {tier: [] for tier in tier_names}
    for period in periods:
        period_data = trends[trends["period_start"] == period]
        counts = {tier: 0 for tier in tier_names}
        for _, row in period_data.iterrows():
            tier = get_tier(row["avg_score"])
            counts[tier] += 1
        for tier in tier_names:
            tier_counts[tier].append(counts[tier])

    fig = go.Figure()
    for tier in tier_names:
        fig.add_trace(go.Scatter(
            x=periods,
            y=tier_counts[tier],
            mode="lines",
            name=tier,
            stackgroup="one",
            line=dict(width=0.5, color=TIER_COLORS[tier]),
            fillcolor=_hex_to_rgba(TIER_COLORS[tier], 0.6),
            hovertemplate=f"<b>{tier}</b><br>Week: %{{x}}<br>Teams: %{{y}}<extra></extra>",
        ))

    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="DM Sans, Inter, system-ui, sans-serif", color=TEXT2),
        xaxis=dict(
            tickfont=dict(color=TEXT2),
            gridcolor=BORDER,
        ),
        yaxis=dict(
            title=dict(text="Team Count", font=dict(color=TEXT2)),
            gridcolor=BORDER,
            tickfont=dict(color=TEXT2),
            dtick=1,
        ),
        legend=dict(
            font=dict(color=TEXT2, size=11),
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
        height=300,
        margin=dict(l=50, r=20, t=50, b=50),
        hovermode="x unified",
    )
    return fig


def _build_domain_small_multiples(scores, team_lookup):
    """Build small multiples subplot grid -- one subplot per domain showing
    each team's score as a horizontal bar."""
    if scores.empty:
        return _empty_figure("No score data available", height=500)

    domains = sorted(scores["domain"].unique())
    n_domains = len(domains)
    if n_domains == 0:
        return _empty_figure("No domains found", height=500)

    # Create subplot grid: 2 columns x ceil(n_domains/2) rows
    n_cols = 2
    n_rows = (n_domains + 1) // 2

    subplot_titles = [DOMAIN_LABELS.get(d, d.replace("_", " ").title()) for d in domains]
    fig = make_subplots(
        rows=n_rows,
        cols=n_cols,
        subplot_titles=subplot_titles,
        vertical_spacing=0.12,
        horizontal_spacing=0.15,
    )

    team_ids = sorted(scores["team_id"].unique())

    for idx, domain in enumerate(domains):
        row = (idx // n_cols) + 1
        col = (idx % n_cols) + 1

        domain_scores = scores[scores["domain"] == domain]

        team_names = []
        score_vals = []
        bar_colors = []
        for team_id in team_ids:
            team_domain = domain_scores[domain_scores["team_id"] == team_id]
            team_name = team_lookup.get(team_id, team_id)
            team_names.append(team_name)
            if not team_domain.empty:
                score_val = team_domain["raw_score"].mean()
            else:
                score_val = 0
            score_vals.append(score_val)
            bar_colors.append(CHART_COLORS[team_ids.tolist().index(team_id) % len(CHART_COLORS)] if hasattr(team_ids, 'tolist') else CHART_COLORS[list(team_ids).index(team_id) % len(CHART_COLORS)])

        fig.add_trace(
            go.Bar(
                y=team_names,
                x=score_vals,
                orientation="h",
                marker=dict(color=bar_colors, opacity=0.85),
                text=[f"{v:.0f}" for v in score_vals],
                textposition="auto",
                textfont=dict(color=TEXT, size=10),
                showlegend=False,
                hovertemplate="<b>%{y}</b><br>Score: %{x:.0f}<extra></extra>",
            ),
            row=row,
            col=col,
        )

    # Style all subplot axes
    fig.update_xaxes(
        range=[0, 100],
        gridcolor=BORDER,
        tickfont=dict(color=TEXT2, size=9),
    )
    fig.update_yaxes(
        tickfont=dict(color=TEXT2, size=10),
        gridcolor=BORDER,
    )

    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="DM Sans, Inter, system-ui, sans-serif", color=TEXT2),
        height=max(350, n_rows * 200),
        margin=dict(l=120, r=20, t=40, b=20),
        showlegend=False,
    )

    # Style subplot titles
    for annotation in fig["layout"]["annotations"]:
        annotation["font"] = dict(color=TEXT, size=12, family="DM Sans, Inter, system-ui, sans-serif")

    return fig


def register_callbacks(app):
    """Register Trend Analysis callbacks."""

    @app.callback(
        [
            Output("trend-multi-line", "figure"),
            Output("trend-delta-bars", "figure"),
            Output("trend-tier-stacked", "figure"),
            Output("trend-domain-small-multiples", "figure"),
        ],
        Input("current-page", "data"),
    )
    def update_trend_analysis(current_page):
        """Populate all Trend Analysis visuals."""
        if current_page != "trend":
            return [no_update] * 4

        try:
            from data_layer.queries.custom_tables import (
                get_teams,
                get_maturity_trends,
                get_maturity_scores,
            )

            teams = get_teams()
            team_lookup = dict(zip(teams["team_id"], teams["team_name"]))
            trends = get_maturity_trends(period_type="weekly")
            scores = get_maturity_scores(latest=True)

            multi_line = _build_multi_line(trends, team_lookup)
            delta_bars = _build_delta_bars(trends, team_lookup)
            tier_stacked = _build_tier_stacked(trends, team_lookup)
            domain_multiples = _build_domain_small_multiples(scores, team_lookup)

            return [multi_line, delta_bars, tier_stacked, domain_multiples]

        except Exception as e:
            err = _empty_figure(f"Error: {str(e)}")
            return [err, err, err, err]
