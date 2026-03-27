"""Pipeline Compass Roadmap Page."""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_layout():
    """Create the roadmap page layout."""
    return html.Div([
        # Header
        html.Div([
            html.Div([
                html.I(className="fas fa-road", style={"color": "#34D399", "fontSize": "20px"}),
                html.Div([
                    html.Div("Improvement Roadmap", style={
                        "fontSize": "18px", "fontWeight": "700", "color": "#E6EDF3",
                    }),
                    html.Div("Prioritized actions to advance CI/CD maturity", style={
                        "fontSize": "12px", "color": "#8B949E",
                    }),
                ]),
            ], style={"display": "flex", "alignItems": "center", "gap": "12px"}),
            html.Div([
                dbc.Select(
                    id="compass-roadmap-selector",
                    options=[],
                    placeholder="Select assessment...",
                    style={
                        "backgroundColor": "var(--elevated, #21262D)",
                        "color": "#E6EDF3",
                        "border": "1px solid var(--border, #272D3F)",
                        "width": "300px",
                    },
                ),
                dbc.Select(
                    id="compass-roadmap-target",
                    options=[
                        {"label": "Target: Next Tier", "value": "next_tier"},
                        {"label": "Target: Elite", "value": "elite"},
                    ],
                    value="next_tier",
                    style={
                        "backgroundColor": "var(--elevated, #21262D)",
                        "color": "#E6EDF3",
                        "border": "1px solid var(--border, #272D3F)",
                        "width": "200px",
                        "marginLeft": "8px",
                    },
                ),
            ], style={"display": "flex", "alignItems": "center"}),
        ], style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "marginBottom": "20px",
        }),

        # Content
        html.Div(id="compass-roadmap-content", children=[
            _create_empty_state(),
        ]),
    ], style={"padding": "24px"})


def _create_empty_state():
    return html.Div([
        html.I(className="fas fa-road", style={
            "fontSize": "48px", "color": "#272D3F", "marginBottom": "16px",
        }),
        html.Div("No Roadmap Available", style={
            "color": "#8B949E", "fontSize": "16px", "fontWeight": "600",
        }),
        html.Div(
            "Complete an assessment first, then come here to see your improvement roadmap.",
            style={"color": "#484F58", "fontSize": "13px", "marginTop": "8px"},
        ),
    ], style={"textAlign": "center", "padding": "80px 40px"})


def create_roadmap_dashboard(
    roadmap: dict,
    dimension_scores: dict,
) -> html.Div:
    """Build the full roadmap dashboard from computed data."""
    from ui.components.roadmap_timeline import create_roadmap_timeline
    from ui.components.impact_effort_matrix import create_impact_effort_matrix
    from ui.components.gap_waterfall import create_gap_waterfall

    phases = roadmap.get("phases", [])
    roi = roadmap.get("total_roi_estimate", {})
    matrix = roadmap.get("impact_effort_matrix", {})
    gaps = roadmap.get("gaps", [])

    total_items = roi.get("items_count", 0)
    total_effort = roi.get("total_effort_days", 0)
    total_improvement = roi.get("total_expected_score_improvement", 0)
    roi_by_cat = roi.get("roi_by_category", {})

    # KPI Row
    kpi_row = html.Div([
        _kpi_card("Recommendations", str(total_items), "improvement items", "#4B7BF5"),
        _kpi_card("Total Effort", f"{total_effort}d", "estimated days", "#FBBF24"),
        _kpi_card("Score Impact", f"+{total_improvement}", "expected points", "#34D399"),
        _kpi_card("Quick Wins", str(len(matrix.get("quick_wins", []))), "high impact, low effort", "#34D399"),
    ], style={
        "display": "grid",
        "gridTemplateColumns": "repeat(4, 1fr)",
        "gap": "12px",
        "marginBottom": "20px",
    })

    # ROI Summary
    roi_section = html.Div([
        _section_header("Estimated ROI"),
        html.Div([
            _roi_item("Developer Hours Saved", f"{roi_by_cat.get('speed', {}).get('hours_saved_annually', 0):,}/year", "#4B7BF5"),
            _roi_item("Incident Reduction", f"{roi_by_cat.get('quality', {}).get('incident_reduction_pct', 0)}%", "#34D399"),
            _roi_item("Risk Reduction", f"{roi_by_cat.get('risk', {}).get('risk_reduction_pct', 0)}%", "#FBBF24"),
            _roi_item("Cost Reduction", f"{roi_by_cat.get('cost', {}).get('cost_reduction_pct', 0)}%", "#A78BFA"),
        ], style={
            "display": "grid",
            "gridTemplateColumns": "repeat(4, 1fr)",
            "gap": "12px",
        }),
    ], style={**_card_style(), "marginBottom": "12px"})

    # Impact-Effort Matrix + Gap Waterfall
    row2 = html.Div([
        html.Div([
            _section_header("Impact x Effort Matrix"),
            create_impact_effort_matrix(matrix),
        ], style={**_card_style(), "flex": "1", "minWidth": "400px"}),
        html.Div([
            _section_header("Gap Analysis"),
            create_gap_waterfall(gaps),
        ], style={**_card_style(), "flex": "1", "minWidth": "400px"}),
    ], style={"display": "flex", "gap": "12px", "marginBottom": "12px", "flexWrap": "wrap"})

    # Progress bar
    all_items = []
    for phase in phases:
        all_items.extend(phase.get("items", []))
    done_count = sum(1 for it in all_items if it.get("status") == "done")
    total_count = len(all_items)
    progress_pct = (done_count / total_count * 100) if total_count > 0 else 0

    progress_bar = html.Div([
        html.Div([
            html.Div(f"Roadmap Progress: {done_count} of {total_count} completed", style={
                "color": "#E6EDF3", "fontSize": "13px", "fontWeight": "600",
            }),
            html.Div(f"{progress_pct:.0f}%", style={
                "color": "#34D399" if progress_pct > 50 else "#FBBF24", "fontWeight": "700",
            }),
        ], style={"display": "flex", "justifyContent": "space-between", "marginBottom": "6px"}),
        dbc.Progress(
            value=progress_pct,
            color="success" if progress_pct > 50 else "warning",
            style={"height": "8px", "backgroundColor": "#21262D"},
        ),
    ], style={**_card_style(), "marginBottom": "12px"})

    # Phased Timeline with status toggles
    row3 = html.Div([
        _section_header("Phased Improvement Timeline"),
        create_roadmap_timeline(phases),
        _create_status_tracker(phases),
    ], style={**_card_style(), "marginBottom": "12px"})

    # Store for status updates
    status_store = dcc.Store(id="roadmap-status-store", data={})

    return html.Div([kpi_row, progress_bar, roi_section, row2, row3, status_store])


def _section_header(title: str) -> html.Div:
    return html.Div(title, style={
        "color": "#E6EDF3", "fontSize": "14px", "fontWeight": "700", "marginBottom": "12px",
    })


def _card_style() -> dict:
    return {
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "8px",
        "padding": "20px",
        "border": "1px solid var(--border, #272D3F)",
    }


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


def _create_status_tracker(phases: list) -> html.Div:
    """Create status toggle UI for each roadmap item."""
    items = []
    for phase in phases:
        phase_name = phase.get("name", "")
        for item in phase.get("items", []):
            item_id = item.get("id", item.get("title", "").replace(" ", "_")[:30])
            status = item.get("status", "not_started")
            title = item.get("title", "")
            effort = item.get("effort_days", "?")
            impact = item.get("expected_score_improvement", 0)

            status_color = {"not_started": "#484F58", "in_progress": "#FBBF24", "done": "#34D399"}.get(status, "#484F58")
            status_label = {"not_started": "Not Started", "in_progress": "In Progress", "done": "Done"}.get(status, "Not Started")

            items.append(html.Div([
                html.Div([
                    html.Span(status_label, style={
                        "display": "inline-block", "padding": "2px 8px", "borderRadius": "4px",
                        "backgroundColor": status_color, "color": "#fff", "fontSize": "10px",
                        "fontWeight": "700", "marginRight": "10px", "minWidth": "70px", "textAlign": "center",
                    }),
                    html.Span(title, style={"color": "#E6EDF3", "fontSize": "13px", "fontWeight": "600"}),
                ], style={"flex": "1"}),
                html.Div([
                    html.Span(f"{effort}d", style={"color": "#8B949E", "fontSize": "11px", "marginRight": "12px"}),
                    html.Span(f"+{impact}pts", style={"color": "#34D399", "fontSize": "11px", "marginRight": "12px"}),
                    dbc.RadioItems(
                        id={"type": "roadmap-status", "index": item_id},
                        options=[
                            {"label": "Not Started", "value": "not_started"},
                            {"label": "In Progress", "value": "in_progress"},
                            {"label": "Done", "value": "done"},
                        ],
                        value=status,
                        inline=True,
                        style={"fontSize": "11px"},
                        inputStyle={"marginRight": "3px"},
                        labelStyle={"marginRight": "8px", "color": "#8B949E", "fontSize": "11px"},
                    ),
                ], style={"display": "flex", "alignItems": "center"}),
            ], style={
                "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                "padding": "10px 12px", "borderBottom": "1px solid rgba(39,45,63,0.3)",
            }))

    if not items:
        return html.Div()

    return html.Div([
        html.Div("Status Tracker", style={
            "color": "#E6EDF3", "fontSize": "14px", "fontWeight": "700",
            "marginTop": "16px", "marginBottom": "8px",
        }),
        html.Div(items),
    ])


def _roi_item(label: str, value: str, color: str) -> html.Div:
    return html.Div([
        html.Div(value, style={"color": color, "fontSize": "20px", "fontWeight": "700"}),
        html.Div(label, style={"color": "#8B949E", "fontSize": "11px"}),
    ], style={"textAlign": "center"})
