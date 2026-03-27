"""Blueprint Sidebar Navigation"""
from dash import html

NAV_ITEMS = [
    {"group": "OVERVIEW", "items": [
        {"id": "nav-executive", "label": "Executive Summary", "icon": "fas fa-chart-line", "page": "executive"},
    ]},
    {"group": "ANALYSIS", "items": [
        {"id": "nav-team", "label": "Team Drilldown", "icon": "fas fa-users", "page": "team"},
        {"id": "nav-trend", "label": "Trend Analysis", "icon": "fas fa-chart-area", "page": "trend"},
        {"id": "nav-deployment", "label": "Deployment Explorer", "icon": "fas fa-rocket", "page": "deployment"},
        {"id": "nav-correlation", "label": "Correlation Analysis", "icon": "fas fa-project-diagram", "page": "correlation"},
    ]},
    {"group": "SETTINGS", "items": [
        {"id": "nav-datasources", "label": "Data Sources", "icon": "fas fa-plug", "page": "data_sources"},
        {"id": "nav-admin", "label": "Admin", "icon": "fas fa-cog", "page": "admin"},
    ]},
]

def create_sidebar():
    nav_elements = []
    for group in NAV_ITEMS:
        nav_elements.append(html.Div(group["group"], className="nav-group-label"))
        for item in group["items"]:
            nav_elements.append(
                html.Div(
                    [html.I(className=item["icon"]), html.Span(item["label"])],
                    id=item["id"],
                    className="nav-item active" if item["page"] == "executive" else "nav-item",
                    **{"data-page": item["page"]}
                )
            )

    return html.Div([
        # Brand
        html.Div([
            html.Span("CI/CD", style={"color": "#4B7BF5", "fontWeight": "700", "fontSize": "18px"}),
            html.Span(" Maturity", style={"color": "#E6EDF3", "fontWeight": "400", "fontSize": "18px"}),
        ], className="sidebar-brand"),
        # Nav
        html.Div(nav_elements, className="sidebar-nav", id="sidebar-nav"),
        # Footer
        html.Div([
            html.Div([
                html.Strong("Blueprint"),
                html.Span("Powered by"),
            ], className="powered-by"),
            html.Div("Databricks Platform", style={"fontSize": "10px", "color": "var(--text3)", "marginTop": "2px"}),
        ], className="sidebar-footer"),
    ], className="sidebar")
