"""Admin Callbacks - Assessment config, mock toggle, connection info, team registry."""

from dash import html, Input, Output, State, no_update

from ui.theme import (
    SURFACE, ELEVATED, TEXT, TEXT2, TEXT3, BORDER, ACCENT, GREEN, RED,
)
from ui.components.data_table import create_data_table
from compass.admin_config import save_admin_config
from compass.scoring_engine import WEIGHT_PROFILE_LABELS


def register_callbacks(app):
    """Register Administration callbacks."""

    # ── Callback 0: Save assessment configuration ────────────────
    @app.callback(
        Output("admin-toast", "is_open"),
        Output("admin-toast", "header"),
        Output("admin-toast", "children"),
        Output("admin-active-profile-label", "children"),
        Input("admin-save-config-btn", "n_clicks"),
        State("admin-org-name", "value"),
        State("admin-org-size", "value"),
        State("admin-industry", "value"),
        State("admin-uses-databricks", "value"),
        State("admin-scoring-profile", "value"),
        prevent_initial_call=True,
    )
    def save_assessment_config(n_clicks, org_name, org_size, industry, uses_db, profile):
        """Save assessment configuration to persistent store."""
        if not n_clicks:
            return no_update, no_update, no_update, no_update

        save_admin_config({
            "organization_name": org_name or "",
            "org_size": org_size or "mid_market",
            "industry": industry or "tech",
            "uses_databricks": bool(uses_db),
            "scoring_profile": profile or "balanced",
        })

        label = WEIGHT_PROFILE_LABELS.get(profile or "balanced", "Balanced")
        return True, "Configuration Saved", "Assessment settings updated successfully.", label

    # ── Callback 1: Mock toggle → connection info ──────────────────
    @app.callback(
        Output("connection-info", "children"),
        [
            Input("mock-toggle", "value"),
            Input("refresh-connection-btn", "n_clicks"),
        ],
    )
    def update_connection_info(mock_value, n_clicks):
        """Show connection status based on mock toggle state."""
        is_mock = "mock" in (mock_value or [])

        if is_mock:
            status_icon = html.I(
                className="fas fa-database",
                style={"color": ACCENT, "marginRight": "8px"},
            )
            status_text = "Mock Mode Active"
            status_color = ACCENT
            details = [
                _status_row("Data Source", "Local CSV files", ACCENT),
                _status_row("Status", "Connected", GREEN),
                _status_row("Tables", "12 mock tables loaded", TEXT2),
                _status_row("Latency", "< 1ms", GREEN),
            ]
        else:
            try:
                from config.settings import (
                    DATABRICKS_SERVER_HOSTNAME,
                    DATABRICKS_HTTP_PATH,
                    USE_MOCK,
                )
                if DATABRICKS_SERVER_HOSTNAME:
                    hostname_display = DATABRICKS_SERVER_HOSTNAME[:30] + "..." if len(str(DATABRICKS_SERVER_HOSTNAME)) > 30 else DATABRICKS_SERVER_HOSTNAME
                else:
                    hostname_display = "Not configured"

                status_icon = html.I(
                    className="fas fa-cloud",
                    style={"color": GREEN, "marginRight": "8px"},
                )
                status_text = "Databricks SQL"
                status_color = GREEN
                details = [
                    _status_row("Hostname", str(hostname_display), TEXT2),
                    _status_row("HTTP Path", "Configured" if DATABRICKS_HTTP_PATH else "Not set", GREEN if DATABRICKS_HTTP_PATH else RED),
                    _status_row("Auth", "Token" if not USE_MOCK else "Mock", TEXT2),
                    _status_row("Status", "Ready" if DATABRICKS_SERVER_HOSTNAME else "Not configured", GREEN if DATABRICKS_SERVER_HOSTNAME else RED),
                ]
            except Exception:
                status_icon = html.I(
                    className="fas fa-exclamation-triangle",
                    style={"color": RED, "marginRight": "8px"},
                )
                status_text = "Configuration Error"
                status_color = RED
                details = [
                    _status_row("Status", "Error loading config", RED),
                ]

        return html.Div([
            html.Div([
                status_icon,
                html.Span(status_text, style={
                    "color": status_color,
                    "fontWeight": "600",
                    "fontSize": "14px",
                }),
            ], style={
                "display": "flex",
                "alignItems": "center",
                "marginBottom": "16px",
                "padding": "10px 14px",
                "backgroundColor": ELEVATED,
                "borderRadius": "6px",
                "border": f"1px solid {BORDER}",
            }),
            html.Div(details),
        ])

    # ── Callback 2: Team registry table ────────────────────────────
    @app.callback(
        Output("admin-team-table", "children"),
        Input("current-page", "data"),
    )
    def update_team_registry(current_page):
        """Load and display the team registry table."""
        if current_page != "admin":
            return no_update

        try:
            from data_layer.queries.custom_tables import get_teams
            teams = get_teams()

            if teams.empty:
                return html.Div(
                    "No teams registered",
                    style={"color": TEXT2, "padding": "20px"},
                )

            display_df = teams.copy()
            if "created_date" in display_df.columns:
                display_df["created_date"] = display_df["created_date"].astype(str).str[:10]

            columns = [
                {"name": "Team ID", "id": "team_id"},
                {"name": "Team Name", "id": "team_name"},
                {"name": "Members", "id": "member_count"},
                {"name": "Created", "id": "created_date"},
            ]

            return create_data_table(
                display_df,
                table_id="admin-teams-dt",
                page_size=10,
                columns=columns,
            )

        except Exception as e:
            return html.Div(
                f"Error loading teams: {str(e)}",
                style={"color": RED, "padding": "20px"},
            )


def _status_row(label, value, value_color):
    """Build a key-value status row."""
    return html.Div([
        html.Span(label, style={
            "color": TEXT3,
            "fontSize": "12px",
            "fontWeight": "500",
            "textTransform": "uppercase",
            "letterSpacing": "0.5px",
            "minWidth": "100px",
        }),
        html.Span(value, style={
            "color": value_color,
            "fontSize": "13px",
            "fontWeight": "500",
        }),
    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "padding": "6px 0",
        "borderBottom": f"1px solid {BORDER}",
    })
