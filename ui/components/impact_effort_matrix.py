"""Impact-Effort Matrix — Scatter plot quadrant chart for recommendations."""

import plotly.graph_objects as go
from dash import dcc


EFFORT_MAP = {"low": 1, "medium": 2, "high": 3}
IMPACT_MAP = {"low": 1, "high": 2}

QUADRANT_LABELS = {
    "quick_wins": {"name": "Quick Wins", "color": "#34D399"},
    "strategic": {"name": "Strategic", "color": "#4B7BF5"},
    "fill_ins": {"name": "Fill-Ins", "color": "#FBBF24"},
    "deprioritize": {"name": "Deprioritize", "color": "#8B949E"},
}


def create_impact_effort_matrix(
    classified: dict,
    height: int = 380,
) -> dcc.Graph:
    """
    Create a scatter plot showing recommendations on an Impact x Effort matrix.

    Args:
        classified: Dict with keys quick_wins, strategic, fill_ins, deprioritize.
        height: Chart height in pixels.
    """
    fig = go.Figure()

    for quadrant, meta in QUADRANT_LABELS.items():
        items = classified.get(quadrant, [])
        if not items:
            continue

        x_vals = []
        y_vals = []
        texts = []
        sizes = []

        for item in items:
            effort = EFFORT_MAP.get(item.get("effort", "medium"), 2)
            impact = IMPACT_MAP.get(item.get("impact", "low"), 1)
            # Add jitter to avoid overlap
            import random
            random.seed(hash(item.get("id", "")))
            jx = effort + (random.random() - 0.5) * 0.4
            jy = impact + (random.random() - 0.5) * 0.3

            x_vals.append(jx)
            y_vals.append(jy)
            texts.append(item.get("title", ""))
            sizes.append(max(item.get("expected_score_improvement", 10), 8))

        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="markers+text",
            name=meta["name"],
            marker=dict(
                color=meta["color"],
                size=sizes,
                opacity=0.8,
                line=dict(width=1, color="#0D1117"),
            ),
            text=texts,
            textposition="top center",
            textfont=dict(color="#E6EDF3", size=9),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Impact: %{customdata[0]}<br>"
                "Effort: %{customdata[1]}<br>"
                "Expected: +%{customdata[2]} pts"
                "<extra></extra>"
            ),
            customdata=[
                [item.get("impact", ""), item.get("effort", ""), item.get("expected_score_improvement", 0)]
                for item in items
            ],
        ))

    # Quadrant shading
    fig.add_shape(type="rect", x0=0.3, y0=1.45, x1=1.8, y1=2.55,
                  fillcolor="rgba(52,211,153,0.05)", line=dict(width=0))
    fig.add_shape(type="rect", x0=1.8, y0=1.45, x1=3.7, y1=2.55,
                  fillcolor="rgba(75,123,245,0.05)", line=dict(width=0))
    fig.add_shape(type="rect", x0=0.3, y0=0.45, x1=1.8, y1=1.45,
                  fillcolor="rgba(251,191,36,0.05)", line=dict(width=0))
    fig.add_shape(type="rect", x0=1.8, y0=0.45, x1=3.7, y1=1.45,
                  fillcolor="rgba(139,148,158,0.05)", line=dict(width=0))

    # Quadrant labels
    annotations = [
        dict(x=1.0, y=2.45, text="Quick Wins", font=dict(color="#34D39980", size=13)),
        dict(x=2.8, y=2.45, text="Strategic", font=dict(color="#4B7BF580", size=13)),
        dict(x=1.0, y=0.55, text="Fill-Ins", font=dict(color="#FBBF2480", size=13)),
        dict(x=2.8, y=0.55, text="Deprioritize", font=dict(color="#8B949E80", size=13)),
    ]
    for a in annotations:
        a.update(showarrow=False, xanchor="center")

    fig.update_layout(
        xaxis=dict(
            title="Effort",
            tickvals=[1, 2, 3],
            ticktext=["Low", "Medium", "High"],
            range=[0.3, 3.7],
            gridcolor="rgba(39,45,63,0.3)",
            tickfont=dict(color="#8B949E"),
            titlefont=dict(color="#8B949E"),
        ),
        yaxis=dict(
            title="Impact",
            tickvals=[1, 2],
            ticktext=["Low", "High"],
            range=[0.4, 2.6],
            gridcolor="rgba(39,45,63,0.3)",
            tickfont=dict(color="#8B949E"),
            titlefont=dict(color="#8B949E"),
        ),
        showlegend=True,
        legend=dict(
            x=0.5, y=-0.2,
            xanchor="center",
            orientation="h",
            font=dict(color="#8B949E"),
            bgcolor="rgba(0,0,0,0)",
        ),
        annotations=annotations,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=20, t=20, b=60),
        height=height,
    )

    return dcc.Graph(
        figure=fig,
        config={"displayModeBar": False},
        style={"width": "100%"},
    )
