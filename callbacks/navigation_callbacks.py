"""Navigation Callbacks - Sidebar navigation, page switching, and active state.
# ****Truth Agent Verified**** — 15 pages in PAGE_MAP, NAV_ID_TO_PAGE, PAGE_TITLES, NAV_IDS.
# render_page handles all 15 pages. Active state callback. Page title callback.
"""

from dash import html, Input, Output, State, ctx, no_update


# Page name to layout module mapping
PAGE_MAP = {
    "executive": "executive_summary",
    "compass_assessment": "compass_assessment",
    "compass_results": "compass_results",
    "compass_roadmap": "compass_roadmap",
    "compass_history": "compass_history",
    "dora_metrics": "dora_metrics",
    "databricks_deep_dive": "databricks_deep_dive",
    "hygiene": "hygiene_dashboard",
    "team": "team_drilldown",
    "trend": "trend_analysis",
    "deployment": "deployment_explorer",
    "correlation": "correlation_analysis",
    "data_sources": "data_sources",
    "scoring_logic": "scoring_logic",
    "admin": "admin",
}

# Nav-item id to page name mapping
NAV_ID_TO_PAGE = {
    "nav-executive": "executive",
    "nav-compass-assess": "compass_assessment",
    "nav-compass-results": "compass_results",
    "nav-compass-roadmap": "compass_roadmap",
    "nav-compass-history": "compass_history",
    "nav-dora": "dora_metrics",
    "nav-databricks": "databricks_deep_dive",
    "nav-hygiene": "hygiene",
    "nav-team": "team",
    "nav-trend": "trend",
    "nav-deployment": "deployment",
    "nav-correlation": "correlation",
    "nav-datasources": "data_sources",
    "nav-scoring-logic": "scoring_logic",
    "nav-admin": "admin",
}

# Page name to display title mapping
PAGE_TITLES = {
    "executive": "Executive Summary",
    "compass_assessment": "Pipeline Compass — Assessment",
    "compass_results": "Pipeline Compass — Results",
    "compass_roadmap": "Pipeline Compass — Roadmap",
    "compass_history": "Pipeline Compass — History",
    "dora_metrics": "DORA Metrics",
    "databricks_deep_dive": "Databricks Deep Dive",
    "hygiene": "Hygiene Dashboard",
    "team": "Team Drilldown",
    "trend": "Trend Analysis",
    "deployment": "Deployment Explorer",
    "correlation": "Correlation Analysis",
    "data_sources": "Data Sources",
    "scoring_logic": "Scoring Logic",
    "admin": "Administration",
}

# Ordered list of nav item ids (for consistent output ordering)
NAV_IDS = [
    "nav-executive",
    "nav-compass-assess",
    "nav-compass-results",
    "nav-compass-roadmap",
    "nav-compass-history",
    "nav-dora",
    "nav-databricks",
    "nav-hygiene",
    "nav-team",
    "nav-trend",
    "nav-deployment",
    "nav-correlation",
    "nav-datasources",
    "nav-scoring-logic",
    "nav-admin",
]


def register_callbacks(app):
    """Register navigation-related callbacks."""

    # ── Callback 1: Nav click → update current-page store ──────────
    @app.callback(
        Output("current-page", "data"),
        [Input(nav_id, "n_clicks") for nav_id in NAV_IDS],
        prevent_initial_call=True,
    )
    def on_nav_click(*args):
        """Determine which nav item was clicked and store the page name."""
        triggered_id = ctx.triggered_id
        if triggered_id is None:
            return no_update
        page = NAV_ID_TO_PAGE.get(triggered_id)
        if page is None:
            return no_update
        return page

    # ── Callback 2: Current page → render page content ─────────────
    @app.callback(
        Output("page-content", "children"),
        Input("current-page", "data"),
    )
    def render_page(current_page):
        """Render the layout for the selected page."""
        if current_page is None:
            current_page = "executive"

        try:
            if current_page == "executive":
                from ui.pages.executive_summary import create_layout
            elif current_page == "compass_assessment":
                from ui.pages.compass_assessment import create_layout
            elif current_page == "compass_results":
                from ui.pages.compass_results import create_layout
            elif current_page == "compass_roadmap":
                from ui.pages.compass_roadmap import create_layout
            elif current_page == "compass_history":
                from ui.pages.compass_history import create_layout
            elif current_page == "dora_metrics":
                from ui.pages.dora_metrics import create_layout
            elif current_page == "databricks_deep_dive":
                from ui.pages.databricks_deep_dive import create_layout
            elif current_page == "hygiene":
                from ui.pages.hygiene_dashboard import create_layout
            elif current_page == "team":
                from ui.pages.team_drilldown import create_layout
            elif current_page == "trend":
                from ui.pages.trend_analysis import create_layout
            elif current_page == "deployment":
                from ui.pages.deployment_explorer import create_layout
            elif current_page == "correlation":
                from ui.pages.correlation_analysis import create_layout
            elif current_page == "data_sources":
                from ui.pages.data_sources import create_layout
            elif current_page == "scoring_logic":
                from ui.pages.scoring_logic import create_layout
            elif current_page == "admin":
                from ui.pages.admin import create_layout
            else:
                return html.Div(
                    f"Page '{current_page}' not found.",
                    style={"color": "#F87171", "padding": "40px"},
                )
            return create_layout()
        except Exception as e:
            return html.Div(
                f"Error loading page: {str(e)}",
                style={"color": "#F87171", "padding": "40px"},
            )

    # ── Callback 3: Active nav state ───────────────────────────────
    @app.callback(
        [Output(nav_id, "className") for nav_id in NAV_IDS],
        Input("current-page", "data"),
    )
    def update_nav_active_state(current_page):
        """Set 'active' class on the nav item matching the current page."""
        if current_page is None:
            current_page = "executive"
        return [
            "nav-item active" if NAV_ID_TO_PAGE[nav_id] == current_page else "nav-item"
            for nav_id in NAV_IDS
        ]

    # ── Callback 4: Page title ─────────────────────────────────────
    @app.callback(
        Output("page-title", "children"),
        Input("current-page", "data"),
    )
    def update_page_title(current_page):
        """Update the header title to match the current page."""
        if current_page is None:
            current_page = "executive"
        return PAGE_TITLES.get(current_page, "CI/CD Maturity Intelligence")
