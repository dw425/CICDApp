"""Scoring Logic Page Callbacks — check registry filtering.
# ****Truth Agent Verified**** — Platform filter callback for 78-check DataTable registry.
"""

from dash import Input, Output, no_update, dash_table
from compass.hygiene_scorer import get_all_check_definitions


def register_callbacks(app):
    """Register scoring logic page callbacks."""

    @app.callback(
        Output("scoring-check-table", "children"),
        Input("scoring-check-platform-filter", "value"),
    )
    def filter_check_registry(platform):
        """Filter the check registry table by platform."""
        all_checks = get_all_check_definitions()

        if platform and platform != "all":
            all_checks = [c for c in all_checks if c["platform"] == platform]

        return dash_table.DataTable(
            id="scoring-check-datatable",
            data=all_checks,
            columns=[
                {"name": "ID", "id": "check_id"},
                {"name": "Check Name", "id": "check_name"},
                {"name": "Platform", "id": "platform"},
                {"name": "Dimension", "id": "dimension"},
                {"name": "Weight", "id": "weight"},
                {"name": "Hard Gate", "id": "hard_gate"},
                {"name": "Score", "id": "score"},
            ],
            sort_action="native",
            filter_action="native",
            page_size=20,
            style_header={
                "backgroundColor": "#161B22",
                "color": "#8B949E",
                "fontWeight": "600",
                "fontSize": "11px",
                "border": "1px solid #21262D",
            },
            style_cell={
                "backgroundColor": "#0D1117",
                "color": "#E6EDF3",
                "fontSize": "11px",
                "padding": "6px 10px",
                "border": "1px solid #21262D",
                "textAlign": "left",
            },
            style_data_conditional=[
                {"if": {"filter_query": "{hard_gate} = True"}, "backgroundColor": "#EF444411"},
                {"if": {"filter_query": "{score} < 50"}, "color": "#EF4444"},
                {"if": {"filter_query": "{score} >= 80"}, "color": "#22C55E"},
            ],
        )
