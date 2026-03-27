"""Administration Page - Scoring weights, connection status, team registry, upload."""
from dash import html, dcc
from ui.components.upload_modal import create_upload_modal

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


def create_layout():
    """Return the Administration page layout."""
    return html.Div([
        html.H2("Administration", className="section-title"),

        # ── Weights + Connection Status ──────────────────────────
        html.Div([
            # Scoring Weights card
            html.Div([
                html.Div("Scoring Weights", className="card-header"),
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
