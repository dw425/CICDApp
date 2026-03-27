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

    # Row 2: Traffic Light Grid with Per-Question Drill-Down
    row2 = html.Div([
        _section_header("Dimension Scorecard — Click a dimension to expand"),
        create_traffic_light_grid(dimension_scores),
        _create_dimension_drilldown(assessment, dimension_scores),
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


def _create_dimension_drilldown(assessment: dict, dimension_scores: dict) -> html.Div:
    """Create expandable per-question drill-down for each dimension."""
    responses = assessment.get("responses", {})
    hygiene_data = assessment.get("hygiene_scores", {})

    from compass.question_bank.loader import load_all_dimensions, get_questions_for_dimension
    from compass.scoring_engine import compute_question_score, TIER_COLORS
    load_all_dimensions()

    accordion_items = []
    for dim_id, score_data in sorted(
        dimension_scores.items(),
        key=lambda x: x[1].get("raw_score", 0) if isinstance(x[1], dict) else 0,
    ):
        if not isinstance(score_data, dict):
            continue
        raw_score = score_data.get("raw_score", 0)
        level = score_data.get("level", 1)
        label = score_data.get("label", "Initial")
        display_name = score_data.get("display_name", dim_id.replace("_", " ").title())
        color = TIER_COLORS.get(level, "#888")

        questions = get_questions_for_dimension(dim_id)
        if not questions:
            continue

        # Build question rows sorted by score (lowest first)
        q_rows = []
        for q in questions:
            qid = q["id"]
            resp = responses.get(qid)
            if not resp:
                q_rows.append((None, _question_row(q, None, None)))
                continue
            resp_val = resp.get("response_value", resp)
            if isinstance(resp_val, (int, float)):
                resp_val = {"value": resp_val}
            score = compute_question_score(q, resp_val)
            answer_text = _get_answer_text(q, resp_val)
            q_rows.append((score, _question_row(q, score, answer_text)))

        q_rows.sort(key=lambda x: x[0] if x[0] is not None else 999)
        question_content = [r[1] for r in q_rows]

        # Hygiene checks for this dimension
        dim_hygiene = [h for h in hygiene_data if isinstance(h, dict) and h.get("dimension") == dim_id] if isinstance(hygiene_data, list) else []
        hygiene_section = html.Div()
        if dim_hygiene:
            hygiene_rows = []
            for h in dim_hygiene:
                status = h.get("status", "unknown")
                badge_color = {"pass": "#34D399", "warn": "#FBBF24", "fail": "#EF4444"}.get(status, "#6B7280")
                hygiene_rows.append(html.Div([
                    html.Span(status.upper(), style={
                        "display": "inline-block", "padding": "1px 6px", "borderRadius": "3px",
                        "backgroundColor": badge_color, "color": "#fff", "fontSize": "10px",
                        "fontWeight": "700", "width": "40px", "textAlign": "center", "marginRight": "8px",
                    }),
                    html.Span(h.get("name", h.get("check_id", "")), style={"color": "#E6EDF3", "fontSize": "12px"}),
                    html.Span(f" — {h.get('raw_value', '')}", style={"color": "#8B949E", "fontSize": "11px", "marginLeft": "8px"}),
                ], style={"padding": "4px 0"}))
            hygiene_section = html.Div([
                html.Div("Hygiene Checks", style={"color": "#A78BFA", "fontSize": "12px", "fontWeight": "700", "marginTop": "12px", "marginBottom": "6px"}),
                *hygiene_rows,
            ])

        accordion_items.append(dbc.AccordionItem(
            title=f"{display_name} — {raw_score:.0f}/100 (L{level} {label})",
            children=[
                html.Div(question_content, style={"marginBottom": "8px"}),
                hygiene_section,
            ],
            style={"backgroundColor": "var(--elevated, #21262D)", "border": f"1px solid {color}33"},
        ))

    if not accordion_items:
        return html.Div()

    return html.Div([
        html.Div("Per-Question Breakdown", style={
            "color": "#E6EDF3", "fontSize": "14px", "fontWeight": "700",
            "marginTop": "16px", "marginBottom": "8px",
        }),
        dbc.Accordion(accordion_items, start_collapsed=True, flush=True),
    ])


def _question_row(question: dict, score, answer_text: str) -> html.Div:
    """Render a single question row in the drill-down."""
    if score is None and answer_text is None:
        badge_color = "#484F58"
        badge_text = "—"
    elif score is None:
        badge_color = "#6B7280"
        badge_text = "IDK"
    elif score <= 25:
        badge_color = "#EF4444"
        badge_text = f"{score:.0f}"
    elif score <= 50:
        badge_color = "#F97316"
        badge_text = f"{score:.0f}"
    elif score <= 75:
        badge_color = "#EAB308"
        badge_text = f"{score:.0f}"
    else:
        badge_color = "#34D399"
        badge_text = f"{score:.0f}"

    return html.Div([
        html.Span(badge_text, style={
            "display": "inline-block", "width": "36px", "textAlign": "center",
            "padding": "2px 4px", "borderRadius": "4px",
            "backgroundColor": badge_color, "color": "#fff",
            "fontSize": "11px", "fontWeight": "700", "marginRight": "10px",
            "flexShrink": "0",
        }),
        html.Div([
            html.Div(question.get("text", ""), style={"color": "#E6EDF3", "fontSize": "12px"}),
            html.Div(answer_text or "Not answered", style={
                "color": "#8B949E", "fontSize": "11px", "fontStyle": "italic",
            }),
        ], style={"flex": "1"}),
    ], style={
        "display": "flex", "alignItems": "flex-start", "padding": "6px 0",
        "borderBottom": "1px solid rgba(39,45,63,0.3)",
    })


def _get_answer_text(question: dict, resp_val: dict) -> str:
    """Get human-readable answer text from response value."""
    qtype = question.get("type", "likert")
    if qtype in ("likert", "single_select"):
        val = resp_val.get("value")
        if val == -1:
            return "I'm not sure / Don't know"
        for opt in question.get("options", []):
            if opt.get("value") == val:
                return opt.get("label", str(val))
        return str(val) if val is not None else ""
    elif qtype == "binary":
        return "Yes" if resp_val.get("value") else "No"
    elif qtype == "multi_select":
        selected = resp_val.get("values", [])
        labels = []
        for opt in question.get("options", []):
            if opt.get("value") in selected:
                labels.append(opt.get("label", opt["value"]))
        return ", ".join(labels) if labels else "None selected"
    elif qtype == "freeform":
        return resp_val.get("text", "")[:200]
    return ""


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
