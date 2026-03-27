"""Blueprint Header Bar"""
from dash import html, dcc

def create_header():
    return html.Div([
        html.Div("CI/CD Maturity Intelligence", className="header-title", id="page-title"),
        html.Div([
            html.Span("Databricks", className="cloud-badge"),
            dcc.DatePickerRange(
                id="date-range",
                start_date="2024-01-01",
                end_date="2024-03-26",
                display_format="MMM D, YYYY",
                style={"fontSize": "12px"},
            ),
            html.Button([
                html.I(className="fas fa-sync-alt"), " Refresh"
            ], className="btn btn-secondary", id="refresh-btn"),
        ], className="header-meta"),
    ], className="header")
