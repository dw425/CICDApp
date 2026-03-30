"""Impact-Effort Matrix — Scatter plot quadrant chart for recommendations."""

import random
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

# Axis boundaries
X_MIN, X_MAX = 0.5, 3.5
Y_MIN, Y_MAX = 0.5, 2.5
X_MID = 2.0   # divider between low-effort and high-effort
Y_MID = 1.5   # divider between low-impact and high-impact


def create_impact_effort_matrix(
    classified: dict,
    height: int = 400,
) -> dcc.Graph:
    """Create a scatter plot showing recommendations on an Impact x Effort matrix."""
    fig = go.Figure()

    # Collect all items — position shows quadrant, color gradient shows expected improvement
    all_x, all_y, all_text, all_improvement, all_custom = [], [], [], [], []
    for quadrant in QUADRANT_LABELS:
        for item in classified.get(quadrant, []):
            effort = EFFORT_MAP.get(item.get("effort", "medium"), 2)
            impact = IMPACT_MAP.get(item.get("impact", "low"), 1)
            random.seed(hash(item.get("id", "")))
            jx = effort + (random.random() - 0.5) * 0.6
            jy = impact + (random.random() - 0.5) * 0.35
            all_x.append(jx)
            all_y.append(jy)
            all_text.append(item.get("title", ""))
            all_improvement.append(item.get("expected_score_improvement", 0))
            all_custom.append([
                item.get("impact", ""), item.get("effort", ""),
                item.get("expected_score_improvement", 0), quadrant.replace("_", " ").title(),
            ])

    if all_x:
        fig.add_trace(go.Scatter(
            x=all_x,
            y=all_y,
            mode="markers",
            name="Recommendations",
            showlegend=False,
            marker=dict(
                color=all_improvement,
                colorscale=[[0, "#1E3A5F"], [0.5, "#4B7BF5"], [1, "#34D399"]],
                cmin=0,
                cmax=max(all_improvement) if all_improvement else 25,
                size=16,
                opacity=0.9,
                line=dict(width=1.5, color="#0D1117"),
                colorbar=dict(
                    title=dict(text="Score<br>Impact", font=dict(color="#8B949E", size=11)),
                    tickfont=dict(color="#8B949E", size=10),
                    thickness=12,
                    len=0.7,
                    bgcolor="rgba(0,0,0,0)",
                    borderwidth=0,
                    ticksuffix=" pts",
                ),
            ),
            text=all_text,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Quadrant: %{customdata[3]}<br>"
                "Impact: %{customdata[0]}<br>"
                "Effort: %{customdata[1]}<br>"
                "Expected: +%{customdata[2]} pts"
                "<extra></extra>"
            ),
            customdata=all_custom,
        ))

    # Quadrant background shading
    fig.add_shape(type="rect", x0=X_MIN, y0=Y_MID, x1=X_MID, y1=Y_MAX,
                  fillcolor="rgba(52,211,153,0.07)", line=dict(width=0), layer="below")
    fig.add_shape(type="rect", x0=X_MID, y0=Y_MID, x1=X_MAX, y1=Y_MAX,
                  fillcolor="rgba(75,123,245,0.07)", line=dict(width=0), layer="below")
    fig.add_shape(type="rect", x0=X_MIN, y0=Y_MIN, x1=X_MID, y1=Y_MID,
                  fillcolor="rgba(251,191,36,0.07)", line=dict(width=0), layer="below")
    fig.add_shape(type="rect", x0=X_MID, y0=Y_MIN, x1=X_MAX, y1=Y_MID,
                  fillcolor="rgba(139,148,158,0.07)", line=dict(width=0), layer="below")

    # Dividing lines
    fig.add_shape(type="line", x0=X_MID, y0=Y_MIN, x1=X_MID, y1=Y_MAX,
                  line=dict(color="rgba(139,148,158,0.3)", width=1, dash="dot"))
    fig.add_shape(type="line", x0=X_MIN, y0=Y_MID, x1=X_MAX, y1=Y_MID,
                  line=dict(color="rgba(139,148,158,0.3)", width=1, dash="dot"))

    # Quadrant labels in corners
    annotations = [
        dict(x=X_MIN + 0.1, y=Y_MAX - 0.05, text="Quick Wins",
             font=dict(color="rgba(52,211,153,0.6)", size=12), xanchor="left", yanchor="top"),
        dict(x=X_MAX - 0.1, y=Y_MAX - 0.05, text="Strategic",
             font=dict(color="rgba(75,123,245,0.6)", size=12), xanchor="right", yanchor="top"),
        dict(x=X_MIN + 0.1, y=Y_MIN + 0.05, text="Fill-Ins",
             font=dict(color="rgba(251,191,36,0.6)", size=12), xanchor="left", yanchor="bottom"),
        dict(x=X_MAX - 0.1, y=Y_MIN + 0.05, text="Deprioritize",
             font=dict(color="rgba(139,148,158,0.6)", size=12), xanchor="right", yanchor="bottom"),
    ]
    for a in annotations:
        a["showarrow"] = False

    fig.update_layout(
        xaxis=dict(
            title="Effort",
            tickvals=[1, 2, 3],
            ticktext=["Low", "Medium", "High"],
            range=[X_MIN, X_MAX],
            showgrid=False,
            zeroline=False,
            tickfont=dict(color="#8B949E"),
            title_font=dict(color="#8B949E"),
        ),
        yaxis=dict(
            title="Impact",
            tickvals=[1, 2],
            ticktext=["Low", "High"],
            range=[Y_MIN, Y_MAX],
            showgrid=False,
            zeroline=False,
            tickfont=dict(color="#8B949E"),
            title_font=dict(color="#8B949E"),
        ),
        showlegend=False,
        annotations=annotations,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=80, t=20, b=60),
        height=height,
    )

    return dcc.Graph(
        figure=fig,
        config={"displayModeBar": False},
        style={"width": "100%"},
    )
