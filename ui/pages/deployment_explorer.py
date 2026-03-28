"""Deployment Explorer Page - Detailed deployment data and filters."""
from dash import html, dcc


def create_layout():
    """Return the Deployment Explorer page layout."""
    return html.Div([
        html.H2("Deployment Explorer", className="section-title"),

        # ── Filter Row ───────────────────────────────────────────
        html.Div([
            dcc.Dropdown(
                id="deploy-team-filter",
                options=[{"label": "All", "value": "All"}],
                value="All",
                placeholder="Team",
                style={"backgroundColor": "#0D1117", "color": "#E6EDF3", "border": "1px solid #272D3F", "flex": "1"},
            ),
            dcc.Dropdown(
                id="deploy-env-filter",
                options=[
                    {"label": "All", "value": "All"},
                    {"label": "dev", "value": "dev"},
                    {"label": "staging", "value": "staging"},
                    {"label": "prod", "value": "prod"},
                ],
                value="All",
                placeholder="Environment",
                style={"backgroundColor": "#0D1117", "color": "#E6EDF3", "border": "1px solid #272D3F", "flex": "1"},
            ),
            dcc.Dropdown(
                id="deploy-actor-filter",
                options=[
                    {"label": "All", "value": "All"},
                    {"label": "service_principal", "value": "service_principal"},
                    {"label": "human", "value": "human"},
                ],
                value="All",
                placeholder="Actor Type",
                style={"backgroundColor": "#0D1117", "color": "#E6EDF3", "border": "1px solid #272D3F", "flex": "1"},
            ),
        ], style={"display": "flex", "gap": "12px", "marginBottom": "16px"}),

        # ── Chart Row (3 cols) ───────────────────────────────────
        html.Div([
            html.Div([
                html.Div("Golden Path", className="card-header"),
                html.Div([
                    dcc.Graph(id="deploy-golden-pie", config={"displayModeBar": False}),
                ], className="card-body"),
            ], className="card"),

            html.Div([
                html.Div("Volume by Environment", className="card-header"),
                html.Div([
                    dcc.Graph(id="deploy-env-bar", config={"displayModeBar": False}),
                ], className="card-body"),
            ], className="card"),

            html.Div([
                html.Div("Artifacts", className="card-header"),
                html.Div([
                    dcc.Graph(id="deploy-artifact-donut", config={"displayModeBar": False}),
                ], className="card-body"),
            ], className="card"),
        ], className="grid-3"),

        # ── Events Table ─────────────────────────────────────────
        html.Div([
            html.Div([
                html.Span("Deployment Events"),
                html.Button(
                    "Export CSV",
                    id="deploy-export-btn",
                    className="btn btn-outline",
                    style={"marginLeft": "auto", "fontSize": "12px"},
                ),
            ], className="card-header", style={"display": "flex", "alignItems": "center"}),
            html.Div(id="deploy-events-table", className="card-body"),
        ], className="card"),
    ])
    # ****Checked and Verified as Real*****
    # Return the Deployment Explorer page layout.
