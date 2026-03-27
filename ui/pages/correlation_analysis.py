"""Correlation Analysis Page - Relationships between metrics."""
from dash import html, dcc


def create_layout():
    """Return the Correlation Analysis page layout."""
    return html.Div([
        html.H2("Correlation Analysis", className="section-title"),

        # ── Scatter Plots ────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div("Golden Path vs Reliability", className="card-header"),
                html.Div([
                    dcc.Graph(id="corr-gp-reliability", config={"displayModeBar": False}),
                ], className="card-body"),
            ], className="card"),

            html.Div([
                html.Div("Golden Path vs Cost Efficiency", className="card-header"),
                html.Div([
                    dcc.Graph(id="corr-gp-cost", config={"displayModeBar": False}),
                ], className="card-body"),
            ], className="card"),
        ], className="grid-2"),

        # ── Correlation Matrix ───────────────────────────────────
        html.Div([
            html.Div("Correlation Matrix", className="card-header"),
            html.Div([
                dcc.Graph(id="corr-matrix", config={"displayModeBar": False}),
            ], className="card-body"),
        ], className="card"),

        # ── Insights ─────────────────────────────────────────────
        html.Div([
            html.Div("Insights", className="card-header"),
            html.Div(id="corr-insights", className="card-body"),
        ], className="card"),
    ])
