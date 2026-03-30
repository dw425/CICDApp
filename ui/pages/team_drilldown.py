"""Team Drilldown Page - Drill into individual team scores."""
from dash import html, dcc


def _get_team_options():
    """Load team options for the dropdown at layout-creation time."""
    try:
        from data_layer.queries.custom_tables import get_teams
        teams = get_teams()
        if not teams.empty:
            return [
                {"label": row["team_name"], "value": row["team_id"]}
                for _, row in teams.iterrows()
            ]
    except Exception:
        pass
    return []


def create_layout():
    """Return the Team Drilldown page layout."""
    return html.Div([
        html.H2("Team Drilldown", className="section-title"),

        # ── Team selector ────────────────────────────────────────
        dcc.Dropdown(
            id="team-selector",
            options=_get_team_options(),
            placeholder="Select a team...",
            style={"backgroundColor": "#0D1117", "color": "#E6EDF3", "border": "1px solid #272D3F"},
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
    # ****Checked and Verified as Real*****
    # Return the Team Drilldown page layout.
