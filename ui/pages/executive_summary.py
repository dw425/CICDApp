"""Executive Summary Page - Main dashboard overview."""
from dash import html, dcc
from ui.components.kpi_card import create_kpi_card


def create_layout():
    """Return the Executive Summary page layout."""
    return html.Div([

        # ── KPI Row ──────────────────────────────────────────────
        html.Div([
            html.Div(id="kpi-composite"),
            html.Div(id="kpi-golden-path"),
            html.Div(id="kpi-pipeline"),
            html.Div(id="kpi-teams"),
        ], className="kpi-grid"),

        # ── Row 1: Pie + Heatmap ─────────────────────────────────
        html.Div([
            html.Div([
                html.Div("Golden Path Distribution", className="card-header"),
                html.Div([
                    dcc.Graph(id="exec-golden-pie", config={"displayModeBar": False}),
                ], className="card-body"),
            ], className="card"),

            html.Div([
                html.Div("Team Maturity Heatmap", className="card-header"),
                html.Div([
                    dcc.Graph(id="exec-heatmap", config={"displayModeBar": False}),
                ], className="card-body"),
            ], className="card"),
        ], className="grid-2"),

        # ── Row 2: Trend + Alerts ────────────────────────────────
        html.Div([
            html.Div([
                html.Div("Composite Score Trend", className="card-header"),
                html.Div([
                    dcc.Graph(id="exec-trend-line", config={"displayModeBar": False}),
                ], className="card-body"),
            ], className="card"),

            html.Div([
                html.Div("Recent Alerts", className="card-header"),
                html.Div(id="exec-alerts-table", className="card-body"),
            ], className="card"),
        ], className="grid-2"),
    ])
