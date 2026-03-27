"""Scoring Logic Page — transparency into how scores are computed.
# ****Truth Agent Verified**** — 5-layer methodology overview, tier map display,
# weight profile matrix (5 profiles), 78-check DataTable registry with sort/filter,
# DORA benchmark table, 7 archetype cards, formula display, confidence explanation.
"""

from dash import html, dcc, dash_table
from compass.scoring_engine import WEIGHT_PROFILES, WEIGHT_PROFILE_LABELS, TIER_MAP, TIER_COLORS
from compass.scoring_constants import DORA_BENCHMARKS, DORA_TIER_COLORS, DIMENSION_IDS
from compass.hygiene_scorer import get_all_check_definitions
from compass.archetype_engine import ARCHETYPES


def create_layout():
    """Return the Scoring Logic transparency page layout."""
    all_checks = get_all_check_definitions()

    return html.Div([
        # Section 1: Methodology overview
        _section("Scoring Methodology", [
            html.P("Pipeline COMPASS uses a 5-layer scoring architecture:",
                   style={"color": "#8B949E", "fontSize": "13px", "marginBottom": "12px"}),
            html.Div([
                _layer_card("1", "Self-Assessment", "9 dimensions × ~4 questions = 0-100 per dimension", "#3B82F6"),
                _layer_card("2", "Telemetry Hygiene", "78 automated checks across 6 platforms", "#22C55E"),
                _layer_card("3", "Hybrid Blend", "70% telemetry + 30% assessment with confidence", "#8B5CF6"),
                _layer_card("4", "DORA Metrics", "5 industry-standard delivery performance metrics", "#F59E0B"),
                _layer_card("5", "Archetype Classification", "7 team archetypes from score patterns", "#06B6D4"),
            ], style={"display": "flex", "gap": "10px", "flexWrap": "wrap", "marginBottom": "16px"}),
        ]),

        # Section 2: Tier definitions
        _section("Maturity Tier Map", [
            html.Div([
                html.Div([
                    html.Div(f"L{level}", style={
                        "color": TIER_COLORS[level], "fontSize": "20px", "fontWeight": "700",
                    }),
                    html.Div(label, style={"color": "#E6EDF3", "fontSize": "12px", "fontWeight": "600"}),
                    html.Div(f"{low}–{high}", style={"color": "#8B949E", "fontSize": "11px"}),
                ], style={
                    "backgroundColor": "var(--surface, #161B22)",
                    "borderRadius": "6px",
                    "padding": "12px 16px",
                    "border": f"1px solid {TIER_COLORS[level]}33",
                    "textAlign": "center",
                    "flex": "1",
                    "minWidth": "100px",
                }) for low, high, level, label in TIER_MAP
            ], style={"display": "flex", "gap": "10px", "flexWrap": "wrap"}),
        ]),

        # Section 3: Weight profiles
        _section("Weight Profiles", [
            html.P("Different weight profiles shift dimension importance based on organizational context.",
                   style={"color": "#8B949E", "fontSize": "12px", "marginBottom": "10px"}),
            _weight_matrix_table(),
        ]),

        # Section 4: Hybrid blend formula
        _section("Hybrid Scoring Formula", [
            html.Div([
                _formula_item("Both scores available", "Score = Telemetry × 0.70 + Assessment × 0.30", "Confidence: High"),
                _formula_item("Telemetry only", "Score = Telemetry × 1.00", "Confidence: Medium"),
                _formula_item("Assessment only", "Score = Assessment × 1.00", "Confidence: Low"),
                _formula_item("No data", "Score = 0", "Confidence: None"),
            ], style={"display": "flex", "gap": "10px", "flexWrap": "wrap", "marginBottom": "12px"}),
            html.Div([
                html.Span("Composite: ", style={"color": "#8B949E", "fontSize": "12px"}),
                html.Code("exp(Σ(wᵢ × ln(scoreᵢ + 1)) / Σwᵢ) − 1",
                           style={"color": "#4B7BF5", "fontSize": "13px"}),
                html.Span("  (Weighted Geometric Mean — penalizes imbalance)",
                           style={"color": "#484F58", "fontSize": "11px"}),
            ]),
            html.Div([
                html.Span("Hard Gates: ", style={"color": "#EF4444", "fontSize": "12px", "fontWeight": "600"}),
                html.Span("If any hard-gate check fails (score < 50), the entire dimension is capped at L2 (40).",
                           style={"color": "#8B949E", "fontSize": "12px"}),
            ], style={"marginTop": "8px"}),
            html.Div([
                html.Span("Discrepancy: ", style={"color": "#F59E0B", "fontSize": "12px", "fontWeight": "600"}),
                html.Span("Flagged when |telemetry − assessment| > 20 points.",
                           style={"color": "#8B949E", "fontSize": "12px"}),
            ], style={"marginTop": "4px"}),
        ]),

        # Section 5: Check registry
        _section("Hygiene Check Registry (78 checks)", [
            html.Div([
                html.Label("Filter:", style={"color": "#8B949E", "fontSize": "11px", "marginRight": "8px"}),
                dcc.Dropdown(
                    id="scoring-check-platform-filter",
                    options=[{"label": "All", "value": "all"}] + [
                        {"label": p.replace("_", " ").title(), "value": p}
                        for p in sorted(set(c["platform"] for c in all_checks))
                    ],
                    value="all",
                    clearable=False,
                    style={"width": "200px", "backgroundColor": "#0D1117"},
                    className="dash-dropdown-dark",
                ),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "10px"}),
            html.Div(id="scoring-check-table", children=_check_table(all_checks)),
        ]),

        # Section 6: DORA benchmarks
        _section("DORA 2025 Benchmark Thresholds", [
            _dora_benchmark_table(),
        ]),

        # Section 7: Archetype map
        _section("Team Archetypes (DORA 2025)", [
            html.Div([
                _archetype_card(aid, arch) for aid, arch in ARCHETYPES.items()
            ], style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fill, minmax(280px, 1fr))",
                "gap": "10px",
            }),
        ]),
    ])


def _section(title: str, children: list) -> html.Div:
    return html.Div([
        html.H3(title, style={
            "color": "#E6EDF3", "fontSize": "16px", "fontWeight": "600",
            "marginBottom": "12px", "paddingBottom": "8px",
            "borderBottom": "1px solid #21262D",
        }),
        *children,
    ], style={"marginBottom": "28px"})


def _layer_card(num: str, title: str, desc: str, color: str) -> html.Div:
    return html.Div([
        html.Span(num, style={"color": color, "fontSize": "20px", "fontWeight": "700"}),
        html.Div(title, style={"color": "#E6EDF3", "fontSize": "12px", "fontWeight": "600", "marginTop": "4px"}),
        html.Div(desc, style={"color": "#8B949E", "fontSize": "10px", "marginTop": "2px"}),
    ], style={
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "6px",
        "padding": "12px 14px",
        "border": f"1px solid {color}33",
        "flex": "1",
        "minWidth": "150px",
    })


def _formula_item(condition: str, formula: str, confidence: str) -> html.Div:
    return html.Div([
        html.Div(condition, style={"color": "#E6EDF3", "fontSize": "12px", "fontWeight": "600"}),
        html.Code(formula, style={"color": "#4B7BF5", "fontSize": "11px"}),
        html.Div(confidence, style={"color": "#8B949E", "fontSize": "10px"}),
    ], style={
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "6px",
        "padding": "10px 14px",
        "border": "1px solid var(--border, #272D3F)",
        "flex": "1",
        "minWidth": "180px",
    })


def _weight_matrix_table() -> html.Table:
    """Weight profile comparison table."""
    profiles = list(WEIGHT_PROFILES.keys())
    dims = DIMENSION_IDS

    header = [html.Th("Dimension", style=_th())] + [
        html.Th(WEIGHT_PROFILE_LABELS.get(p, p), style=_th()) for p in profiles
    ]

    rows = [html.Tr(header)]
    for dim in dims:
        cells = [html.Td(dim.replace("_", " ").title(), style=_td())]
        for p in profiles:
            w = WEIGHT_PROFILES[p].get(dim, 0)
            # Highlight highest weight per profile
            max_w = max(WEIGHT_PROFILES[p].values())
            color = "#4B7BF5" if w == max_w else "#E6EDF3"
            cells.append(html.Td(f"{w:.0%}", style={**_td(), "color": color, "fontWeight": "600" if w == max_w else "400"}))
        rows.append(html.Tr(cells))

    return html.Table(rows, style={"width": "100%", "borderCollapse": "collapse"})


def _check_table(checks: list) -> html.Div:
    """Render all hygiene checks as a DataTable."""
    return dash_table.DataTable(
        id="scoring-check-datatable",
        data=checks,
        columns=[
            {"name": "ID", "id": "check_id"},
            {"name": "Check Name", "id": "check_name"},
            {"name": "Platform", "id": "platform"},
            {"name": "Dimension", "id": "dimension"},
            {"name": "Weight", "id": "weight"},
            {"name": "Hard Gate", "id": "hard_gate"},
            {"name": "Score", "id": "score"},
        ],
        sort_action="native",
        filter_action="native",
        page_size=20,
        style_header={
            "backgroundColor": "#161B22",
            "color": "#8B949E",
            "fontWeight": "600",
            "fontSize": "11px",
            "border": "1px solid #21262D",
        },
        style_cell={
            "backgroundColor": "#0D1117",
            "color": "#E6EDF3",
            "fontSize": "11px",
            "padding": "6px 10px",
            "border": "1px solid #21262D",
            "textAlign": "left",
        },
        style_data_conditional=[
            {"if": {"filter_query": "{hard_gate} = True"}, "backgroundColor": "#EF444411"},
            {"if": {"filter_query": "{score} < 50"}, "color": "#EF4444"},
            {"if": {"filter_query": "{score} >= 80"}, "color": "#22C55E"},
        ],
    )


def _dora_benchmark_table() -> html.Table:
    labels = {
        "deployment_frequency": ("Deployment Frequency", "deploys/day"),
        "lead_time": ("Lead Time", "hours"),
        "change_failure_rate": ("Change Failure Rate", "%"),
        "recovery_time": ("Recovery Time", "hours"),
    }

    header = html.Tr([
        html.Th("Metric", style=_th()),
        html.Th("Unit", style=_th()),
        html.Th("Elite", style={**_th(), "color": DORA_TIER_COLORS["Elite"]}),
        html.Th("High", style={**_th(), "color": DORA_TIER_COLORS["High"]}),
        html.Th("Medium", style={**_th(), "color": DORA_TIER_COLORS["Medium"]}),
        html.Th("Low", style={**_th(), "color": DORA_TIER_COLORS["Low"]}),
    ])

    rows = [header]
    for mk, benchmarks in DORA_BENCHMARKS.items():
        label, unit = labels.get(mk, (mk, ""))
        tier_vals = {t: str(v) for v, t in benchmarks}
        rows.append(html.Tr([
            html.Td(label, style=_td()),
            html.Td(unit, style={**_td(), "color": "#8B949E"}),
            html.Td(f"≤ {tier_vals.get('Elite', '')}" if mk != "deployment_frequency" else f"≥ {tier_vals.get('Elite', '')}",
                     style={**_td(), "color": DORA_TIER_COLORS["Elite"]}),
            html.Td(f"≤ {tier_vals.get('High', '')}" if mk != "deployment_frequency" else f"≥ {tier_vals.get('High', '')}",
                     style={**_td(), "color": DORA_TIER_COLORS["High"]}),
            html.Td(f"≤ {tier_vals.get('Medium', '')}" if mk != "deployment_frequency" else f"≥ {tier_vals.get('Medium', '')}",
                     style={**_td(), "color": DORA_TIER_COLORS["Medium"]}),
            html.Td("Above", style={**_td(), "color": DORA_TIER_COLORS["Low"]}),
        ]))

    return html.Table(rows, style={"width": "100%", "borderCollapse": "collapse"})


def _archetype_card(arch_id: str, arch: dict) -> html.Div:
    return html.Div([
        html.Div([
            html.I(className=arch["icon"], style={"color": arch["color"], "fontSize": "16px", "marginRight": "8px"}),
            html.Span(arch["name"], style={"color": "#E6EDF3", "fontSize": "13px", "fontWeight": "600"}),
        ], style={"display": "flex", "alignItems": "center", "marginBottom": "6px"}),
        html.P(arch["description"], style={"color": "#8B949E", "fontSize": "11px", "margin": "0"}),
        html.Div([
            html.Span(f"{k}: ", style={"color": "#484F58", "fontSize": "10px"})
            for k in ["throughput", "stability", "dx", "friction"]
        ] + [
            html.Span(f"{arch['pattern'].get(k, '?')} ", style={
                "color": "#E6EDF3", "fontSize": "10px", "fontWeight": "600",
            }) for k in ["throughput", "stability", "dx", "friction"]
        ], style={"marginTop": "6px", "display": "flex", "flexWrap": "wrap", "gap": "2px"}),
        html.Div(f"~{arch.get('pct_of_teams', '?')} of teams", style={
            "color": "#484F58", "fontSize": "9px", "marginTop": "4px",
        }),
    ], style={
        "backgroundColor": "var(--surface, #161B22)",
        "borderRadius": "6px",
        "padding": "14px",
        "border": f"1px solid {arch['color']}33",
    })


def _th():
    return {
        "color": "#8B949E", "fontSize": "11px", "fontWeight": "600",
        "padding": "8px 10px", "textAlign": "left",
        "borderBottom": "1px solid #21262D",
    }


def _td():
    return {
        "color": "#E6EDF3", "fontSize": "12px",
        "padding": "8px 10px",
        "borderBottom": "1px solid #21262D11",
    }
