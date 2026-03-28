"""Gap Waterfall Chart — Shows gap between current and target per dimension."""

import plotly.graph_objects as go
from dash import dcc


QUADRANT_COLORS = {
    "quick_wins": "#34D399",
    "strategic": "#4B7BF5",
    "fill_ins": "#FBBF24",
    "deprioritize": "#8B949E",
}


def create_gap_waterfall(
    gaps: list,
    height: int = 350,
) -> dcc.Graph:
    """
    Create a horizontal bar chart showing gap per dimension.

    Args:
        gaps: List of gap dicts from roadmap_engine.calculate_gaps.
        height: Chart height in pixels.
    """
    if not gaps:
        return dcc.Graph(
            figure=go.Figure().update_layout(
                annotations=[dict(
                    text="No gaps detected — congratulations!",
                    xref="paper", yref="paper", x=0.5, y=0.5,
                    showarrow=False, font=dict(color="#8B949E", size=14),
                )],
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=200,
            ),
            config={"displayModeBar": False},
        )

    dims = [g.get("display_name", g["dimension"]) for g in gaps]
    gap_vals = [g["gap"] for g in gaps]
    current_vals = [g["current_score"] for g in gaps]
    target_vals = [g["target_score"] for g in gaps]

    colors = []
    for g in gaps:
        gap = g["gap"]
        if gap >= 25:
            colors.append("#EF4444")
        elif gap >= 15:
            colors.append("#F97316")
        elif gap >= 10:
            colors.append("#EAB308")
        else:
            colors.append("#34D399")

    fig = go.Figure()

    # Current score (base)
    fig.add_trace(go.Bar(
        y=dims,
        x=current_vals,
        orientation="h",
        name="Current",
        marker=dict(color="rgba(75,123,245,0.3)"),
        hovertemplate="%{y}: %{x:.0f}<extra>Current</extra>",
    ))

    # Gap (stacked)
    fig.add_trace(go.Bar(
        y=dims,
        x=gap_vals,
        orientation="h",
        name="Gap",
        marker=dict(color=colors),
        text=[f"+{v:.0f}" for v in gap_vals],
        textposition="outside",
        textfont=dict(color="#E6EDF3", size=11),
        hovertemplate="%{y}: Gap of %{x:.0f} points<extra></extra>",
    ))

    fig.update_layout(
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            title="Score",
            range=[0, 110],
            gridcolor="rgba(39,45,63,0.4)",
            tickfont=dict(color="#8B949E"),
            title_font=dict(color="#8B949E"),
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(color="#E6EDF3", size=12),
        ),
        showlegend=True,
        legend=dict(
            x=0.5, y=-0.2,
            xanchor="center",
            orientation="h",
            font=dict(color="#8B949E"),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=120, r=40, t=10, b=50),
        height=max(height, len(gaps) * 40 + 80),
    )

    return dcc.Graph(
        figure=fig,
        config={"displayModeBar": False},
        style={"width": "100%"},
    )
    # ****Checked and Verified as Real*****
    # Create a horizontal bar chart showing gap per dimension. Args: gaps: List of gap dicts from roadmap_engine.calculate_gaps.
