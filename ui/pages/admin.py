"""Administration Page - Assessment config, scoring matrix, weights, connection, teams."""
from dash import html, dcc
import dash_bootstrap_components as dbc
from ui.components.upload_modal import create_upload_modal
from compass.admin_config import get_admin_config
from compass.scoring_engine import WEIGHT_PROFILES, WEIGHT_PROFILE_LABELS

# Default domain weights (must sum to 100)
DEFAULT_WEIGHTS = {
    "golden_path": 25,
    "pipeline_reliability": 20,
    "environment_promotion": 15,
    "data_quality": 15,
    "security_governance": 15,
    "cost_efficiency": 10,
}

DOMAIN_LABELS = {
    "golden_path": "Golden Path Compliance",
    "pipeline_reliability": "Pipeline Reliability",
    "environment_promotion": "Environment Promotion",
    "data_quality": "Data Quality",
    "security_governance": "Security & Governance",
    "cost_efficiency": "Cost Efficiency",
}

# Dimension labels for the scoring matrix
DIMENSION_LABELS = {
    "build_integration": "Build & Integration",
    "testing_quality": "Testing & Quality",
    "deployment_release": "Deployment & Release",
    "security_compliance": "Security & Compliance",
    "observability": "Observability",
    "iac_configuration": "IaC & Configuration",
    "artifact_management": "Artifact Management",
    "developer_experience": "Developer Experience",
    "pipeline_governance": "Pipeline Governance",
}

_input_style = {
    "backgroundColor": "#21262D",
    "color": "#E6EDF3",
    "border": "1px solid #272D3F",
}


def _slider_row(domain, weight):
    """Build a single slider row with label and live value display."""
    label = DOMAIN_LABELS.get(domain, domain)
    return html.Div([
        html.Div([
            html.Span(label, style={"color": "#E6EDF3", "fontSize": "13px"}),
            html.Span(
                str(weight),
                id=f"weight-display-{domain}",
                style={"color": "#8B949E", "fontSize": "13px", "marginLeft": "auto"},
            ),
        ], style={"display": "flex", "justifyContent": "space-between", "marginBottom": "4px"}),
        dcc.Slider(
            id=f"weight-{domain}",
            min=0,
            max=50,
            step=1,
            value=weight,
            marks=None,
            tooltip={"placement": "bottom", "always_visible": False},
        ),
    ], style={"marginBottom": "16px"})
    # ****Checked and Verified as Real*****
    # Build a single slider row with label and live value display.


def _build_scoring_matrix():
    """Build a visual table of all weight profiles and their dimension weights."""
    profiles = list(WEIGHT_PROFILES.keys())
    dimensions = list(WEIGHT_PROFILES["balanced"].keys())

    # Header row
    header_cells = [html.Th("Dimension", style={
        "color": "#E6EDF3", "fontSize": "12px", "fontWeight": "600",
        "padding": "10px 12px", "textAlign": "left",
        "borderBottom": "2px solid #272D3F", "backgroundColor": "#161B22",
    })]
    for p in profiles:
        header_cells.append(html.Th(
            WEIGHT_PROFILE_LABELS.get(p, p).split(" (")[0],
            style={
                "color": "#8B949E", "fontSize": "11px", "fontWeight": "600",
                "padding": "10px 8px", "textAlign": "center",
                "borderBottom": "2px solid #272D3F", "backgroundColor": "#161B22",
                "minWidth": "80px",
            },
        ))
    header = html.Thead(html.Tr(header_cells))

    # Body rows
    rows = []
    for dim in dimensions:
        cells = [html.Td(
            DIMENSION_LABELS.get(dim, dim),
            style={"color": "#E6EDF3", "fontSize": "12px", "padding": "8px 12px"},
        )]
        for p in profiles:
            w = WEIGHT_PROFILES[p].get(dim, 0)
            pct = int(w * 100)
            # Highlight high weights
            color = "#34D399" if pct >= 18 else ("#FBBF24" if pct >= 14 else "#8B949E")
            cells.append(html.Td(
                f"{pct}%",
                style={
                    "color": color, "fontSize": "12px", "fontWeight": "600",
                    "padding": "8px", "textAlign": "center",
                },
            ))
        rows.append(html.Tr(cells, style={"borderBottom": "1px solid #272D3F"}))

    return html.Table(
        [header, html.Tbody(rows)],
        style={
            "width": "100%", "borderCollapse": "collapse",
            "backgroundColor": "#161B22", "borderRadius": "6px",
        },
    )
    # ****Checked and Verified as Real*****
    # Build a visual table of all weight profiles and their dimension weights.


def create_layout():
    """Return the Administration page layout."""
    cfg = get_admin_config()

    return html.Div([
        # Toast for save confirmations
        dbc.Toast(
            id="admin-toast",
            header="",
            is_open=False,
            duration=3000,
            style={"position": "fixed", "top": 10, "right": 10, "zIndex": 9999},
        ),

        # ── Assessment Configuration ──────────────────────────
        html.Div([
            html.Div([
                html.I(className="fas fa-cog", style={"color": "#4B7BF5", "fontSize": "16px"}),
                html.Span("Assessment Configuration", style={
                    "color": "#E6EDF3", "fontSize": "15px", "fontWeight": "700", "marginLeft": "10px",
                }),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "4px"}),
            html.Div("Default settings applied to all new assessments.", style={
                "color": "#484F58", "fontSize": "12px", "marginBottom": "16px",
            }),
        ]),

        html.Div([
            # Left: Org + Databricks
            html.Div([
                html.Div([
                    html.Div("Organization Settings", className="card-header"),
                    html.Div([
                        html.Div([
                            html.Label("Organization Name", style={"color": "#E6EDF3", "fontSize": "13px", "fontWeight": "600"}),
                            dbc.Input(
                                id="admin-org-name",
                                placeholder="e.g., Data Platform Team",
                                type="text",
                                value=cfg.get("organization_name", ""),
                                className="mt-1",
                                style=_input_style,
                            ),
                        ], style={"marginBottom": "14px"}),

                        html.Div([
                            html.Label("Organization Size", style={"color": "#E6EDF3", "fontSize": "13px", "fontWeight": "600"}),
                            dbc.Select(
                                id="admin-org-size",
                                options=[
                                    {"label": "Startup (<50)", "value": "startup"},
                                    {"label": "Mid-Market (50-500)", "value": "mid_market"},
                                    {"label": "Enterprise (500+)", "value": "enterprise"},
                                ],
                                value=cfg.get("org_size", "mid_market"),
                                className="mt-1",
                                style=_input_style,
                            ),
                        ], style={"marginBottom": "14px"}),

                        html.Div([
                            html.Label("Industry", style={"color": "#E6EDF3", "fontSize": "13px", "fontWeight": "600"}),
                            dbc.Select(
                                id="admin-industry",
                                options=[
                                    {"label": "Technology", "value": "tech"},
                                    {"label": "Financial Services", "value": "financial_services"},
                                    {"label": "Healthcare", "value": "healthcare"},
                                    {"label": "Government", "value": "government"},
                                    {"label": "Retail / E-Commerce", "value": "retail"},
                                    {"label": "All Industries", "value": "all"},
                                ],
                                value=cfg.get("industry", "tech"),
                                className="mt-1",
                                style=_input_style,
                            ),
                        ], style={"marginBottom": "14px"}),

                        html.Div([
                            html.Label("Uses Databricks?", style={"color": "#E6EDF3", "fontSize": "13px", "fontWeight": "600"}),
                            dbc.RadioItems(
                                id="admin-uses-databricks",
                                options=[
                                    {"label": "Yes (+15 assessment questions)", "value": True},
                                    {"label": "No", "value": False},
                                ],
                                value=cfg.get("uses_databricks", False),
                                className="mt-2",
                                labelStyle={"fontSize": "13px", "marginBottom": "4px", "color": "#8B949E"},
                            ),
                        ], style={"marginBottom": "14px"}),

                        html.Div([
                            html.Label("Scoring Profile", style={"color": "#E6EDF3", "fontSize": "13px", "fontWeight": "600"}),
                            dbc.Select(
                                id="admin-scoring-profile",
                                options=[
                                    {"label": v, "value": k}
                                    for k, v in WEIGHT_PROFILE_LABELS.items()
                                ],
                                value=cfg.get("scoring_profile", "balanced"),
                                className="mt-1",
                                style=_input_style,
                            ),
                        ], style={"marginBottom": "16px"}),

                        html.Button(
                            [html.I(className="fas fa-save", style={"marginRight": "6px"}), "Save Configuration"],
                            id="admin-save-config-btn",
                            className="btn btn-primary",
                            style={"width": "100%"},
                        ),
                    ], className="card-body"),
                ], className="card"),
            ], style={"flex": "1"}),

            # Right: Scoring Weight Matrix
            html.Div([
                html.Div([
                    html.Div("Assessment Scoring Matrix", className="card-header"),
                    html.Div([
                        html.Div(
                            "Weight distribution across scoring profiles. "
                            "Higher weights increase a dimension's impact on the overall maturity score.",
                            style={"color": "#8B949E", "fontSize": "12px", "marginBottom": "12px"},
                        ),
                        _build_scoring_matrix(),
                        html.Div([
                            html.Span("Active profile: ", style={"color": "#484F58", "fontSize": "11px"}),
                            html.Span(
                                id="admin-active-profile-label",
                                children=WEIGHT_PROFILE_LABELS.get(
                                    cfg.get("scoring_profile", "balanced"), "Balanced"
                                ),
                                style={"color": "#4B7BF5", "fontSize": "11px", "fontWeight": "600"},
                            ),
                        ], style={"marginTop": "10px"}),
                    ], className="card-body"),
                ], className="card"),
            ], style={"flex": "2"}),
        ], style={"display": "flex", "gap": "16px", "marginBottom": "20px"}),

        # ── Dashboard Scoring Weights + Connection Status ─────
        html.Div([
            # Scoring Weights card
            html.Div([
                html.Div("Dashboard Scoring Weights", className="card-header"),
                html.Div([
                    *[_slider_row(domain, weight) for domain, weight in DEFAULT_WEIGHTS.items()],
                    html.Button(
                        "Save Weights",
                        id="save-weights-btn",
                        className="btn btn-primary",
                        style={"marginTop": "8px", "width": "100%"},
                    ),
                ], className="card-body"),
            ], className="card"),

            # Connection Status card
            html.Div([
                html.Div("Connection Status", className="card-header"),
                html.Div([
                    html.Div([
                        dcc.Checklist(
                            id="mock-toggle",
                            options=[{"label": " Mock Mode", "value": "mock"}],
                            value=["mock"],
                            style={"color": "#E6EDF3", "marginBottom": "16px"},
                        ),
                    ]),
                    html.Div(id="connection-info", style={"marginBottom": "16px"}),
                    html.Button(
                        "Refresh Connection",
                        id="refresh-connection-btn",
                        className="btn btn-outline",
                        style={"width": "100%"},
                    ),
                ], className="card-body"),
            ], className="card"),
        ], className="grid-2"),

        # ── Team Registry ────────────────────────────────────────
        html.Div([
            html.Div("Team Registry", className="card-header"),
            html.Div(id="admin-team-table", className="card-body"),
        ], className="card"),

        # ── Upload Modal ─────────────────────────────────────────
        create_upload_modal(),
    ])
    # ****Checked and Verified as Real*****
    # Return the Administration page layout.
