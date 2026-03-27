"""Traffic Light Cards — Dimension score cards with L1-L5 color coding."""

from dash import html

from compass.scoring_engine import TIER_COLORS


DIMENSION_ICONS = {
    "build_integration": "fas fa-hammer",
    "testing_quality": "fas fa-shield-alt",
    "deployment_release": "fas fa-rocket",
    "security_compliance": "fas fa-lock",
    "observability": "fas fa-eye",
    "iac_configuration": "fas fa-server",
    "artifact_management": "fas fa-box",
    "developer_experience": "fas fa-code",
    "pipeline_governance": "fas fa-code-branch",
}


def create_traffic_light_card(
    dim_id: str,
    display_name: str,
    score: float,
    level: int,
    label: str,
    benchmark_avg: float = None,
) -> html.Div:
    """
    Create a single dimension traffic light card.

    Shows dimension name, score, level badge, and optional benchmark comparison.
    """
    color = TIER_COLORS.get(level, "#888")
    icon = DIMENSION_ICONS.get(dim_id, "fas fa-circle")
    vs_bench = None
    if benchmark_avg is not None:
        diff = score - benchmark_avg
        if diff > 5:
            vs_bench = html.Span(
                f"+{diff:.0f} vs avg",
                style={"color": "#34D399", "fontSize": "11px"},
            )
        elif diff < -5:
            vs_bench = html.Span(
                f"{diff:.0f} vs avg",
                style={"color": "#F87171", "fontSize": "11px"},
            )
        else:
            vs_bench = html.Span(
                "At avg",
                style={"color": "#8B949E", "fontSize": "11px"},
            )

    return html.Div([
        html.Div([
            html.Div([
                html.I(className=icon, style={"color": color, "fontSize": "16px"}),
                html.Span(display_name, style={
                    "color": "#E6EDF3",
                    "fontSize": "13px",
                    "fontWeight": "600",
                }),
            ], style={"display": "flex", "alignItems": "center", "gap": "8px"}),
            html.Span(f"L{level}", style={
                "display": "inline-block",
                "padding": "1px 8px",
                "borderRadius": "4px",
                "backgroundColor": color,
                "color": "#fff",
                "fontWeight": "700",
                "fontSize": "11px",
            }),
        ], style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
        }),
        html.Div([
            html.Div([
                html.Span(f"{score:.0f}", style={
                    "color": "#E6EDF3",
                    "fontSize": "28px",
                    "fontWeight": "700",
                    "lineHeight": "1",
                }),
                html.Span("/100", style={
                    "color": "#484F58",
                    "fontSize": "14px",
                    "marginLeft": "2px",
                }),
            ]),
            html.Div(label, style={"color": "#8B949E", "fontSize": "11px"}),
            vs_bench if vs_bench else html.Div(),
        ], style={"marginTop": "10px"}),
        html.Div(style={
            "height": "3px",
            "backgroundColor": "rgba(39,45,63,0.5)",
            "borderRadius": "2px",
            "marginTop": "10px",
            "position": "relative",
            "overflow": "hidden",
        }, children=[
            html.Div(style={
                "height": "100%",
                "width": f"{min(score, 100)}%",
                "backgroundColor": color,
                "borderRadius": "2px",
                "transition": "width 0.5s ease",
            }),
        ]),
    ], style={
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "8px",
        "border": f"1px solid {color}22",
        "padding": "16px",
        "minWidth": "200px",
    })


def create_traffic_light_grid(dimension_scores: dict, benchmarks: dict = None) -> html.Div:
    """Create a grid of traffic light cards for all dimensions."""
    cards = []
    sorted_dims = sorted(
        [(k, v) for k, v in dimension_scores.items() if "." not in k],
        key=lambda x: x[1].get("raw_score", x[1].get("score", 0)),
    )

    for dim_id, score_data in sorted_dims:
        score = score_data.get("raw_score", score_data.get("score", 0))
        level = score_data.get("level", 1)
        label = score_data.get("label", "Initial")
        display_name = score_data.get("display_name", dim_id.replace("_", " ").title())
        bench_avg = None
        if benchmarks:
            bench_data = benchmarks.get(dim_id, {})
            bench_avg = bench_data.get("avg")

        cards.append(create_traffic_light_card(
            dim_id, display_name, score, level, label, bench_avg
        ))

    return html.Div(cards, style={
        "display": "grid",
        "gridTemplateColumns": "repeat(auto-fill, minmax(220px, 1fr))",
        "gap": "12px",
    })
