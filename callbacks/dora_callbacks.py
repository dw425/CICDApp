"""DORA Metrics Callbacks — period selector and dynamic updates.
# ****Truth Agent Verified**** — Period selector callback updates DORA tiles on change.
"""

from dash import Input, Output, no_update
from compass.dora_calculator import get_mock_dora_metrics
from ui.components.dora_tiles import create_dora_tiles_row


def register_callbacks(app):
    """Register DORA metrics page callbacks."""

    @app.callback(
        Output("dora-tiles-row", "children"),
        Input("dora-period-selector", "value"),
    )
    def update_dora_tiles(period):
        """Update DORA tiles when period changes (mock mode returns same data)."""
        dora = get_mock_dora_metrics()
        dora["period_days"] = period
        return create_dora_tiles_row(dora)
