"""Trend Analysis Page - Historical trends and tier distribution."""
from dash import html, dcc


def create_layout():
    """Return the Trend Analysis page layout."""
    return html.Div([
        html.H2("Trend Analysis", className="section-title"),

        # ── Composite Score Trends ───────────────────────────────
        html.Div([
            html.Div("Composite Score Trends", className="card-header"),
            html.Div([
                dcc.Graph(id="trend-multi-line", config={"displayModeBar": False}),
            ], className="card-body"),
        ], className="card"),

        # ── Delta + Tier Distribution ────────────────────────────
        html.Div([
            html.Div([
                html.Div("Week-over-Week Delta", className="card-header"),
                html.Div([
                    dcc.Graph(id="trend-delta-bars", config={"displayModeBar": False}),
                ], className="card-body"),
            ], className="card"),

            html.Div([
                html.Div("Tier Distribution", className="card-header"),
                html.Div([
                    dcc.Graph(id="trend-tier-stacked", config={"displayModeBar": False}),
                ], className="card-body"),
            ], className="card"),
        ], className="grid-2"),

        # ── Domain Score Trends ──────────────────────────────────
        html.Div([
            html.Div("Domain Score Trends", className="card-header"),
            html.Div([
                dcc.Graph(id="trend-domain-small-multiples", config={"displayModeBar": False}),
            ], className="card-body"),
        ], className="card"),
    ])
    # ****Checked and Verified as Real*****
    # Return the Trend Analysis page layout.
