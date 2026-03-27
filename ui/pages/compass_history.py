"""Pipeline Compass Assessment History Page."""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_layout():
    """Create the assessment history page layout."""
    return html.Div([
        # Header
        html.Div([
            html.Div([
                html.I(className="fas fa-history", style={"color": "#A78BFA", "fontSize": "20px"}),
                html.Div([
                    html.Div("Assessment History", style={
                        "fontSize": "18px", "fontWeight": "700", "color": "#E6EDF3",
                    }),
                    html.Div("Track maturity progress across assessments", style={
                        "fontSize": "12px", "color": "#8B949E",
                    }),
                ]),
            ], style={"display": "flex", "alignItems": "center", "gap": "12px"}),
        ], style={"marginBottom": "20px"}),

        # Content (populated by callback)
        html.Div(id="compass-history-content"),
    ], style={"padding": "24px"})


def create_history_dashboard(assessments: list, organizations: dict) -> html.Div:
    """Build the history view from completed assessments."""
    if not assessments:
        return html.Div([
            html.I(className="fas fa-history", style={
                "fontSize": "48px", "color": "#272D3F", "marginBottom": "16px",
            }),
            html.Div("No Completed Assessments", style={
                "color": "#8B949E", "fontSize": "16px", "fontWeight": "600",
            }),
            html.Div(
                "Complete your first assessment to start tracking progress.",
                style={"color": "#484F58", "fontSize": "13px", "marginTop": "8px"},
            ),
        ], style={"textAlign": "center", "padding": "80px 40px"})

    # Summary KPIs
    latest = assessments[0] if assessments else {}
    latest_composite = latest.get("composite", {})
    latest_score = latest_composite.get("overall_score", 0)
    latest_level = latest_composite.get("overall_level", 1)
    latest_label = latest_composite.get("overall_label", "Initial")

    trend_val = ""
    trend_color = "#8B949E"
    if len(assessments) >= 2:
        prev_score = assessments[1].get("composite", {}).get("overall_score", 0)
        diff = latest_score - prev_score
        if diff > 0:
            trend_val = f"+{diff:.0f}"
            trend_color = "#34D399"
        elif diff < 0:
            trend_val = f"{diff:.0f}"
            trend_color = "#EF4444"
        else:
            trend_val = "0"

    kpi_row = html.Div([
        _kpi_card("Total Assessments", str(len(assessments)), "completed", "#4B7BF5"),
        _kpi_card("Latest Score", f"{latest_score:.0f}", f"L{latest_level} — {latest_label}", latest_composite.get("overall_color", "#4B7BF5")),
        _kpi_card("Trend", trend_val, "vs previous" if trend_val else "N/A", trend_color),
        _kpi_card("Organizations", str(len(organizations)), "assessed", "#A78BFA"),
    ], style={
        "display": "grid",
        "gridTemplateColumns": "repeat(4, 1fr)",
        "gap": "12px",
        "marginBottom": "20px",
    })

    # Trend chart
    if len(assessments) >= 2:
        import plotly.graph_objects as go
        dates = []
        scores = []
        for a in reversed(assessments):
            comp = a.get("composite", {})
            dates.append(a.get("completed_at", a.get("created_at", ""))[:10])
            scores.append(comp.get("overall_score", 0))

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=scores,
            mode="lines+markers",
            line=dict(color="#4B7BF5", width=2),
            marker=dict(size=8, color="#4B7BF5"),
            hovertemplate="%{x}: %{y:.0f}<extra></extra>",
        ))
        # Tier bands
        for low, high, color, alpha in [(0, 20, "#EF4444", 0.05), (20, 40, "#F97316", 0.05),
                                         (40, 60, "#EAB308", 0.05), (60, 80, "#22C55E", 0.05),
                                         (80, 100, "#3B82F6", 0.05)]:
            fig.add_hrect(y0=low, y1=high, fillcolor=f"rgba({','.join(str(int(color[i:i+2], 16)) for i in (1, 3, 5))},{alpha})", line_width=0)

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="rgba(39,45,63,0.3)", tickfont=dict(color="#8B949E")),
            yaxis=dict(title="Score", range=[0, 105], gridcolor="rgba(39,45,63,0.3)", tickfont=dict(color="#8B949E"), titlefont=dict(color="#8B949E")),
            margin=dict(l=50, r=20, t=10, b=40),
            height=250,
        )
        trend_chart = html.Div([
            html.Div("Score Trend", style={"color": "#E6EDF3", "fontSize": "14px", "fontWeight": "700", "marginBottom": "12px"}),
            dcc.Graph(figure=fig, config={"displayModeBar": False}),
        ], style={
            "backgroundColor": "var(--surface, #161B22)",
            "borderRadius": "8px",
            "padding": "20px",
            "border": "1px solid var(--border, #272D3F)",
            "marginBottom": "12px",
        })
    else:
        trend_chart = html.Div()

    # Assessment list
    rows = []
    for a in assessments:
        comp = a.get("composite", {})
        org = organizations.get(a.get("org_id", ""), {})
        score = comp.get("overall_score", 0)
        level = comp.get("overall_level", 1)
        label = comp.get("overall_label", "Initial")
        color = comp.get("overall_color", "#888")

        rows.append(html.Div([
            html.Div([
                html.Span(f"L{level}", style={
                    "display": "inline-block", "padding": "1px 8px", "borderRadius": "4px",
                    "backgroundColor": color, "color": "#fff", "fontWeight": "700",
                    "fontSize": "11px", "marginRight": "8px",
                }),
                html.Span(org.get("name", "Unknown"), style={
                    "color": "#E6EDF3", "fontSize": "14px", "fontWeight": "600",
                }),
            ]),
            html.Div([
                html.Span(f"{score:.0f}/100", style={"color": color, "fontWeight": "700", "fontSize": "16px"}),
                html.Span(f" — {label}", style={"color": "#8B949E", "fontSize": "13px"}),
            ]),
            html.Div([
                html.Span(a.get("completed_at", "")[:10], style={"color": "#484F58", "fontSize": "12px"}),
                html.Span(f" | {comp.get('weight_profile', 'balanced').replace('_', ' ').title()}", style={"color": "#484F58", "fontSize": "12px"}),
            ]),
        ], style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "padding": "14px 16px",
            "borderBottom": "1px solid var(--border, #272D3F)",
        }))

    assessment_list = html.Div([
        html.Div("Past Assessments", style={"color": "#E6EDF3", "fontSize": "14px", "fontWeight": "700", "marginBottom": "12px"}),
        html.Div(rows),
    ], style={
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "8px",
        "padding": "20px",
        "border": "1px solid var(--border, #272D3F)",
    })

    return html.Div([kpi_row, trend_chart, assessment_list])


def _kpi_card(label: str, value: str, sublabel: str, color: str) -> html.Div:
    return html.Div([
        html.Div(label, style={"color": "#8B949E", "fontSize": "11px", "fontWeight": "600"}),
        html.Div(value, style={"color": color, "fontSize": "24px", "fontWeight": "700", "lineHeight": "1.2"}),
        html.Div(sublabel, style={"color": "#484F58", "fontSize": "11px"}),
    ], style={
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "8px",
        "padding": "16px",
        "border": "1px solid var(--border, #272D3F)",
    })
