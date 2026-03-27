"""Team Drilldown Page - Drill into individual team scores."""
from dash import html, dcc


def create_layout():
    """Return the Team Drilldown page layout."""
    return html.Div([
        html.H2("Team Drilldown", className="section-title"),

        # ── Team selector ────────────────────────────────────────
        dcc.Dropdown(
            id="team-selector",
            options=[],
            placeholder="Select a team...",
            style={"backgroundColor": "#0D1117", "color": "#E6EDF3"},
        ),

        # ── Radar + Gauge ────────────────────────────────────────
        html.Div([
            html.Div([
                html.Div("Maturity Radar", className="card-header"),
                html.Div([
                    dcc.Graph(id="team-radar", config={"displayModeBar": False}),
                ], className="card-body"),
            ], className="card"),

            html.Div([
                html.Div("Composite Score", className="card-header"),
                html.Div(id="team-gauge-container", className="card-body"),
            ], className="card"),
        ], className="grid-2"),

        # ── Domain Details ───────────────────────────────────────
        html.Div([
            html.Div("Domain Details", className="card-header"),
            html.Div(id="team-domain-details", className="card-body"),
        ], className="card"),

        # ── Deployment History ───────────────────────────────────
        html.Div([
            html.Div("Deployment History", className="card-header"),
            html.Div(id="team-deployment-table", className="card-body"),
        ], className="card"),

        # ── Coaching Recommendations ─────────────────────────────
        html.Div([
            html.Div("Coaching Recommendations", className="card-header"),
            html.Div(id="team-recommendations", className="card-body"),
        ], className="card"),
    ])
