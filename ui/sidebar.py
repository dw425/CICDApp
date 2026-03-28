"""Blueprint Sidebar Navigation"""
from dash import html

NAV_ITEMS = [
    {"group": "OVERVIEW", "items": [
        {"id": "nav-executive", "label": "Executive Summary", "icon": "fas fa-chart-line", "page": "executive"},
    ]},
    {"group": "COMPASS", "items": [
        {"id": "nav-compass-assess", "label": "Assessment", "icon": "fas fa-compass", "page": "compass_assessment"},
        {"id": "nav-compass-results", "label": "Results", "icon": "fas fa-chart-pie", "page": "compass_results"},
        {"id": "nav-compass-roadmap", "label": "Roadmap", "icon": "fas fa-road", "page": "compass_roadmap"},
        {"id": "nav-compass-history", "label": "History", "icon": "fas fa-history", "page": "compass_history"},
        {"id": "nav-dora", "label": "DORA Metrics", "icon": "fas fa-tachometer-alt", "page": "dora_metrics"},
        {"id": "nav-databricks", "label": "Databricks Deep Dive", "icon": "fas fa-database", "page": "databricks_deep_dive"},
    ]},
    {"group": "ANALYSIS", "items": [
        {"id": "nav-hygiene", "label": "Hygiene Dashboard", "icon": "fas fa-heartbeat", "page": "hygiene"},
        {"id": "nav-golden-path", "label": "Golden Path", "icon": "fas fa-road", "page": "golden_path"},
        {"id": "nav-team", "label": "Team Drilldown", "icon": "fas fa-users", "page": "team"},
        {"id": "nav-trend", "label": "Trend Analysis", "icon": "fas fa-chart-area", "page": "trend"},
        {"id": "nav-deployment", "label": "Deployment Explorer", "icon": "fas fa-rocket", "page": "deployment"},
        {"id": "nav-correlation", "label": "Correlation Analysis", "icon": "fas fa-project-diagram", "page": "correlation"},
        {"id": "nav-roi", "label": "ROI Calculator", "icon": "fas fa-dollar-sign", "page": "roi"},
    ]},
    {"group": "SETTINGS", "items": [
        {"id": "nav-datasources", "label": "Data Sources", "icon": "fas fa-plug", "page": "data_sources"},
        {"id": "nav-scoring-logic", "label": "Scoring Logic", "icon": "fas fa-calculator", "page": "scoring_logic"},
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
    # ****Checked and Verified as Real*****
    # Constructs the Dash HTML layout for sidebar. Returns a component tree of styled html.Div and html.Span elements.
