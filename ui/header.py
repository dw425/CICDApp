"""Blueprint Header Bar"""
from dash import html
import dash_bootstrap_components as dbc


def create_header():
    _date_style = {
        "backgroundColor": "#21262D",
        "color": "#E6EDF3",
        "border": "1px solid #272D3F",
        "borderRadius": "4px",
        "padding": "4px 8px",
        "fontSize": "12px",
        "width": "120px",
        "height": "30px",
    }

    return html.Div([
        html.Div("CI/CD Maturity Intelligence", className="header-title", id="page-title"),
        html.Div([
            html.Span("Databricks", className="cloud-badge"),
            html.Div([
                dbc.Input(
                    id="date-start",
                    type="date",
                    value="2024-01-01",
                    style=_date_style,
                ),
                html.Span("->", style={
                    "color": "#484F58",
                    "fontSize": "12px",
                    "margin": "0 6px",
                }),
                dbc.Input(
                    id="date-end",
                    type="date",
                    value="2024-03-26",
                    style=_date_style,
                ),
            ], style={"display": "flex", "alignItems": "center"}),
            html.Button([
                html.I(className="fas fa-sync-alt"), " Refresh"
            ], className="btn btn-secondary", id="refresh-btn"),
        ], className="header-meta"),
    ], className="header")
