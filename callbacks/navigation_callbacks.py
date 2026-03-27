"""Navigation Callbacks - Sidebar navigation, page switching, and active state."""

from dash import html, Input, Output, State, ctx, no_update


# Page name to layout module mapping
PAGE_MAP = {
    "executive": "executive_summary",
    "team": "team_drilldown",
    "trend": "trend_analysis",
    "deployment": "deployment_explorer",
    "correlation": "correlation_analysis",
    "admin": "admin",
}

# Nav-item id to page name mapping
NAV_ID_TO_PAGE = {
    "nav-executive": "executive",
    "nav-team": "team",
    "nav-trend": "trend",
    "nav-deployment": "deployment",
    "nav-correlation": "correlation",
    "nav-admin": "admin",
}

# Page name to display title mapping
PAGE_TITLES = {
    "executive": "Executive Summary",
    "team": "Team Drilldown",
    "trend": "Trend Analysis",
    "deployment": "Deployment Explorer",
    "correlation": "Correlation Analysis",
    "admin": "Administration",
}

# Ordered list of nav item ids (for consistent output ordering)
NAV_IDS = [
    "nav-executive",
    "nav-team",
    "nav-trend",
    "nav-deployment",
    "nav-correlation",
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
            elif current_page == "team":
                from ui.pages.team_drilldown import create_layout
            elif current_page == "trend":
                from ui.pages.trend_analysis import create_layout
            elif current_page == "deployment":
                from ui.pages.deployment_explorer import create_layout
            elif current_page == "correlation":
                from ui.pages.correlation_analysis import create_layout
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
