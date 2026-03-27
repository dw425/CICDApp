"""Maturity Gauge — Overall composite score gauge visualization."""

import plotly.graph_objects as go
from dash import dcc, html

from compass.scoring_engine import TIER_COLORS, TIER_LABELS


def create_maturity_gauge(
    score: float,
    level: int,
    label: str,
    height: int = 260,
) -> html.Div:
    """
    Create a gauge chart showing the overall maturity score.

    Args:
        score: Composite score 0-100.
        level: Maturity level 1-5.
        label: Maturity label (Initial/Managed/Defined/Optimized/Elite).
        height: Chart height in pixels.
    """
    color = TIER_COLORS.get(level, "#888")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(
            font=dict(size=42, color="#E6EDF3", family="DM Sans"),
            suffix="",
        ),
        gauge=dict(
            axis=dict(
                range=[0, 100],
                tickwidth=1,
                tickcolor="#484F58",
                tickvals=[0, 20, 40, 60, 80, 100],
                ticktext=["0", "20", "40", "60", "80", "100"],
                tickfont=dict(color="#484F58", size=10),
            ),
            bar=dict(color=color, thickness=0.3),
            bgcolor="rgba(33,38,45,0.5)",
            borderwidth=0,
            steps=[
                {"range": [0, 20], "color": "rgba(239,68,68,0.1)"},
                {"range": [20, 40], "color": "rgba(249,115,22,0.1)"},
                {"range": [40, 60], "color": "rgba(234,179,8,0.1)"},
                {"range": [60, 80], "color": "rgba(34,197,94,0.1)"},
                {"range": [80, 100], "color": "rgba(59,130,246,0.1)"},
            ],
            threshold=dict(
                line=dict(color=color, width=3),
                thickness=0.8,
                value=score,
            ),
        ),
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=30, r=30, t=30, b=10),
        height=height,
    )

    return html.Div([
        dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"width": "100%"}),
        html.Div([
            html.Span(f"L{level}", style={
                "display": "inline-block",
                "padding": "2px 10px",
                "borderRadius": "4px",
                "backgroundColor": color,
                "color": "#fff",
                "fontWeight": "700",
                "fontSize": "14px",
                "marginRight": "8px",
            }),
            html.Span(label, style={
                "color": "#E6EDF3",
                "fontSize": "16px",
                "fontWeight": "600",
            }),
        ], style={"textAlign": "center", "marginTop": "-10px"}),
    ])
