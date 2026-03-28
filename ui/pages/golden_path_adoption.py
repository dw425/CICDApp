"""Golden Path Adoption Dashboard — Tracks deployment standard compliance.

Visualizations: adoption pie chart, team heatmap, non-standard drill-down,
trend line, artifact type breakdown, team leaderboard, coaching queue.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

from ui.theme import SURFACE, ELEVATED, TEXT, TEXT2, TEXT3, BORDER, ACCENT, GREEN, YELLOW, RED


def create_layout():
    """Create the Golden Path Adoption dashboard layout."""
    return html.Div([
        # Header
        html.Div([
            html.H2("Golden Path Adoption", style={"color": TEXT, "marginBottom": "4px"}),
            html.P(
                "Track which deployments follow the approved CI/CD pipeline vs ad-hoc methods.",
                style={"color": TEXT2, "fontSize": "14px", "margin": 0},
            ),
        ], style={"marginBottom": "24px"}),

        # Filters row
        html.Div([
            html.Div([
                html.Label("Time Range", style={"color": TEXT2, "fontSize": "12px"}),
                dcc.Dropdown(
                    id="gp-time-range",
                    options=[
                        {"label": "Last 7 Days", "value": "7d"},
                        {"label": "Last 30 Days", "value": "30d"},
                        {"label": "Last 90 Days", "value": "90d"},
                        {"label": "Last 6 Months", "value": "180d"},
                    ],
                    value="30d",
                    clearable=False,
                    style={"color": TEXT, "backgroundColor": SURFACE, "border": f"1px solid {BORDER}"},
                ),
            ], style={"width": "200px"}),
            html.Div([
                html.Label("Team Filter", style={"color": TEXT2, "fontSize": "12px"}),
                dcc.Dropdown(
                    id="gp-team-filter",
                    options=[{"label": "All Teams", "value": "all"}],
                    value="all",
                    clearable=False,
                    style={"color": TEXT, "backgroundColor": SURFACE, "border": f"1px solid {BORDER}"},
                ),
            ], style={"width": "200px", "marginLeft": "16px"}),
        ], style={"display": "flex", "marginBottom": "24px"}),

        # KPI Row
        html.Div(id="gp-kpi-row", style={"display": "flex", "gap": "16px", "marginBottom": "24px"}),

        # Charts Row 1: Pie + Trend
        dbc.Row([
            dbc.Col([
                _chart_card("Adoption Rate", "gp-adoption-pie"),
            ], md=5),
            dbc.Col([
                _chart_card("Adoption Trend", "gp-trend-chart"),
            ], md=7),
        ], style={"marginBottom": "16px"}),

        # Charts Row 2: Artifact Breakdown + Team Heatmap
        dbc.Row([
            dbc.Col([
                _chart_card("By Artifact Type", "gp-artifact-chart"),
            ], md=5),
            dbc.Col([
                _chart_card("Team Adoption Heatmap", "gp-team-heatmap"),
            ], md=7),
        ], style={"marginBottom": "16px"}),

        # Team Leaderboard
        html.Div([
            html.H5("Team Leaderboard", style={"color": TEXT, "marginBottom": "12px"}),
            html.Div(id="gp-leaderboard"),
        ], style={
            "backgroundColor": ELEVATED,
            "border": f"1px solid {BORDER}",
            "borderRadius": "8px",
            "padding": "20px",
            "marginBottom": "16px",
        }),

        # Non-standard Deployments Table
        html.Div([
            html.H5("Non-Standard Deployments", style={"color": TEXT, "marginBottom": "12px"}),
            html.P("Deployments that bypassed the golden path pipeline", style={"color": TEXT2, "fontSize": "13px"}),
            html.Div(id="gp-violations-table"),
        ], style={
            "backgroundColor": ELEVATED,
            "border": f"1px solid {BORDER}",
            "borderRadius": "8px",
            "padding": "20px",
            "marginBottom": "16px",
        }),

        # Coaching Queue
        html.Div([
            html.H5("Coaching Queue", style={"color": TEXT, "marginBottom": "12px"}),
            html.P("Teams below adoption threshold needing support", style={"color": TEXT2, "fontSize": "13px"}),
            html.Div(id="gp-coaching-queue"),
        ], style={
            "backgroundColor": ELEVATED,
            "border": f"1px solid {BORDER}",
            "borderRadius": "8px",
            "padding": "20px",
        }),
    ])


def _chart_card(title, chart_id):
    """Wrap a chart in a styled card."""
    return html.Div([
        html.H6(title, style={"color": TEXT, "marginBottom": "12px", "fontSize": "14px"}),
        dcc.Graph(id=chart_id, config={"displayModeBar": False}),
    ], style={
        "backgroundColor": ELEVATED,
        "border": f"1px solid {BORDER}",
        "borderRadius": "8px",
        "padding": "16px",
    })
