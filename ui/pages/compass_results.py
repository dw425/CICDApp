"""Pipeline Compass Results Dashboard Page."""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_layout():
    """Create the results dashboard layout."""
    return html.Div([
        # Page header
        html.Div([
            html.Div([
                html.I(className="fas fa-chart-pie", style={"color": "#4B7BF5", "fontSize": "20px"}),
                html.Div([
                    html.Div("Assessment Results", style={
                        "fontSize": "18px", "fontWeight": "700", "color": "#E6EDF3",
                    }),
                    html.Div(id="compass-results-subtitle", children="Select an assessment to view results", style={
                        "fontSize": "12px", "color": "#8B949E",
                    }),
                ]),
            ], style={"display": "flex", "alignItems": "center", "gap": "12px"}),
            html.Div([
                dbc.Select(
                    id="compass-results-selector",
                    options=[],
                    placeholder="Select assessment...",
                    style={
                        "backgroundColor": "var(--elevated, #21262D)",
                        "color": "#E6EDF3",
                        "border": "1px solid var(--border, #272D3F)",
                        "width": "300px",
                    },
                ),
                dbc.Button(
                    [html.I(className="fas fa-file-pdf"), " Export PDF"],
                    id="compass-export-pdf-btn",
                    color="secondary",
                    outline=True,
                    size="sm",
                    style={"marginLeft": "8px"},
                ),
                dbc.Button(
                    [html.I(className="fas fa-file-powerpoint"), " Export PPTX"],
                    id="compass-export-pptx-btn",
                    color="secondary",
                    outline=True,
                    size="sm",
                    style={"marginLeft": "4px"},
                ),
                dbc.Button(
                    [html.I(className="fas fa-file-csv"), " CSV"],
                    id="compass-export-csv-btn",
                    color="secondary",
                    outline=True,
                    size="sm",
                    style={"marginLeft": "4px"},
                ),
                dbc.Button(
                    [html.I(className="fas fa-code"), " JSON"],
                    id="compass-export-json-btn",
                    color="secondary",
                    outline=True,
                    size="sm",
                    style={"marginLeft": "4px"},
                ),
                dcc.Download(id="compass-download"),
                dcc.Download(id="compass-download-csv"),
                dcc.Download(id="compass-download-json"),
            ], style={"display": "flex", "alignItems": "center"}),
        ], style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "marginBottom": "20px",
        }),

        # Results content (populated by callback)
        html.Div(id="compass-results-content", children=[
            _create_empty_state(),
        ]),

        # Toast
        dbc.Toast(
            id="compass-results-toast",
            header="",
            is_open=False,
            duration=3000,
            style={"position": "fixed", "top": 10, "right": 10, "zIndex": 9999},
        ),
    ], style={"padding": "24px"})


def _create_empty_state():
    """Create empty state when no assessment selected."""
    return html.Div([
        html.I(className="fas fa-compass", style={
            "fontSize": "48px", "color": "#272D3F", "marginBottom": "16px",
        }),
        html.Div("No Assessment Selected", style={
            "color": "#8B949E", "fontSize": "16px", "fontWeight": "600",
        }),
        html.Div(
            "Complete an assessment or select a previous one from the dropdown above.",
            style={"color": "#484F58", "fontSize": "13px", "marginTop": "8px"},
        ),
    ], style={
        "textAlign": "center",
        "padding": "80px 40px",
    })


def create_results_dashboard(
    assessment: dict,
    org: dict,
    composite: dict,
    dimension_scores: dict,
    anti_patterns: list,
    roadmap: dict,
    benchmark_comparison: dict,
) -> html.Div:
    """
    Build the full results dashboard from computed data.

    This is called by the callback after scoring.
    """
    from ui.components.maturity_radar import create_maturity_radar
    from ui.components.maturity_gauge import create_maturity_gauge
    from ui.components.traffic_light_card import create_traffic_light_grid
    from ui.components.gap_waterfall import create_gap_waterfall
    from ui.components.antipattern_scanner import (
        create_antipattern_grid,
        create_antipattern_summary_bar,
    )
    from ui.components.benchmark_comparison import (
        create_benchmark_chart,
        create_percentile_badges,
    )
    from compass.antipattern_engine import get_anti_pattern_summary

    overall = composite.get("overall_score", 0)
    overall_level = composite.get("overall_level", 1)
    overall_label = composite.get("overall_label", "Initial")
    breakdown = composite.get("dimension_breakdown", {})

    ap_summary = get_anti_pattern_summary(anti_patterns)
    gaps = roadmap.get("gaps", [])

    # KPI Row
    kpi_row = html.Div([
        _kpi_card("Overall Score", f"{overall:.0f}/100", f"L{overall_level} — {overall_label}", composite.get("overall_color", "#4B7BF5")),
        _kpi_card("Dimensions", str(len(breakdown)), "core assessed", "#4B7BF5"),
        _kpi_card("Anti-Patterns", str(ap_summary["total"]), f"{ap_summary.get('critical_count', 0)} critical", "#EF4444" if ap_summary.get("critical_count", 0) > 0 else "#34D399"),
        _kpi_card("Weight Profile", composite.get("weight_profile", "balanced").replace("_", " ").title(), "scoring profile", "#A78BFA"),
    ], style={
        "display": "grid",
        "gridTemplateColumns": "repeat(4, 1fr)",
        "gap": "12px",
        "marginBottom": "20px",
    })

    # Row 1: Gauge + Radar
    row1 = html.Div([
        html.Div([
            _section_header("Overall Maturity"),
            create_maturity_gauge(overall, overall_level, overall_label),
        ], style={**_card_style(), "flex": "1", "minWidth": "300px"}),
        html.Div([
            _section_header("Dimension Radar"),
            create_maturity_radar(
                dimension_scores,
                benchmark_scores=benchmark_comparison if benchmark_comparison else None,
            ),
        ], style={**_card_style(), "flex": "2", "minWidth": "400px"}),
    ], style={"display": "flex", "gap": "12px", "marginBottom": "12px", "flexWrap": "wrap"})

    # Row 2: Traffic Light Grid
    row2 = html.Div([
        _section_header("Dimension Scorecard"),
        create_traffic_light_grid(dimension_scores),
    ], style={**_card_style(), "marginBottom": "12px"})

    # Row 3: Gap Waterfall + Benchmark
    row3 = html.Div([
        html.Div([
            _section_header("Gap Analysis"),
            create_gap_waterfall(gaps),
        ], style={**_card_style(), "flex": "1", "minWidth": "400px"}),
        html.Div([
            _section_header("Benchmark Comparison"),
            create_benchmark_chart(benchmark_comparison) if benchmark_comparison else html.Div("No benchmark data", style={"color": "#484F58", "textAlign": "center", "padding": "40px"}),
            create_percentile_badges(benchmark_comparison) if benchmark_comparison else html.Div(),
        ], style={**_card_style(), "flex": "1", "minWidth": "400px"}),
    ], style={"display": "flex", "gap": "12px", "marginBottom": "12px", "flexWrap": "wrap"})

    # Row 4: Anti-Patterns
    row4 = html.Div([
        _section_header("Anti-Pattern Scanner"),
        create_antipattern_summary_bar(ap_summary),
        create_antipattern_grid(anti_patterns),
    ], style={**_card_style(), "marginBottom": "12px"})

    # Row 5: Vulnerability Response Time callout (Oh Sh*t Factor)
    vuln_response = _get_vuln_response(assessment)
    row5 = html.Div() if not vuln_response else html.Div([
        _section_header("Vulnerability Response Time — \"Oh Sh*t Factor\""),
        vuln_response,
    ], style={**_card_style(), "marginBottom": "12px"})

    return html.Div([kpi_row, row1, row2, row3, row4, row5])


def _section_header(title: str) -> html.Div:
    return html.Div(title, style={
        "color": "#E6EDF3",
        "fontSize": "14px",
        "fontWeight": "700",
        "marginBottom": "12px",
    })


def _card_style() -> dict:
    return {
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "8px",
        "padding": "20px",
        "border": "1px solid var(--border, #272D3F)",
    }


def _get_vuln_response(assessment: dict) -> html.Div:
    """Extract the Oh Sh*t Factor response (pg_005) and render a callout."""
    responses = assessment.get("responses", {})
    pg_005 = responses.get("pg_005")
    if not pg_005:
        return None

    resp_val = pg_005.get("response_value", pg_005)
    if isinstance(resp_val, dict):
        val = resp_val.get("value", 0)
    else:
        val = resp_val

    if val == -1:
        return None

    labels = {
        1: ("Weeks", "#EF4444", "fas fa-exclamation-triangle"),
        2: ("Days", "#F97316", "fas fa-clock"),
        3: ("Hours", "#EAB308", "fas fa-hourglass-half"),
        4: ("Under an Hour", "#22C55E", "fas fa-bolt"),
        5: ("Minutes", "#3B82F6", "fas fa-rocket"),
    }

    label, color, icon = labels.get(val, ("Unknown", "#6B7280", "fas fa-question"))

    return html.Div([
        html.Div([
            html.I(className=icon, style={"color": color, "fontSize": "24px", "marginRight": "12px"}),
            html.Div([
                html.Div(label, style={"color": color, "fontSize": "22px", "fontWeight": "700"}),
                html.Div("to deploy a critical vulnerability fix across all services",
                         style={"color": "#8B949E", "fontSize": "12px"}),
            ]),
        ], style={"display": "flex", "alignItems": "center"}),
    ], style={
        "backgroundColor": f"{color}11",
        "borderRadius": "8px",
        "padding": "16px 20px",
        "border": f"1px solid {color}33",
    })


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
