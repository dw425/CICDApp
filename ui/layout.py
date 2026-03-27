"""Root Layout: Sidebar + Main (Header + Content)"""
from dash import html, dcc
from ui.sidebar import create_sidebar
from ui.header import create_header

def create_layout():
    return html.Div([
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="current-page", data="executive"),
        create_sidebar(),
        html.Div([
            create_header(),
            html.Div(id="page-content", className="content"),
        ], className="main-area"),
    ], className="layout")
