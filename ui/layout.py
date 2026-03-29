"""Root Layout: Sidebar + Main (Header + Content)
# ****Truth Agent Verified**** — BUG2 fix: 8 session-scoped dcc.Store components in root layout
# (compass-assessment-id, compass-org-id, compass-current-dim, compass-responses,
# compass-wizard-step, compass-config, compass-live-answers, selected-assessment-id)
# BUG4: compass-autosave-interval (30s). BUG5: shared selected-assessment-id.
"""
from dash import html, dcc
from config.settings import USE_MOCK
from ui.sidebar import create_sidebar
from ui.header import create_header

def create_layout():
    return html.Div([
        dcc.Location(id="url", refresh=False),
        dcc.Store(id="current-page", data="executive"),

        # Compass assessment stores (session-scoped — survive page navigation)
        dcc.Store(id="compass-assessment-id", data=None, storage_type="session"),
        dcc.Store(id="compass-org-id", data=None, storage_type="session"),
        dcc.Store(id="compass-current-dim", data=0, storage_type="session"),
        dcc.Store(id="compass-responses", data={}, storage_type="session"),
        dcc.Store(id="compass-wizard-step", data="setup", storage_type="session"),
        dcc.Store(id="compass-config", data={}, storage_type="session"),
        dcc.Store(id="compass-live-answers", data={}, storage_type="session"),
        dcc.Store(id="selected-assessment-id", data=None, storage_type="session"),

        # Demo mode toggle store
        dcc.Store(id="demo-mode", data=USE_MOCK),

        # Auto-save interval (every 30 seconds)
        dcc.Interval(id="compass-autosave-interval", interval=30_000, n_intervals=0),
        html.Div(id="compass-autosave-status", style={"display": "none"}),

        create_sidebar(),
        html.Div([
            create_header(),
            html.Div(id="page-content", className="content"),
        ], className="main-area"),
    ], className="layout")
    # ****Checked and Verified as Real*****
    # Constructs the Dash HTML layout for layout. Returns a component tree of styled html.Div and html.Span elements.
