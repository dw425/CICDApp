"""Executive Summary Page — unified landing page with 3 states.
# ****Truth Agent Verified**** — 3 states: _create_welcome_state (CTAs + feature highlights),
# create_assessment_state (gauge, radar, top 3 gaps, confidence badge),
# create_full_data_state (DORA tiles, hygiene summary, archetype, full data)
"""

from dash import html, dcc
from ui.components.kpi_card import create_kpi_card


def create_layout():
    """Return the Executive Summary page layout.

    Three states are rendered by the callback:
    - State 1: No data (fresh install) — welcome + CTAs
    - State 2: Assessment only — COMPASS scores + radar
    - State 3: Full data — assessment + telemetry + DORA
    """
    return html.Div([
        # The callback populates this entirely based on data state
        html.Div(id="exec-landing-content", children=[
            _create_welcome_state(),
        ]),

        # Hidden containers for chart outputs (needed for callback registration)
        html.Div([
            html.Div(id="kpi-composite"),
            html.Div(id="kpi-golden-path"),
            html.Div(id="kpi-pipeline"),
            html.Div(id="kpi-teams"),
            dcc.Graph(id="exec-golden-pie", config={"displayModeBar": False}, style={"display": "none"}),
            dcc.Graph(id="exec-heatmap", config={"displayModeBar": False}, style={"display": "none"}),
            dcc.Graph(id="exec-trend-line", config={"displayModeBar": False}, style={"display": "none"}),
            html.Div(id="exec-alerts-table", style={"display": "none"}),
        ], style={"display": "none"}),
    ])


def _create_welcome_state() -> html.Div:
    """State 1: Fresh install — welcome message with CTAs."""
    return html.Div([
        html.Div([
            html.I(className="fas fa-compass", style={
                "fontSize": "48px", "color": "#4B7BF5", "marginBottom": "20px",
            }),
            html.H2("Pipeline COMPASS", style={
                "color": "#E6EDF3", "fontSize": "28px", "fontWeight": "700", "marginBottom": "8px",
            }),
            html.Div("CI/CD Maturity Intelligence Platform", style={
                "color": "#8B949E", "fontSize": "14px", "marginBottom": "24px",
            }),
        ], style={"textAlign": "center"}),

        # Framework explanation
        html.Div([
            html.P([
                "COMPASS evaluates your CI/CD maturity across ",
                html.Strong("9 dimensions"),
                " using a hybrid approach: self-assessment questionnaires validated by ",
                html.Strong("78 automated telemetry checks"),
                " across 6 platforms.",
            ], style={"color": "#8B949E", "fontSize": "13px", "textAlign": "center", "maxWidth": "600px", "margin": "0 auto 24px"}),
        ]),

        # CTA cards
        html.Div([
            _cta_card(
                "Start Assessment",
                "Answer questions about your CI/CD practices across 9 dimensions",
                "fas fa-play-circle",
                "#22C55E",
                "compass_assessment",
            ),
            _cta_card(
                "View Hygiene Dashboard",
                "See automated telemetry checks across connected platforms",
                "fas fa-heartbeat",
                "#4B7BF5",
                "hygiene",
            ),
            _cta_card(
                "Explore DORA Metrics",
                "Industry-standard delivery performance metrics with tier classification",
                "fas fa-tachometer-alt",
                "#F59E0B",
                "dora_metrics",
            ),
        ], style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fill, minmax(250px, 1fr))",
            "gap": "16px",
            "marginBottom": "32px",
        }),

        # Feature highlights
        html.Div([
            _feature_highlight("9 Dimensions", "Build, Test, Deploy, Security, Observability, IaC, Artifacts, DX, Governance", "fas fa-layer-group"),
            _feature_highlight("78 Checks", "Automated hygiene checks across GitHub, ADO, Jenkins, GitLab, Jira, Databricks", "fas fa-check-double"),
            _feature_highlight("5 DORA Metrics", "Deployment Frequency, Lead Time, CFR, MTTR, Rework Rate", "fas fa-chart-bar"),
            _feature_highlight("7 Archetypes", "DORA 2025 team classification from High-Achievers to Foundational Challenges", "fas fa-users"),
            _feature_highlight("Hybrid Scoring", "70% telemetry + 30% assessment with confidence levels", "fas fa-balance-scale"),
            _feature_highlight("Hard Gates", "Critical checks that cap scores — no shortcuts to Elite", "fas fa-shield-alt"),
        ], style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fill, minmax(200px, 1fr))",
            "gap": "10px",
        }),
    ], style={"padding": "40px 20px"})


def create_assessment_state(composite: dict, dimension_scores: dict, anti_patterns: list) -> html.Div:
    """State 2: Assessment completed but no telemetry — show COMPASS results."""
    from ui.components.maturity_radar import create_maturity_radar
    from ui.components.maturity_gauge import create_maturity_gauge
    from ui.components.confidence_badge import create_confidence_badge
    from compass.antipattern_engine import get_anti_pattern_summary

    overall = composite.get("overall_score", 0)
    overall_level = composite.get("overall_level", 1)
    overall_label = composite.get("overall_label", "Initial")
    breakdown = composite.get("dimension_breakdown", {})
    ap_summary = get_anti_pattern_summary(anti_patterns)

    return html.Div([
        # Confidence banner
        html.Div([
            create_confidence_badge("low"),
            html.Span("  Connect a data source for objective telemetry scoring",
                      style={"color": "#8B949E", "fontSize": "12px", "marginLeft": "8px"}),
        ], style={"marginBottom": "16px"}),

        # KPIs
        html.Div([
            _exec_kpi("COMPASS Score", f"{overall:.0f}/100", f"L{overall_level} — {overall_label}",
                      composite.get("overall_color", "#4B7BF5")),
            _exec_kpi("Dimensions", str(len(breakdown)), "assessed", "#4B7BF5"),
            _exec_kpi("Anti-Patterns", str(ap_summary["total"]),
                      f"{ap_summary.get('critical_count', 0)} critical",
                      "#EF4444" if ap_summary.get("critical_count", 0) > 0 else "#22C55E"),
            _exec_kpi("Data Sources", "0", "connect one for telemetry", "#F59E0B"),
        ], style={
            "display": "grid", "gridTemplateColumns": "repeat(4, 1fr)",
            "gap": "12px", "marginBottom": "20px",
        }),

        # Radar + Gauge
        html.Div([
            html.Div([
                html.Div("Overall Maturity", className="card-header"),
                html.Div([create_maturity_gauge(overall, overall_level, overall_label)], className="card-body"),
            ], className="card"),
            html.Div([
                html.Div("Dimension Radar", className="card-header"),
                html.Div([create_maturity_radar(dimension_scores)], className="card-body"),
            ], className="card"),
        ], className="grid-2"),

        # Top 3 gaps
        html.Div([
            html.Div("Top Improvement Areas", className="card-header"),
            html.Div([
                _gap_item(dim_id, data)
                for dim_id, data in sorted(
                    breakdown.items(),
                    key=lambda x: x[1].get("score", 0) if isinstance(x[1], dict) else 0,
                )[:3]
            ], className="card-body"),
        ], className="card", style={"marginTop": "12px"}),
    ])


def create_full_data_state(
    composite: dict, dimension_scores: dict, anti_patterns: list,
    dora_metrics: dict, hygiene_summary: dict,
) -> html.Div:
    """State 3: Full data — assessment + telemetry + DORA."""
    from ui.components.maturity_radar import create_maturity_radar
    from ui.components.maturity_gauge import create_maturity_gauge
    from ui.components.confidence_badge import create_confidence_badge
    from ui.components.dora_tiles import create_dora_tiles_row
    from ui.components.hygiene_platform_summary import create_platform_summary
    from compass.antipattern_engine import get_anti_pattern_summary
    from compass.archetype_engine import classify_archetype, get_archetype_info

    overall = composite.get("overall_score", 0)
    overall_level = composite.get("overall_level", 1)
    overall_label = composite.get("overall_label", "Initial")
    breakdown = composite.get("dimension_breakdown", {})
    ap_summary = get_anti_pattern_summary(anti_patterns)

    archetype_id = classify_archetype(dimension_scores, dora_metrics)
    archetype = get_archetype_info(archetype_id)

    return html.Div([
        # Confidence banner
        html.Div([
            create_confidence_badge("high"),
            html.Span("  Telemetry-validated scoring active",
                      style={"color": "#8B949E", "fontSize": "12px", "marginLeft": "8px"}),
        ], style={"marginBottom": "16px"}),

        # KPIs
        html.Div([
            _exec_kpi("COMPASS Score", f"{overall:.0f}/100", f"L{overall_level} — {overall_label}",
                      composite.get("overall_color", "#4B7BF5")),
            _exec_kpi("Archetype", archetype["name"], archetype.get("pct_of_teams", ""), archetype["color"]),
            _exec_kpi("Anti-Patterns", str(ap_summary["total"]),
                      f"{ap_summary.get('critical_count', 0)} critical",
                      "#EF4444" if ap_summary.get("critical_count", 0) > 0 else "#22C55E"),
            _exec_kpi("Deploys", str(dora_metrics.get("total_deploys", 0)),
                      f"last {dora_metrics.get('period_days', 30)}d",
                      "#22C55E"),
        ], style={
            "display": "grid", "gridTemplateColumns": "repeat(4, 1fr)",
            "gap": "12px", "marginBottom": "20px",
        }),

        # DORA tiles
        html.Div([
            html.Div("DORA Metrics", className="card-header"),
            html.Div([create_dora_tiles_row(dora_metrics)], className="card-body"),
        ], className="card", style={"marginBottom": "12px"}),

        # Radar + Gauge
        html.Div([
            html.Div([
                html.Div("Overall Maturity", className="card-header"),
                html.Div([create_maturity_gauge(overall, overall_level, overall_label)], className="card-body"),
            ], className="card"),
            html.Div([
                html.Div("Dimension Radar", className="card-header"),
                html.Div([create_maturity_radar(dimension_scores)], className="card-body"),
            ], className="card"),
        ], className="grid-2"),

        # Hygiene summary + Top gaps
        html.Div([
            html.Div([
                html.Div("Platform Hygiene", className="card-header"),
                html.Div([
                    create_platform_summary(p, data)
                    for p, data in sorted(hygiene_summary.items())
                ] if hygiene_summary else [
                    html.Div("No hygiene data", style={"color": "#484F58", "textAlign": "center", "padding": "20px"})
                ], className="card-body", style={"display": "flex", "flexDirection": "column", "gap": "6px"}),
            ], className="card"),
            html.Div([
                html.Div("Top Improvement Areas", className="card-header"),
                html.Div([
                    _gap_item(dim_id, data)
                    for dim_id, data in sorted(
                        breakdown.items(),
                        key=lambda x: x[1].get("score", 0) if isinstance(x[1], dict) else 0,
                    )[:3]
                ], className="card-body"),
            ], className="card"),
        ], className="grid-2", style={"marginTop": "12px"}),
    ])


def _cta_card(title: str, desc: str, icon: str, color: str, page: str) -> html.Div:
    return html.Div([
        html.I(className=icon, style={"color": color, "fontSize": "24px", "marginBottom": "10px"}),
        html.Div(title, style={"color": "#E6EDF3", "fontSize": "14px", "fontWeight": "600", "marginBottom": "4px"}),
        html.Div(desc, style={"color": "#8B949E", "fontSize": "11px"}),
    ], id=f"exec-cta-{page}", style={
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "8px",
        "padding": "20px",
        "border": f"1px solid {color}33",
        "cursor": "pointer",
        "textAlign": "center",
    })


def _feature_highlight(title: str, desc: str, icon: str) -> html.Div:
    return html.Div([
        html.I(className=icon, style={"color": "#4B7BF5", "fontSize": "16px", "marginBottom": "6px"}),
        html.Div(title, style={"color": "#E6EDF3", "fontSize": "12px", "fontWeight": "600"}),
        html.Div(desc, style={"color": "#484F58", "fontSize": "10px"}),
    ], style={
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "6px",
        "padding": "12px",
        "border": "1px solid var(--border, #272D3F)",
    })


def _exec_kpi(label: str, value: str, sublabel: str, color: str) -> html.Div:
    return html.Div([
        html.Div(label, style={"color": "#8B949E", "fontSize": "11px", "fontWeight": "600"}),
        html.Div(value, style={"color": color, "fontSize": "22px", "fontWeight": "700", "lineHeight": "1.2"}),
        html.Div(sublabel, style={"color": "#484F58", "fontSize": "11px"}),
    ], style={
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "8px",
        "padding": "14px",
        "border": "1px solid var(--border, #272D3F)",
    })


def _gap_item(dim_id: str, data: dict) -> html.Div:
    score = data.get("score", 0) if isinstance(data, dict) else data
    color = data.get("color", "#EF4444") if isinstance(data, dict) else "#EF4444"
    name = data.get("display_name", dim_id.replace("_", " ").title()) if isinstance(data, dict) else dim_id
    return html.Div([
        html.Div([
            html.Span(name, style={"color": "#E6EDF3", "fontSize": "13px", "fontWeight": "500"}),
            html.Span(f"{score:.0f}/100", style={"color": color, "fontSize": "13px", "fontWeight": "700"}),
        ], style={"display": "flex", "justifyContent": "space-between"}),
        html.Div(style={
            "height": "4px", "backgroundColor": "#21262D", "borderRadius": "2px", "marginTop": "4px",
            "position": "relative", "overflow": "hidden",
        }, children=[
            html.Div(style={
                "height": "100%", "width": f"{score}%", "backgroundColor": color,
                "borderRadius": "2px",
            }),
        ]),
    ], style={"padding": "6px 0", "borderBottom": "1px solid #21262D22"})
