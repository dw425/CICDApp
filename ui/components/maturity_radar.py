"""Maturity Radar Chart — 9-axis radar displaying all COMPASS dimensions."""

import plotly.graph_objects as go
from dash import dcc


DIMENSION_ORDER = [
    "build_integration",
    "testing_quality",
    "deployment_release",
    "security_compliance",
    "observability",
    "iac_configuration",
    "artifact_management",
    "developer_experience",
    "pipeline_governance",
]

DIMENSION_SHORT_LABELS = {
    "build_integration": "Build",
    "testing_quality": "Testing",
    "deployment_release": "Deploy",
    "security_compliance": "Security",
    "observability": "Observe",
    "iac_configuration": "IaC",
    "artifact_management": "Artifacts",
    "developer_experience": "Dev XP",
    "pipeline_governance": "Governance",
}


def create_maturity_radar(
    dimension_scores: dict,
    target_scores: dict = None,
    benchmark_scores: dict = None,
    height: int = 420,
) -> dcc.Graph:
    """
    Create a 9-axis radar chart for COMPASS dimension scores.

    Args:
        dimension_scores: {dim_id: {"raw_score": float, "score": float, ...}}
        target_scores: Optional {dim_id: target_score} for overlay
        benchmark_scores: Optional {dim_id: {"avg": float}} for overlay
        height: Chart height in pixels
    """
    categories = []
    current_values = []
    target_values = []
    bench_values = []

    for dim in DIMENSION_ORDER:
        label = DIMENSION_SHORT_LABELS.get(dim, dim)
        categories.append(label)

        score_data = dimension_scores.get(dim, {})
        score = score_data.get("raw_score", score_data.get("score", 0))
        current_values.append(score)

        if target_scores:
            target_values.append(target_scores.get(dim, score + 25))
        if benchmark_scores:
            bench_data = benchmark_scores.get(dim, {})
            bench_values.append(bench_data.get("avg", bench_data.get("median", 40)))

    # Close the polygon
    categories.append(categories[0])
    current_values.append(current_values[0])
    if target_values:
        target_values.append(target_values[0])
    if bench_values:
        bench_values.append(bench_values[0])

    fig = go.Figure()

    # Current scores
    fig.add_trace(go.Scatterpolar(
        r=current_values,
        theta=categories,
        fill="toself",
        fillcolor="rgba(75, 123, 245, 0.15)",
        line=dict(color="#4B7BF5", width=2),
        name="Current",
        hovertemplate="%{theta}: %{r:.0f}/100<extra></extra>",
    ))

    # Target overlay
    if target_values:
        fig.add_trace(go.Scatterpolar(
            r=target_values,
            theta=categories,
            fill=None,
            line=dict(color="#34D399", width=2, dash="dash"),
            name="Target",
            hovertemplate="%{theta}: %{r:.0f}/100<extra></extra>",
        ))

    # Benchmark overlay
    if bench_values:
        fig.add_trace(go.Scatterpolar(
            r=bench_values,
            theta=categories,
            fill=None,
            line=dict(color="#FBBF24", width=1.5, dash="dot"),
            name="Benchmark",
            hovertemplate="%{theta}: %{r:.0f}/100<extra></extra>",
        ))

    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[20, 40, 60, 80, 100],
                ticktext=["L1", "L2", "L3", "L4", "L5"],
                tickfont=dict(color="#484F58", size=10),
                gridcolor="rgba(39,45,63,0.6)",
                linecolor="rgba(39,45,63,0.3)",
            ),
            angularaxis=dict(
                tickfont=dict(color="#E6EDF3", size=11),
                gridcolor="rgba(39,45,63,0.4)",
                linecolor="rgba(39,45,63,0.3)",
            ),
        ),
        showlegend=True,
        legend=dict(
            x=0.5, y=-0.15,
            xanchor="center",
            orientation="h",
            font=dict(color="#8B949E", size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=60, t=20, b=60),
        height=height,
    )

    return dcc.Graph(
        figure=fig,
        config={"displayModeBar": False},
        style={"width": "100%"},
    )
