"""ROI Calculator Dashboard — Quantifies the business value of CI/CD maturity improvements."""

from dash import html, dcc
import dash_bootstrap_components as dbc

from ui.theme import SURFACE, ELEVATED, TEXT, TEXT2, TEXT3, BORDER, ACCENT, GREEN, YELLOW, RED


def create_layout():
    """Create the ROI Calculator dashboard layout."""
    return html.Div([
        # Header
        html.Div([
            html.H2("ROI Calculator", style={"color": TEXT, "marginBottom": "4px"}),
            html.P(
                "Quantify the business value of CI/CD maturity improvements using industry benchmarks.",
                style={"color": TEXT2, "fontSize": "14px", "margin": 0},
            ),
        ], style={"marginBottom": "24px"}),

        # Input Parameters
        html.Div([
            html.H5("Organization Parameters", style={"color": TEXT, "marginBottom": "16px"}),
            dbc.Row([
                dbc.Col([
                    html.Label("Number of Developers", style={"color": TEXT2, "fontSize": "12px"}),
                    dcc.Input(id="roi-num-devs", type="number", value=50, min=1, max=10000,
                              style={"width": "100%", "backgroundColor": SURFACE, "color": TEXT,
                                     "border": f"1px solid {BORDER}", "padding": "8px", "borderRadius": "4px"}),
                ], md=3),
                dbc.Col([
                    html.Label("Avg Developer Salary ($)", style={"color": TEXT2, "fontSize": "12px"}),
                    dcc.Input(id="roi-avg-salary", type="number", value=150000, min=30000, max=500000,
                              style={"width": "100%", "backgroundColor": SURFACE, "color": TEXT,
                                     "border": f"1px solid {BORDER}", "padding": "8px", "borderRadius": "4px"}),
                ], md=3),
                dbc.Col([
                    html.Label("Deploys per Week", style={"color": TEXT2, "fontSize": "12px"}),
                    dcc.Input(id="roi-deploys-week", type="number", value=20, min=1, max=1000,
                              style={"width": "100%", "backgroundColor": SURFACE, "color": TEXT,
                                     "border": f"1px solid {BORDER}", "padding": "8px", "borderRadius": "4px"}),
                ], md=3),
                dbc.Col([
                    html.Label("Incidents per Month", style={"color": TEXT2, "fontSize": "12px"}),
                    dcc.Input(id="roi-incidents-month", type="number", value=5, min=0, max=500,
                              style={"width": "100%", "backgroundColor": SURFACE, "color": TEXT,
                                     "border": f"1px solid {BORDER}", "padding": "8px", "borderRadius": "4px"}),
                ], md=3),
            ], style={"marginBottom": "16px"}),
            dbc.Row([
                dbc.Col([
                    html.Label("Avg Build Time (min)", style={"color": TEXT2, "fontSize": "12px"}),
                    dcc.Input(id="roi-build-time", type="number", value=15, min=1, max=120,
                              style={"width": "100%", "backgroundColor": SURFACE, "color": TEXT,
                                     "border": f"1px solid {BORDER}", "padding": "8px", "borderRadius": "4px"}),
                ], md=3),
                dbc.Col([
                    html.Label("MTTR (hours)", style={"color": TEXT2, "fontSize": "12px"}),
                    dcc.Input(id="roi-mttr", type="number", value=4, min=0.1, max=168, step=0.1,
                              style={"width": "100%", "backgroundColor": SURFACE, "color": TEXT,
                                     "border": f"1px solid {BORDER}", "padding": "8px", "borderRadius": "4px"}),
                ], md=3),
                dbc.Col([
                    html.Label("Current Maturity Tier", style={"color": TEXT2, "fontSize": "12px"}),
                    dcc.Dropdown(
                        id="roi-current-tier",
                        options=[
                            {"label": "Ad Hoc", "value": "Ad Hoc"},
                            {"label": "Managed", "value": "Managed"},
                            {"label": "Defined", "value": "Defined"},
                            {"label": "Measured", "value": "Measured"},
                            {"label": "Optimized", "value": "Optimized"},
                        ],
                        value="Managed",
                        clearable=False,
                        style={"color": TEXT, "backgroundColor": SURFACE, "border": f"1px solid {BORDER}"},
                    ),
                ], md=3),
                dbc.Col([
                    html.Label("Target Tier", style={"color": TEXT2, "fontSize": "12px"}),
                    dcc.Dropdown(
                        id="roi-target-tier",
                        options=[
                            {"label": "Managed", "value": "Managed"},
                            {"label": "Defined", "value": "Defined"},
                            {"label": "Measured", "value": "Measured"},
                            {"label": "Optimized", "value": "Optimized"},
                        ],
                        value="Defined",
                        clearable=False,
                        style={"color": TEXT, "backgroundColor": SURFACE, "border": f"1px solid {BORDER}"},
                    ),
                ], md=3),
            ]),
            html.Div([
                html.Button("Calculate ROI", id="roi-calculate-btn",
                            style={"backgroundColor": ACCENT, "color": "#fff", "border": "none",
                                   "padding": "10px 24px", "borderRadius": "6px", "cursor": "pointer",
                                   "fontWeight": "600", "marginTop": "16px"}),
            ]),
        ], style={
            "backgroundColor": ELEVATED,
            "border": f"1px solid {BORDER}",
            "borderRadius": "8px",
            "padding": "20px",
            "marginBottom": "24px",
        }),

        # KPI Summary Row
        html.Div(id="roi-kpi-row", style={"display": "flex", "gap": "16px", "marginBottom": "24px"}),

        # Charts
        dbc.Row([
            dbc.Col([
                _chart_card("Savings Breakdown", "roi-breakdown-chart"),
            ], md=6),
            dbc.Col([
                _chart_card("Cumulative ROI (12 Months)", "roi-cumulative-chart"),
            ], md=6),
        ], style={"marginBottom": "16px"}),

        # Detail table
        html.Div([
            html.H5("ROI Detail", style={"color": TEXT, "marginBottom": "12px"}),
            html.Div(id="roi-detail-table"),
        ], style={
            "backgroundColor": ELEVATED,
            "border": f"1px solid {BORDER}",
            "borderRadius": "8px",
            "padding": "20px",
            "marginBottom": "16px",
        }),

        # Benchmarks
        html.Div([
            html.H5("Industry Benchmarks", style={"color": TEXT, "marginBottom": "12px"}),
            html.Div(id="roi-benchmarks"),
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
