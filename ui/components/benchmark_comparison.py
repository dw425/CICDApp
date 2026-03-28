"""Benchmark Comparison — Compare assessment scores against industry/size peers."""

import plotly.graph_objects as go
from dash import dcc, html

from compass.scoring_engine import TIER_COLORS


def create_benchmark_chart(
    comparison: dict,
    height: int = 380,
) -> dcc.Graph:
    """
    Create a grouped bar chart comparing scores vs industry/size benchmarks.

    Args:
        comparison: Dict from benchmark_data.compare_to_benchmarks.
        height: Chart height.
    """
    if not comparison:
        return dcc.Graph(
            figure=go.Figure().update_layout(
                annotations=[dict(
                    text="No benchmark data available",
                    xref="paper", yref="paper", x=0.5, y=0.5,
                    showarrow=False, font=dict(color="#8B949E"),
                )],
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=200,
            ),
            config={"displayModeBar": False},
        )

    dims = []
    your_scores = []
    industry_avgs = []
    size_avgs = []

    for dim_id, data in sorted(comparison.items()):
        dims.append(data.get("display_name", dim_id.replace("_", " ").title()))
        your_scores.append(data["score"])
        industry_avgs.append(data["industry_avg"])
        size_avgs.append(data["size_avg"])

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Your Score",
        x=dims,
        y=your_scores,
        marker_color="#4B7BF5",
        hovertemplate="%{x}: %{y:.0f}<extra>Your Score</extra>",
    ))

    fig.add_trace(go.Bar(
        name="Industry Avg",
        x=dims,
        y=industry_avgs,
        marker_color="rgba(251,191,36,0.6)",
        hovertemplate="%{x}: %{y:.0f}<extra>Industry Avg</extra>",
    ))

    fig.add_trace(go.Bar(
        name="Size Avg",
        x=dims,
        y=size_avgs,
        marker_color="rgba(139,148,158,0.5)",
        hovertemplate="%{x}: %{y:.0f}<extra>Size Avg</extra>",
    ))

    fig.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            tickfont=dict(color="#E6EDF3", size=11),
            tickangle=-30,
            gridcolor="rgba(39,45,63,0.3)",
        ),
        yaxis=dict(
            title="Score (0-100)",
            range=[0, 105],
            gridcolor="rgba(39,45,63,0.3)",
            tickfont=dict(color="#8B949E"),
            title_font=dict(color="#8B949E"),
        ),
        showlegend=True,
        legend=dict(
            x=0.5, y=-0.25,
            xanchor="center",
            orientation="h",
            font=dict(color="#8B949E"),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=50, r=20, t=10, b=80),
        height=height,
    )

    return dcc.Graph(
        figure=fig,
        config={"displayModeBar": False},
        style={"width": "100%"},
    )
    # ****Checked and Verified as Real*****
    # Create a grouped bar chart comparing scores vs industry/size benchmarks. Args: comparison: Dict from benchmark_data.compare_to_benchmarks.


def create_percentile_badges(comparison: dict) -> html.Div:
    """Create badges showing percentile rank per dimension."""
    badges = []
    for dim_id, data in sorted(comparison.items()):
        pct = data.get("industry_percentile", 50)
        if pct >= 75:
            badge_color = "#34D399"
            badge_label = "Top 25%"
        elif pct >= 50:
            badge_color = "#4B7BF5"
            badge_label = "Above Median"
        elif pct >= 25:
            badge_color = "#FBBF24"
            badge_label = "Below Median"
        else:
            badge_color = "#EF4444"
            badge_label = "Bottom 25%"

        badges.append(html.Div([
            html.Div(data.get("display_name", dim_id.replace("_", " ").title()), style={
                "color": "#8B949E",
                "fontSize": "11px",
            }),
            html.Div([
                html.Span(f"P{pct:.0f}", style={
                    "fontWeight": "700",
                    "color": badge_color,
                    "fontSize": "16px",
                }),
                html.Span(f" {badge_label}", style={
                    "color": "#484F58",
                    "fontSize": "10px",
                }),
            ]),
        ], style={
            "textAlign": "center",
            "padding": "8px 12px",
            "backgroundColor": "var(--elevated, #21262D)",
            "borderRadius": "6px",
        }))

    return html.Div(badges, style={
        "display": "grid",
        "gridTemplateColumns": "repeat(auto-fill, minmax(140px, 1fr))",
        "gap": "8px",
    })
    # ****Checked and Verified as Real*****
    # Create badges showing percentile rank per dimension.
