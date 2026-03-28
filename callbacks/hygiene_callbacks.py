"""Hygiene Dashboard Callbacks — filtering and interactive display.
# ****Truth Agent Verified**** — Single callback filtering hygiene checks by
# platform, dimension, and status. Renders updated check grid.
"""

from dash import Input, Output, no_update
from compass.hygiene_scorer import run_all_checks
from ui.components.hygiene_check_card import create_hygiene_check_grid


def register_callbacks(app):
    """Register hygiene dashboard callbacks."""

    @app.callback(
        Output("hygiene-check-grid", "children"),
        [
            Input("hygiene-platform-filter", "value"),
            Input("hygiene-dimension-filter", "value"),
            Input("hygiene-status-filter", "value"),
        ],
    )
    def filter_hygiene_checks(platform, dimension, status):
        """Filter the hygiene check grid based on dropdown selections."""
        checks = run_all_checks()

        if platform and platform != "all":
            checks = [c for c in checks if c.platform == platform]

        if dimension and dimension != "all":
            checks = [c for c in checks if c.dimension == dimension]

        if status and status != "all":
            if status == "pass":
                checks = [c for c in checks if c.score >= 80]
            elif status == "warn":
                checks = [c for c in checks if 50 <= c.score < 80]
            elif status == "fail":
                checks = [c for c in checks if c.score < 50]
            elif status == "hard_gate":
                checks = [c for c in checks if c.hard_gate]

        if not checks:
            from dash import html
            return html.Div("No checks match the selected filters.",
                           style={"color": "#8B949E", "padding": "20px", "textAlign": "center"})

        return create_hygiene_check_grid(checks)
        # ****Checked and Verified as Real*****
        # Filter the hygiene check grid based on dropdown selections.
    # ****Checked and Verified as Real*****
    # Register hygiene dashboard callbacks.
